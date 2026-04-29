package fmxxxx

import (
	"encoding/binary"
	"fmt"
)

// CommandType représente le type de commande FMXXXX/Teltonika
type CommandType byte

const (
	CommandGetStatus      CommandType = 0x01 // Obtenir le status
	CommandSetIO          CommandType = 0x02 // Définir IO
	CommandCutEngine      CommandType = 0x03 // Coupure moteur
	CommandRestoreEngine  CommandType = 0x04 // Restauration moteur
	CommandRequestGPS     CommandType = 0x05 // Demander position
	CommandSetInterval    CommandType = 0x06 // Définir intervalle
)

// EncodeCommand encode une commande FMXXXX/Teltonika
func EncodeCommand(cmdType CommandType, imei string, params map[string]interface{}) ([]byte, error) {
	// Format Teltonika: [IMEI_LENGTH][IMEI][COMMAND_ID][PARAMS...]
	frame := make([]byte, 0)

	// IMEI length
	frame = append(frame, byte(len(imei)))

	// IMEI
	frame = append(frame, []byte(imei)...)

	// Command ID
	frame = append(frame, byte(cmdType))

	// Paramètres selon le type de commande
	switch cmdType {
	case CommandGetStatus:
		// Pas de paramètres supplémentaires

	case CommandSetIO:
		// [IO_ID][VALUE]
		ioID, ok := params["io_id"].(byte)
		if !ok {
			return nil, fmt.Errorf("paramètre 'io_id' manquant ou invalide")
		}
		value, ok := params["value"].(byte)
		if !ok {
			return nil, fmt.Errorf("paramètre 'value' manquant ou invalide")
		}
		frame = append(frame, ioID, value)

	case CommandCutEngine:
		// Pas de paramètres supplémentaires

	case CommandRestoreEngine:
		// Pas de paramètres supplémentaires

	case CommandRequestGPS:
		// Pas de paramètres supplémentaires

	case CommandSetInterval:
		// [INTERVAL_HIGH][INTERVAL_LOW]
		interval, ok := params["interval"].(uint16)
		if !ok {
			return nil, fmt.Errorf("paramètre 'interval' manquant ou invalide")
		}
		intervalBytes := make([]byte, 2)
		binary.BigEndian.PutUint16(intervalBytes, interval)
		frame = append(frame, intervalBytes...)

	default:
		return nil, fmt.Errorf("type de commande inconnu: 0x%02X", cmdType)
	}

	return frame, nil
}