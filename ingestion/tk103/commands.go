package tk103

import (
	"encoding/binary"
	"fmt"
)

// CommandType représente le type de commande TK103
type CommandType string

const (
	CommandCutEngine     CommandType = "CUTENGINE"
	CommandRestoreEngine CommandType = "RESTOREENGINE"
	CommandSetOutput     CommandType = "SETOUTPUT"
	CommandClearOutput   CommandType = "CLEAROUTPUT"
	CommandRequestGPS    CommandType = "REQUESTGPS"
	CommandSetInterval   CommandType = "SETINTERVAL"
)

// EncodeCommand encode une commande TK103
func EncodeCommand(cmdType CommandType, imei string, params map[string]interface{}) ([]byte, error) {
	var command string

	switch cmdType {
	case CommandCutEngine:
		// Format: *HQ,IMEI,CUTENGINE#
		command = fmt.Sprintf("*HQ,%s,CUTENGINE#", imei)

	case CommandRestoreEngine:
		// Format: *HQ,IMEI,RESTOREENGINE#
		command = fmt.Sprintf("*HQ,%s,RESTOREENGINE#", imei)

	case CommandSetOutput:
		// Format: *HQ,IMEI,SETOUTPUT,OUTPUT_NUMBER#
		outputNum, ok := params["output"].(int)
		if !ok {
			return nil, fmt.Errorf("paramètre 'output' manquant ou invalide")
		}
		command = fmt.Sprintf("*HQ,%s,SETOUTPUT,%d#", imei, outputNum)

	case CommandClearOutput:
		// Format: *HQ,IMEI,CLEAROUTPUT,OUTPUT_NUMBER#
		outputNum, ok := params["output"].(int)
		if !ok {
			return nil, fmt.Errorf("paramètre 'output' manquant ou invalide")
		}
		command = fmt.Sprintf("*HQ,%s,CLEAROUTPUT,%d#", imei, outputNum)

	case CommandRequestGPS:
		// Format: *HQ,IMEI,REQUESTGPS#
		command = fmt.Sprintf("*HQ,%s,REQUESTGPS#", imei)

	case CommandSetInterval:
		// Format: *HQ,IMEI,SETINTERVAL,INTERVAL#
		interval, ok := params["interval"].(int)
		if !ok {
			return nil, fmt.Errorf("paramètre 'interval' manquant ou invalide")
		}
		command = fmt.Sprintf("*HQ,%s,SETINTERVAL,%d#", imei, interval)

	default:
		return nil, fmt.Errorf("type de commande inconnu: %s", cmdType)
	}

	return []byte(command), nil
}

// EncodeACK génère un ACK binaire pour TK103/GT06
// Format: 0x78 0x78 [length=0x05] [proto] [serial=2] [crc=2] 0x0D 0x0A
func EncodeACK(protocol byte, serial uint16) []byte {
	ack := make([]byte, 10)
	ack[0] = 0x78
	ack[1] = 0x78
	ack[2] = 0x05
	ack[3] = protocol
	binary.BigEndian.PutUint16(ack[4:6], serial)

	crc := CRCX25(ack[2:6])
	binary.BigEndian.PutUint16(ack[6:8], crc)

	ack[8] = 0x0D
	ack[9] = 0x0A

	return ack
}
