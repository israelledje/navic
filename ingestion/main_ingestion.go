package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"
)

// GPSMessage représente un message GPS décodé
type GPSMessage struct {
	IMEI       string                 `json:"imei"`
	Protocol   string                 `json:"protocol"`
	Timestamp  time.Time              `json:"timestamp"`
	Latitude   float64                `json:"latitude,omitempty"`
	Longitude  float64                `json:"longitude,omitempty"`
	Speed      float64                `json:"speed,omitempty"`   // en km/h
	Heading    float64                `json:"heading,omitempty"` // en degrés
	Altitude   float64                `json:"altitude,omitempty"`
	Satellites int                    `json:"satellites,omitempty"`
	Battery    int                    `json:"battery,omitempty"` // pourcentage
	Signal     int                    `json:"signal,omitempty"`  // force du signal
	Alerts     []string               `json:"alerts,omitempty"`
	RawData    string                 `json:"raw_data,omitempty"`
	Response   []byte                 `json:"-"` // Réponse à renvoyer au tracker (non envoyé à Django)
	OtherData  map[string]interface{} `json:"other_data,omitempty"`
}

// sendToDjango envoie le message décodé à l'API Django
func sendToDjango(message *GPSMessage, djangoURL string, apiKey string) error {
	jsonData, err := json.Marshal(message)
	if err != nil {
		return fmt.Errorf("erreur encodage JSON: %v", err)
	}

	// Envoi HTTP POST à Django avec retry
	client := &http.Client{
		Timeout: 5 * time.Second,
	}

	maxRetries := 3
	for i := 0; i < maxRetries; i++ {
		req, err := http.NewRequest("POST", djangoURL, bytes.NewBuffer(jsonData))
		if err != nil {
			return fmt.Errorf("erreur création requête: %v", err)
		}

		req.Header.Set("Content-Type", "application/json")
		req.Header.Set("X-API-Key", apiKey)

		resp, err := client.Do(req)
		if err != nil {
			if i == maxRetries-1 {
				return fmt.Errorf("erreur envoi à Django après %d tentatives: %v", maxRetries, err)
			}
			time.Sleep(time.Duration(i+1) * time.Second)
			continue
		}

		defer resp.Body.Close()

		if resp.StatusCode == 200 || resp.StatusCode == 201 {
			return nil
		}

		// Si erreur serveur, réessayer
		if resp.StatusCode >= 500 && i < maxRetries-1 {
			body, _ := io.ReadAll(resp.Body)
			log.Printf("Erreur serveur Django (status %d), nouvelle tentative: %s", resp.StatusCode, string(body))
			time.Sleep(time.Duration(i+1) * time.Second)
			continue
		}

		// Erreur client, ne pas réessayer
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("erreur Django (status %d): %s", resp.StatusCode, string(body))
	}

	return fmt.Errorf("échec envoi à Django après %d tentatives", maxRetries)
}

func main() {
	// Configuration du logging
	log.SetFlags(log.LstdFlags | log.Lshortfile)

	log.Println("╔═══════════════════════════════════════════════════════════╗")
	log.Println("║     Service d'Ingestion GPS Navic - Démarrage            ║")
	log.Println("╚═══════════════════════════════════════════════════════════╝")

	// Chargement de la configuration
	config := LoadConfig()
	log.Printf("Configuration chargée:")
	log.Printf("  - URL Django: %s", config.DjangoURL)
	log.Printf("  - Rate Limit IP: %d req/min", config.Security.RateLimitPerIP)
	log.Printf("  - Rate Limit IMEI: %d req/min", config.Security.RateLimitPerIMEI)
	log.Printf("  - Max Connexions: %d", config.Security.MaxConnections)
	log.Printf("  - Max Taille Paquet: %d bytes", config.Security.MaxPacketSize)

	// Création du gestionnaire de sécurité
	securityManager := NewSecurityManager(config.Security)

	// Création du gestionnaire de connexions actives
	connectionManager := NewConnectionManager()

	// Démarrage des serveurs pour chaque protocole
	servers := make([]*ProtocolServer, 0)

	for protocolName, protocolConfig := range config.Protocols {
		if !protocolConfig.Enabled {
			log.Printf("Protocole %s désactivé", protocolName)
			continue
		}

		decoder := GetDecoder(protocolName)
		if decoder == nil {
			log.Printf("ATTENTION: Décodeur non trouvé pour %s, utilisation du décodeur générique", protocolName)
			decoder = &GenericDecoder{}
		}

		server := NewProtocolServer(protocolConfig, decoder, securityManager, connectionManager, config.DjangoURL, config.APIKey)
		if err := server.Start(); err != nil {
			log.Printf("ERREUR: Impossible de démarrer serveur %s: %v", protocolName, err)
			continue
		}

		servers = append(servers, server)
		log.Printf("✓ Serveur %s configuré (TCP:%s, UDP:%s)",
			protocolName, protocolConfig.TCPPort, protocolConfig.UDPPort)
	}

	if len(servers) == 0 {
		log.Fatal("Aucun serveur démarré. Vérifiez la configuration.")
	}

	log.Println("╔═══════════════════════════════════════════════════════════╗")
	log.Println("║     Tous les serveurs sont démarrés et opérationnels     ║")
	log.Println("╚═══════════════════════════════════════════════════════════╝")

	// Création du gestionnaire de commandes
	commandSender := NewCommandSender(connectionManager)

	// Démarrage du serveur HTTP pour recevoir les commandes
	commandPort := getEnv("COMMAND_PORT", "8080")
	go startCommandServer(commandPort, commandSender)
	log.Printf("✓ Serveur de commandes démarré sur le port %s", commandPort)

	// Gestion des signaux pour arrêt propre
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)

	// Attente d'un signal d'arrêt
	<-sigChan
	log.Println("\n╔═══════════════════════════════════════════════════════════╗")
	log.Println("║     Arrêt du service d'ingestion GPS...                  ║")
	log.Println("╚═══════════════════════════════════════════════════════════╝")

	// Ici on pourrait ajouter un nettoyage propre des ressources
	log.Println("Service arrêté proprement.")
}

// notifyDjangoStatus notifie Django d'un changement de statut de connexion (online/offline)
func notifyDjangoStatus(imei string, isOnline bool, djangoURL string, apiKey string) error {
	statusURL := djangoURL
	// On remplace le dernier segment de l'URL d'ingestion (ingest/) par status/
	if len(statusURL) > 7 && statusURL[len(statusURL)-7:] == "ingest/" {
		statusURL = statusURL[:len(statusURL)-7] + "status/"
	}

	data := map[string]interface{}{
		"imei":      imei,
		"is_online": isOnline,
	}

	jsonData, err := json.Marshal(data)
	if err != nil {
		return err
	}

	client := &http.Client{Timeout: 5 * time.Second}
	req, err := http.NewRequest("POST", statusURL, bytes.NewBuffer(jsonData))
	if err != nil {
		return err
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-API-Key", apiKey)

	resp, err := client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("erreur status API: %d", resp.StatusCode)
	}

	return nil
}
