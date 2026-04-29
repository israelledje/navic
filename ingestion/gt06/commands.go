package gt06

import (
	"encoding/binary"
	"fmt"
)

// CommandType représente le type de commande GT06
type CommandType byte

const (
	CommandCutEngine     CommandType = 0x80 // Coupure moteur
	CommandRestoreEngine CommandType = 0x81 // Restauration moteur
	CommandSetOutput     CommandType = 0x82 // Activer sortie
	CommandClearOutput   CommandType = 0x83 // Désactiver sortie
	CommandRequestGPS    CommandType = 0x16 // Demander position GPS
	CommandSetInterval   CommandType = 0x85 // Définir intervalle de rapport
	CommandSetSpeedLimit CommandType = 0x86 // Définir limite de vitesse
	CommandSetGeofence   CommandType = 0x87 // Définir géofence
)

// EncodeCommand encode une commande GT06
func EncodeCommand(cmdType CommandType, imei string, params map[string]interface{}) ([]byte, error) {
	var payload []byte
	var length byte

	switch cmdType {
	case CommandCutEngine:
		// Commande coupure moteur: [0x80][0x00]
		payload = []byte{0x80, 0x00}
		length = 0x02

	case CommandRestoreEngine:
		// Commande restauration moteur: [0x81][0x00]
		payload = []byte{0x81, 0x00}
		length = 0x02

	case CommandSetOutput:
		// Activer sortie: [0x82][output_number]
		outputNum, ok := params["output"].(byte)
		if !ok {
			return nil, fmt.Errorf("paramètre 'output' manquant ou invalide")
		}
		payload = []byte{0x82, outputNum}
		length = 0x02

	case CommandClearOutput:
		// Désactiver sortie: [0x83][output_number]
		outputNum, ok := params["output"].(byte)
		if !ok {
			return nil, fmt.Errorf("paramètre 'output' manquant ou invalide")
		}
		payload = []byte{0x83, outputNum}
		length = 0x02

	case CommandRequestGPS:
		// Demander position: [0x16]
		payload = []byte{0x16}
		length = 0x01

	case CommandSetInterval:
		// Définir intervalle: [0x85][interval_high][interval_low]
		interval, ok := params["interval"].(uint16)
		if !ok {
			return nil, fmt.Errorf("paramètre 'interval' manquant ou invalide")
		}
		payload = make([]byte, 3)
		payload[0] = 0x85
		binary.BigEndian.PutUint16(payload[1:], interval)
		length = 0x03

	case CommandSetSpeedLimit:
		// Définir limite vitesse: [0x86][speed]
		speed, ok := params["speed"].(byte)
		if !ok {
			return nil, fmt.Errorf("paramètre 'speed' manquant ou invalide")
		}
		payload = []byte{0x86, speed}
		length = 0x02

	case CommandSetGeofence:
		// Définir géofence: [0x87][lat_high][lat_low][lon_high][lon_low][radius]
		lat, latOk := params["latitude"].(float64)
		lon, lonOk := params["longitude"].(float64)
		radius, radiusOk := params["radius"].(uint16)
		if !latOk || !lonOk || !radiusOk {
			return nil, fmt.Errorf("paramètres géofence manquants ou invalides")
		}
		payload = make([]byte, 9)
		payload[0] = 0x87
		latInt := uint32(lat * 100000)
		lonInt := uint32(lon * 100000)
		binary.BigEndian.PutUint32(payload[1:], latInt)
		binary.BigEndian.PutUint32(payload[5:], lonInt)
		binary.BigEndian.PutUint16(payload[9:], radius)
		length = 0x0B

	default:
		return nil, fmt.Errorf("type de commande inconnu: 0x%02X", cmdType)
	}

	// Construire la trame GT06
	// [0x78][0x78][length][protocol][payload][serial][crc][0x0D][0x0A]
	frame := make([]byte, 0, 10+int(length))

	// Header
	frame = append(frame, 0x78, 0x78)

	// Length
	frame = append(frame, length)

	// Protocol (type de commande)
	frame = append(frame, byte(cmdType))

	// Payload
	frame = append(frame, payload...)

	// Serial number (0x0000 pour les commandes)
	serial := uint16(0)
	frame = append(frame, byte(serial>>8), byte(serial&0xFF))

	// CRC (sur length + protocol + payload + serial)
	crcData := frame[2:]
	crc := CRC16(crcData)
	frame = append(frame, byte(crc>>8), byte(crc&0xFF))

	// Stop bits
	frame = append(frame, 0x0D, 0x0A)

	return frame, nil
}

// EncodeACK génère un ACK binaire pour GT06
func EncodeACK(protocol byte, serial uint16) []byte {
	ack := make([]byte, 10)
	ack[0] = 0x78
	ack[1] = 0x78
	ack[2] = 0x05
	ack[3] = protocol
	binary.BigEndian.PutUint16(ack[4:6], serial)

	crc := CRC16(ack[2:6])
	binary.BigEndian.PutUint16(ack[6:8], crc)

	ack[8] = 0x0D
	ack[9] = 0x0A

	return ack
}
