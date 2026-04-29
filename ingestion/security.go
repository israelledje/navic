package main

import (
	"fmt"
	"net"
	"sync"
	"time"
)

// RateLimiter gère le rate limiting par IP et IMEI
type RateLimiter struct {
	ipLimits     map[string]*rateLimitEntry
	imeiLimits   map[string]*rateLimitEntry
	blockedIPs   map[string]time.Time
	blockedIMEIs map[string]time.Time
	mu           sync.RWMutex
	config       SecurityConfig
}

type rateLimitEntry struct {
	count       int
	windowStart time.Time
}

// NewRateLimiter crée un nouveau rate limiter
func NewRateLimiter(config SecurityConfig) *RateLimiter {
	rl := &RateLimiter{
		ipLimits:     make(map[string]*rateLimitEntry),
		imeiLimits:   make(map[string]*rateLimitEntry),
		blockedIPs:   make(map[string]time.Time),
		blockedIMEIs: make(map[string]time.Time),
		config:       config,
	}

	// Nettoyage périodique des entrées expirées
	go rl.cleanup()
	return rl
}

// cleanup nettoie périodiquement les entrées expirées
func (rl *RateLimiter) cleanup() {
	ticker := time.NewTicker(1 * time.Minute)
	defer ticker.Stop()

	for range ticker.C {
		rl.mu.Lock()
		now := time.Now()

		// Nettoyage des IPs bloquées expirées
		for ip, blockUntil := range rl.blockedIPs {
			if now.After(blockUntil) {
				delete(rl.blockedIPs, ip)
			}
		}

		// Nettoyage des IMEIs bloqués expirés
		for imei, blockUntil := range rl.blockedIMEIs {
			if now.After(blockUntil) {
				delete(rl.blockedIMEIs, imei)
			}
		}

		// Nettoyage des compteurs expirés (fenêtre de 1 minute)
		for key, entry := range rl.ipLimits {
			if now.Sub(entry.windowStart) > 1*time.Minute {
				delete(rl.ipLimits, key)
			}
		}

		for key, entry := range rl.imeiLimits {
			if now.Sub(entry.windowStart) > 1*time.Minute {
				delete(rl.imeiLimits, key)
			}
		}

		rl.mu.Unlock()
	}
}

// CheckIP vérifie si une IP est autorisée
func (rl *RateLimiter) CheckIP(ip string) error {
	rl.mu.Lock()
	defer rl.mu.Unlock()

	// Vérifier si l'IP est bloquée
	if blockUntil, blocked := rl.blockedIPs[ip]; blocked {
		if time.Now().Before(blockUntil) {
			return fmt.Errorf("IP bloquée jusqu'à %v", blockUntil)
		}
		// Blocage expiré, le supprimer
		delete(rl.blockedIPs, ip)
	}

	// Vérifier le rate limit
	now := time.Now()
	entry, exists := rl.ipLimits[ip]

	if !exists || now.Sub(entry.windowStart) > 1*time.Minute {
		// Nouvelle fenêtre
		rl.ipLimits[ip] = &rateLimitEntry{
			count:       1,
			windowStart: now,
		}
		return nil
	}

	entry.count++
	if entry.count > rl.config.RateLimitPerIP {
		// Bloquer l'IP
		blockUntil := now.Add(time.Duration(rl.config.BlockDuration) * time.Second)
		rl.blockedIPs[ip] = blockUntil
		delete(rl.ipLimits, ip)
		return fmt.Errorf("rate limit dépassé pour IP %s, bloquée jusqu'à %v", ip, blockUntil)
	}

	return nil
}

// CheckIMEI vérifie si un IMEI est autorisé
func (rl *RateLimiter) CheckIMEI(imei string) error {
	if imei == "" {
		return nil // Pas de vérification si IMEI vide
	}

	rl.mu.Lock()
	defer rl.mu.Unlock()

	// Vérifier si l'IMEI est bloqué
	if blockUntil, blocked := rl.blockedIMEIs[imei]; blocked {
		if time.Now().Before(blockUntil) {
			return fmt.Errorf("IMEI bloqué jusqu'à %v", blockUntil)
		}
		delete(rl.blockedIMEIs, imei)
	}

	// Vérifier le rate limit
	now := time.Now()
	entry, exists := rl.imeiLimits[imei]

	if !exists || now.Sub(entry.windowStart) > 1*time.Minute {
		rl.imeiLimits[imei] = &rateLimitEntry{
			count:       1,
			windowStart: now,
		}
		return nil
	}

	entry.count++
	if entry.count > rl.config.RateLimitPerIMEI {
		blockUntil := now.Add(time.Duration(rl.config.BlockDuration) * time.Second)
		rl.blockedIMEIs[imei] = blockUntil
		delete(rl.imeiLimits, imei)
		return fmt.Errorf("rate limit dépassé pour IMEI %s, bloqué jusqu'à %v", imei, blockUntil)
	}

	return nil
}

