package main

import (
	"fmt"
	"net"
	"sync"
	"time"
)

// ActiveConnection représente une connexion TCP active avec son IMEI
type ActiveConnection struct {
	Conn       net.Conn
	IMEI       string
	Protocol   string
	LastSeen   time.Time
	RemoteAddr string
}

// ConnectionManager gère les connexions TCP actives par IMEI et protocole
type ConnectionManager struct {
	connections map[string]*ActiveConnection // key: "protocol:imei" -> connection
	mu          sync.RWMutex
}

// NewConnectionManager crée un nouveau gestionnaire de connexions
func NewConnectionManager() *ConnectionManager {
	cm := &ConnectionManager{
		connections: make(map[string]*ActiveConnection),
	}

	// Nettoyage périodique des connexions fermées
	go cm.cleanup()
	return cm
}

// cleanup nettoie les connexions fermées
func (cm *ConnectionManager) cleanup() {
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	for range ticker.C {
		cm.mu.Lock()
		now := time.Now()
		for key, conn := range cm.connections {
			// Supprimer les connexions fermées ou inactives depuis plus de 10 minutes
			if conn.Conn == nil || now.Sub(conn.LastSeen) > 10*time.Minute {
				if conn.Conn != nil {
					conn.Conn.Close()
				}
				delete(cm.connections, key)
			}
		}
		cm.mu.Unlock()
	}
}

// Register enregistre une connexion active
func (cm *ConnectionManager) Register(protocol, imei string, conn net.Conn) {
	if imei == "" {
		return
	}

	cm.mu.Lock()
	defer cm.mu.Unlock()

	key := fmt.Sprintf("%s:%s", protocol, imei)

	// Fermer l'ancienne connexion si elle existe
	if oldConn, exists := cm.connections[key]; exists && oldConn.Conn != nil {
		oldConn.Conn.Close()
	}

	cm.connections[key] = &ActiveConnection{
		Conn:       conn,
		IMEI:       imei,
		Protocol:   protocol,
		LastSeen:   time.Now(),
		RemoteAddr: conn.RemoteAddr().String(),
	}
}

// UpdateLastSeen met à jour le timestamp de dernière activité
func (cm *ConnectionManager) UpdateLastSeen(protocol, imei string) {
	if imei == "" {
		return
	}

	cm.mu.Lock()
	defer cm.mu.Unlock()

	key := fmt.Sprintf("%s:%s", protocol, imei)
	if conn, exists := cm.connections[key]; exists {
		conn.LastSeen = time.Now()
	}
}

// GetConnection récupère une connexion active par protocole et IMEI
func (cm *ConnectionManager) GetConnection(protocol, imei string) (net.Conn, error) {
	if imei == "" {
		return nil, fmt.Errorf("IMEI vide")
	}

	cm.mu.RLock()
	defer cm.mu.RUnlock()

	key := fmt.Sprintf("%s:%s", protocol, imei)
	conn, exists := cm.connections[key]
	if !exists || conn.Conn == nil {
		return nil, fmt.Errorf("aucune connexion active pour IMEI %s (protocole %s)", imei, protocol)
	}

	// Vérifier que la connexion est toujours valide
	if conn.Conn == nil {
		return nil, fmt.Errorf("connexion fermée pour IMEI %s", imei)
	}

	return conn.Conn, nil
}

// Unregister supprime une connexion
func (cm *ConnectionManager) Unregister(protocol, imei string) {
	if imei == "" {
		return
	}

	cm.mu.Lock()
	defer cm.mu.Unlock()

	key := fmt.Sprintf("%s:%s", protocol, imei)
	if conn, exists := cm.connections[key]; exists {
		if conn.Conn != nil {
			conn.Conn.Close()
		}
		delete(cm.connections, key)
	}
}

// GetAllConnections retourne toutes les connexions actives (pour debug)
func (cm *ConnectionManager) GetAllConnections() map[string]*ActiveConnection {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	result := make(map[string]*ActiveConnection)
	for k, v := range cm.connections {
		result[k] = v
	}
	return result
}
