package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"time"

	"navic/ingestion/fmxxxx"
	"navic/ingestion/gt06"
	"navic/ingestion/tk102"
	"navic/ingestion/tk103"
)

// CommandRequest représente une demande de commande depuis Django
type CommandRequest struct {
	Protocol string                 `json:"protocol"`
	IMEI     string                 `json:"imei"`
	Command  string                 `json:"command"`
	Params   map[string]interface{} `json:"params,omitempty"`
}

// CommandResponse représente la réponse à une commande
type CommandResponse struct {
	Success bool   `json:"success"`
	Message string `json:"message,omitempty"`
	Error   string `json:"error,omitempty"`
}

// CommandSender gère l'envoi de commandes aux balises
type CommandSender struct {
	connectionManager *ConnectionManager
}

// NewCommandSender crée un nouveau gestionnaire de commandes
func NewCommandSender(connectionManager *ConnectionManager) *CommandSender {
	return &CommandSender{
		connectionManager: connectionManager,
	}
}

// SendCommand envoie une commande à UNE SEULE balise spécifique (identifiée par son IMEI)
func (cs *CommandSender) SendCommand(req CommandRequest) error {
	// Récupérer la connexion active pour cette balise spécifique
	// La commande est envoyée individuellement à cette balise uniquement
	conn, err := cs.connectionManager.GetConnection(req.Protocol, req.IMEI)
	if err != nil {
		return fmt.Errorf("connexion non disponible pour la balise %s: %v. La balise doit être connectée via TCP pour recevoir des commandes.", req.IMEI, err)
	}

	// Encoder la commande selon le protocole
	var commandData []byte
	var encodeErr error

	switch req.Protocol {
	case "GT06", "GT06N":
		// GT06 et GT06N utilisent le même format de commandes
		cmdType, err := parseGT06Command(req.Command)
		if err != nil {
			return err
		}
		commandData, encodeErr = gt06.EncodeCommand(cmdType, req.IMEI, req.Params)

	case "TK102":
		cmdType := tk102.CommandType(req.Command)
		commandData, encodeErr = tk102.EncodeCommand(cmdType, req.IMEI, req.Params)
	case "TK103":
		cmdType := tk103.CommandType(req.Command)
		commandData, encodeErr = tk103.EncodeCommand(cmdType, req.IMEI, req.Params)

	case "FMXXXX", "TELTONIKA":
		cmdType, err := parseFMXXXXCommand(req.Command)
		if err != nil {
			return err
		}
		commandData, encodeErr = fmxxxx.EncodeCommand(cmdType, req.IMEI, req.Params)

	default:
		return fmt.Errorf("protocole non supporté pour les commandes: %s", req.Protocol)
	}

	if encodeErr != nil {
		return fmt.Errorf("erreur encodage commande: %v", encodeErr)
	}

	// Envoyer la commande avec timeout à cette balise spécifique
	// La commande est envoyée individuellement, une seule balise la recevra
	conn.SetWriteDeadline(time.Now().Add(5 * time.Second))
	_, err = conn.Write(commandData)
	if err != nil {
		return fmt.Errorf("erreur envoi commande à la balise %s: %v", req.IMEI, err)
	}

	log.Printf("Commande envoyée individuellement à la balise %s: Protocol=%s, Command=%s", req.IMEI, req.Protocol, req.Command)
	return nil
}

// parseGT06Command convertit une commande string en CommandType GT06
func parseGT06Command(cmd string) (gt06.CommandType, error) {
	cmdMap := map[string]gt06.CommandType{
		"cut_engine":      gt06.CommandCutEngine,
		"restore_engine":  gt06.CommandRestoreEngine,
		"set_output":      gt06.CommandSetOutput,
		"clear_output":    gt06.CommandClearOutput,
		"request_gps":     gt06.CommandRequestGPS,
		"set_interval":    gt06.CommandSetInterval,
		"set_speed_limit": gt06.CommandSetSpeedLimit,
		"set_geofence":    gt06.CommandSetGeofence,
	}

	if cmdType, ok := cmdMap[cmd]; ok {
		return cmdType, nil
	}
	return 0, fmt.Errorf("commande GT06 inconnue: %s", cmd)
}

// parseFMXXXXCommand convertit une commande string en CommandType FMXXXX
func parseFMXXXXCommand(cmd string) (fmxxxx.CommandType, error) {
	cmdMap := map[string]fmxxxx.CommandType{
		"get_status":     fmxxxx.CommandGetStatus,
		"set_io":         fmxxxx.CommandSetIO,
		"cut_engine":     fmxxxx.CommandCutEngine,
		"restore_engine": fmxxxx.CommandRestoreEngine,
		"request_gps":    fmxxxx.CommandRequestGPS,
		"set_interval":   fmxxxx.CommandSetInterval,
	}

	if cmdType, ok := cmdMap[cmd]; ok {
		return cmdType, nil
	}
	return 0, fmt.Errorf("commande FMXXXX inconnue: %s", cmd)
}

// HandleCommandRequest gère une requête HTTP de commande
func HandleCommandRequest(w http.ResponseWriter, r *http.Request, commandSender *CommandSender) {
	if r.Method != http.MethodPost {
		http.Error(w, "Méthode non autorisée", http.StatusMethodNotAllowed)
		return
	}

	var req CommandRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, fmt.Sprintf("Erreur décodage JSON: %v", err), http.StatusBadRequest)
		return
	}

	// Validation
	if req.Protocol == "" || req.IMEI == "" || req.Command == "" {
		http.Error(w, "Paramètres manquants: protocol, imei et command sont requis", http.StatusBadRequest)
		return
	}

	// Envoyer la commande
	err := commandSender.SendCommand(req)
	if err != nil {
		response := CommandResponse{
			Success: false,
			Error:   err.Error(),
		}
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusInternalServerError)
		json.NewEncoder(w).Encode(response)
		return
	}

	response := CommandResponse{
		Success: true,
		Message: fmt.Sprintf("Commande '%s' envoyée avec succès à %s (%s)", req.Command, req.IMEI, req.Protocol),
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(response)
}
