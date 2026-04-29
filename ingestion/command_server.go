package main

import (
	"encoding/json"
	"log"
	"net/http"
)

// startCommandServer démarre le serveur HTTP pour recevoir les commandes
func startCommandServer(port string, commandSender *CommandSender) {
	mux := http.NewServeMux()

	// Endpoint pour envoyer des commandes
	mux.HandleFunc("/api/command", func(w http.ResponseWriter, r *http.Request) {
		HandleCommandRequest(w, r, commandSender)
	})

	// Endpoint de santé
	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("OK"))
	})

	// Endpoint pour lister les connexions actives (debug)
	mux.HandleFunc("/api/connections", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			http.Error(w, "Méthode non autorisée", http.StatusMethodNotAllowed)
			return
		}

		connections := commandSender.connectionManager.GetAllConnections()
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(connections)
	})

	server := &http.Server{
		Addr:    ":" + port,
		Handler: mux,
	}

	log.Printf("Serveur de commandes HTTP démarré sur le port %s", port)
	if err := server.ListenAndServe(); err != nil {
		log.Fatalf("Erreur démarrage serveur de commandes: %v", err)
	}
}
