package main

import (
	"encoding/hex"
	"io"
	"log"
	"net"
	"sync"
	"time"
)

// ProtocolServer gère un serveur pour un protocole spécifique
type ProtocolServer struct {
	config            ProtocolConfig
	decoder           Decoder
	securityManager   *SecurityManager
	imeiStore         *IMEIStore         // Pour stocker les IMEI par connexion TCP
	connectionManager *ConnectionManager // Pour gérer les connexions actives
	djangoURL         string             // URL de l'API Django
	apiKey            string             // Clé API pour Django
	mu                sync.RWMutex
}

// IMEIStore stocke les IMEI associés aux connexions TCP
type IMEIStore struct {
	connections map[string]string // remoteAddr -> IMEI
	mu          sync.RWMutex
}

func NewIMEIStore() *IMEIStore {
	return &IMEIStore{
		connections: make(map[string]string),
	}
}

func (is *IMEIStore) Set(addr, imei string) {
	is.mu.Lock()
	defer is.mu.Unlock()
	is.connections[addr] = imei
}

func (is *IMEIStore) Get(addr string) (string, bool) {
	is.mu.RLock()
	defer is.mu.RUnlock()
	imei, exists := is.connections[addr]
	return imei, exists
}

func (is *IMEIStore) Delete(addr string) {
	is.mu.Lock()
	defer is.mu.Unlock()
	delete(is.connections, addr)
}

// NewProtocolServer crée un nouveau serveur pour un protocole
func NewProtocolServer(config ProtocolConfig, decoder Decoder, securityManager *SecurityManager, connectionManager *ConnectionManager, djangoURL string, apiKey string) *ProtocolServer {
	return &ProtocolServer{
		config:            config,
		decoder:           decoder,
		securityManager:   securityManager,
		imeiStore:         NewIMEIStore(),
		connectionManager: connectionManager,
		djangoURL:         djangoURL,
		apiKey:            apiKey,
	}
}

// Start démarre les serveurs TCP et UDP pour ce protocole
func (ps *ProtocolServer) Start() error {
	if !ps.config.Enabled {
		log.Printf("Protocole %s désactivé, ignoré", ps.config.Name)
		return nil
	}

	log.Printf("Démarrage serveur pour protocole %s (TCP:%s, UDP:%s)",
		ps.config.Name, ps.config.TCPPort, ps.config.UDPPort)

	// Démarrer TCP
	if ps.config.TCPPort != "" {
		go ps.startTCPServer()
	}

	// Démarrer UDP
	if ps.config.UDPPort != "" {
		go ps.startUDPServer()
	}

	return nil
}

// startTCPServer démarre le serveur TCP
func (ps *ProtocolServer) startTCPServer() {
	listener, err := net.Listen("tcp", ":"+ps.config.TCPPort)
	if err != nil {
		log.Printf("ERREUR: Impossible de démarrer serveur TCP %s sur port %s: %v",
			ps.config.Name, ps.config.TCPPort, err)
		return
	}
	defer listener.Close()

	log.Printf("✓ Serveur TCP %s démarré sur port %s", ps.config.Name, ps.config.TCPPort)

	for {
		conn, err := listener.Accept()
		if err != nil {
			log.Printf("Erreur acceptation connexion TCP %s: %v", ps.config.Name, err)
			continue
		}

		// Validation de sécurité avant traitement
		if err := ps.securityManager.ValidateConnection(conn); err != nil {
			log.Printf("Connexion TCP %s rejetée: %v", ps.config.Name, err)
			conn.Close()
			continue
		}

		// Gérer la connexion dans une goroutine
		go ps.handleTCPConnection(conn)
	}
}

// startUDPServer démarre le serveur UDP
func (ps *ProtocolServer) startUDPServer() {
	addr, err := net.ResolveUDPAddr("udp", ":"+ps.config.UDPPort)
	if err != nil {
		log.Printf("ERREUR: Résolution adresse UDP %s: %v", ps.config.Name, err)
		return
	}

	conn, err := net.ListenUDP("udp", addr)
	if err != nil {
		log.Printf("ERREUR: Impossible de démarrer serveur UDP %s sur port %s: %v",
			ps.config.Name, ps.config.UDPPort, err)
		return
	}
	defer conn.Close()

	log.Printf("✓ Serveur UDP %s démarré sur port %s", ps.config.Name, ps.config.UDPPort)

	buffer := make([]byte, ps.config.MaxPacketSize)

	for {
		conn.SetReadDeadline(time.Now().Add(time.Duration(ps.config.ReadTimeout) * time.Second))

		n, remoteAddr, err := conn.ReadFromUDP(buffer)
		if err != nil {
			if netErr, ok := err.(net.Error); ok && netErr.Timeout() {
				continue
			}
			log.Printf("Erreur lecture UDP %s: %v", ps.config.Name, err)
			continue
		}

		if n == 0 {
			continue
		}

		data := make([]byte, n)
		copy(data, buffer[:n])

		// Traiter le paquet dans une goroutine
		go ps.handleUDPPacket(data, remoteAddr)
	}
}