// SecurityConnectionManager gère les connexions simultanées
type SecurityConnectionManager struct {
	activeConnections map[string]time.Time
	currentCount      int
	maxConnections    int
	mu                sync.RWMutex
}

// NewSecurityConnectionManager crée un nouveau gestionnaire de connexions
func NewSecurityConnectionManager(maxConnections int) *SecurityConnectionManager {
	cm := &SecurityConnectionManager{
		activeConnections: make(map[string]time.Time),
		maxConnections:    maxConnections,
	}

	// Nettoyage périodique des connexions orphelines
	go cm.cleanup()
	return cm
}

func (cm *SecurityConnectionManager) cleanup() {
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	for range ticker.C {
		cm.mu.Lock()
		now := time.Now()
		for addr, lastSeen := range cm.activeConnections {
			// Supprimer les connexions inactives depuis plus de 5 minutes
			if now.Sub(lastSeen) > 5*time.Minute {
				delete(cm.activeConnections, addr)
				cm.currentCount--
			}
		}
		cm.mu.Unlock()
	}
}

// Acquire tente d'acquérir une connexion
func (cm *SecurityConnectionManager) Acquire(addr string) error {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	if cm.currentCount >= cm.maxConnections {
		return fmt.Errorf("nombre maximum de connexions atteint (%d)", cm.maxConnections)
	}

	cm.activeConnections[addr] = time.Now()
	cm.currentCount++
	return nil
}

// Release libère une connexion
func (cm *SecurityConnectionManager) Release(addr string) {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	if _, exists := cm.activeConnections[addr]; exists {
		delete(cm.activeConnections, addr)
		cm.currentCount--
	}
}

// Validator valide les données reçues
type Validator struct {
	maxPacketSize int
}

// NewValidator crée un nouveau validateur
func NewValidator(maxPacketSize int) *Validator {
	return &Validator{
		maxPacketSize: maxPacketSize,
	}
}

// ValidatePacket valide la taille d'un paquet
func (v *Validator) ValidatePacket(data []byte) error {
	if len(data) == 0 {
		return fmt.Errorf("paquet vide")
	}

	if len(data) > v.maxPacketSize {
		return fmt.Errorf("paquet trop grand: %d bytes (max: %d)", len(data), v.maxPacketSize)
	}

	return nil
}

// ValidateIMEI valide le format d'un IMEI
func (v *Validator) ValidateIMEI(imei string) error {
	if len(imei) != 15 {
		return fmt.Errorf("IMEI doit contenir 15 chiffres, reçu: %d", len(imei))
	}

	for _, c := range imei {
		if c < '0' || c > '9' {
			return fmt.Errorf("IMEI contient des caractères non numériques: %s", imei)
		}
	}

	return nil
}

// SecurityManager regroupe tous les composants de sécurité
type SecurityManager struct {
	rateLimiter       *RateLimiter
	connectionManager *SecurityConnectionManager
	validator         *Validator
	config            SecurityConfig
}

// NewSecurityManager crée un nouveau gestionnaire de sécurité
func NewSecurityManager(config SecurityConfig) *SecurityManager {
	return &SecurityManager{
		rateLimiter:       NewRateLimiter(config),
		connectionManager: NewSecurityConnectionManager(config.MaxConnections),
		validator:         NewValidator(config.MaxPacketSize),
		config:            config,
	}
}

// ValidateConnection valide une nouvelle connexion
func (sm *SecurityManager) ValidateConnection(conn net.Conn) error {
	remoteAddr := conn.RemoteAddr().String()
	ip, _, _ := net.SplitHostPort(remoteAddr)

	// Vérifier le rate limit IP
	if err := sm.rateLimiter.CheckIP(ip); err != nil {
		return fmt.Errorf("validation IP échouée: %v", err)
	}

	// Vérifier le nombre de connexions
	if err := sm.connectionManager.Acquire(remoteAddr); err != nil {
		return fmt.Errorf("validation connexion échouée: %v", err)
	}

	return nil
}

// ValidatePacket valide un paquet de données
func (sm *SecurityManager) ValidatePacket(data []byte, imei string) error {
	// Valider la taille
	if err := sm.validator.ValidatePacket(data); err != nil {
		return err
	}

	// Valider l'IMEI si présent
	if imei != "" {
		if err := sm.validator.ValidateIMEI(imei); err != nil {
			return err
		}

		// Vérifier le rate limit IMEI
		if err := sm.rateLimiter.CheckIMEI(imei); err != nil {
			return err
		}
	}

	return nil
}

// ReleaseConnection libère une connexion
func (sm *SecurityManager) ReleaseConnection(conn net.Conn) {
	sm.connectionManager.Release(conn.RemoteAddr().String())
}
