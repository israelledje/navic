package tk102

import (
	"fmt"
)

// CommandType représente le type de commande TK102
type CommandType string

const (
	CommandCutEngine     CommandType = "CUTENGINE"
	CommandRestoreEngine CommandType = "RESTOREENGINE"
	CommandSetOutput    CommandType = "SETOUTPUT"
	CommandClearOutput  CommandType = "CLEAROUTPUT"
	CommandRequestGPS   CommandType = "REQUESTGPS"
)

// EncodeCommand encode une commande TK102 (similaire à TK103)
func EncodeCommand(cmdType CommandType, imei string, params map[string]interface{}) ([]byte, error) {
	var command string

	switch cmdType {
	case CommandCutEngine:
		command = fmt.Sprintf("*HQ,%s,CUTENGINE#", imei)
	case CommandRestoreEngine:
		command = fmt.Sprintf("*HQ,%s,RESTOREENGINE#", imei)
	case CommandSetOutput:
		outputNum, ok := params["output"].(int)
		if !ok {
			return nil, fmt.Errorf("paramètre 'output' manquant ou invalide")
		}
		command = fmt.Sprintf("*HQ,%s,SETOUTPUT,%d#", imei, outputNum)
	case CommandClearOutput:
		outputNum, ok := params["output"].(int)
		if !ok {
			return nil, fmt.Errorf("paramètre 'output' manquant ou invalide")
		}
		command = fmt.Sprintf("*HQ,%s,CLEAROUTPUT,%d#", imei, outputNum)
	case CommandRequestGPS:
		command = fmt.Sprintf("*HQ,%s,REQUESTGPS#", imei)
	default:
		return nil, fmt.Errorf("type de commande inconnu: %s", cmdType)
	}

	return []byte(command), nil
}