// handleTCPConnection gère une connexion TCP
func (ps *ProtocolServer) handleTCPConnection(conn net.Conn) {
	defer func() {
		ps.securityManager.ReleaseConnection(conn)
		// Récupérer l'IMEI avant de supprimer
		if imei, exists := ps.imeiStore.Get(conn.RemoteAddr().String()); exists {
			ps.connectionManager.Unregister(ps.config.Name, imei)
			// Notifier Django que le device est hors-ligne
			go notifyDjangoStatus(imei, false, ps.djangoURL, ps.apiKey)
		}
		ps.imeiStore.Delete(conn.RemoteAddr().String())
		conn.Close()
	}()

	remoteAddr := conn.RemoteAddr().String()
	log.Printf("[%s] Nouvelle connexion TCP de %s", ps.config.Name, remoteAddr)

	buffer := make([]byte, ps.config.MaxPacketSize)

	for {
		conn.SetReadDeadline(time.Now().Add(time.Duration(ps.config.ReadTimeout) * time.Second))

		n, err := conn.Read(buffer)
		if err != nil {
			if err == io.EOF {
				log.Printf("[%s] Connexion fermée par le client: %s", ps.config.Name, remoteAddr)
				return
			}
			if netErr, ok := err.(net.Error); ok && netErr.Timeout() {
				// Timeout normal, continuer
				continue
			}
			log.Printf("[%s] Erreur lecture TCP: %v", ps.config.Name, err)
			return
		}

		if n == 0 {
			continue
		}

		data := make([]byte, n)
		copy(data, buffer[:n])

		// Traiter les données
		ps.processData(data, conn, remoteAddr)
	}
}

// handleUDPPacket gère un paquet UDP
func (ps *ProtocolServer) handleUDPPacket(data []byte, remoteAddr *net.UDPAddr) {
	ps.processData(data, nil, remoteAddr.String())
}

// processData traite les données reçues
func (ps *ProtocolServer) processData(data []byte, conn net.Conn, remoteAddr string) {
	// Validation de sécurité du paquet
	if err := ps.securityManager.ValidatePacket(data, ""); err != nil {
		log.Printf("[%s] Paquet rejeté de %s: %v", ps.config.Name, remoteAddr, err)
		return
	}

	log.Printf("[%s] Reçu %d bytes de %s: %s",
		ps.config.Name, len(data), remoteAddr, hex.EncodeToString(data))

	// Décodage avec le décodeur du protocole
	message, err := ps.decoder.Decode(data)
	if err != nil {
		log.Printf("[%s] Erreur décodage: %v", ps.config.Name, err)
		return
	}

	// Envoyer la réponse au tracker si nécessaire (ACK)
	if len(message.Response) > 0 && conn != nil {
		_, err := conn.Write(message.Response)
		if err != nil {
			log.Printf("[%s] Erreur envoi réponse (ACK): %v", ps.config.Name, err)
		} else {
			log.Printf("[%s] Réponse (ACK) envoyée à %s", ps.config.Name, remoteAddr)
		}
	}

	// Si IMEI extrait, le stocker pour les connexions TCP
	if message.IMEI != "" && conn != nil {
		ps.imeiStore.Set(remoteAddr, message.IMEI)
		// Enregistrer la connexion active pour l'envoi de commandes
		ps.connectionManager.Register(ps.config.Name, message.IMEI, conn)
		ps.connectionManager.UpdateLastSeen(ps.config.Name, message.IMEI)
	} else if conn != nil {
		// Essayer de récupérer l'IMEI depuis le store
		if storedIMEI, exists := ps.imeiStore.Get(remoteAddr); exists {
			message.IMEI = storedIMEI
			// Mettre à jour la connexion active
			ps.connectionManager.Register(ps.config.Name, storedIMEI, conn)
			ps.connectionManager.UpdateLastSeen(ps.config.Name, storedIMEI)
		}
	}

	// Validation IMEI si présent
	if message.IMEI != "" {
		if err := ps.securityManager.ValidatePacket(data, message.IMEI); err != nil {
			log.Printf("[%s] Validation IMEI échouée pour %s: %v",
				ps.config.Name, message.IMEI, err)
			return
		}
	}

	// Envoi à Django
	if err := sendToDjango(message, ps.djangoURL, ps.apiKey); err != nil {
		log.Printf("[%s] Erreur envoi à Django: %v", ps.config.Name, err)
	} else {
		log.Printf("[%s] Message envoyé: IMEI=%s", ps.config.Name, message.IMEI)
	}
}
