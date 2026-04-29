package main

import (
	"encoding/hex"
	"fmt"
	"time"

	"navic/ingestion/fmxxxx"
	"navic/ingestion/gt06"
	"navic/ingestion/tk103"
)

// Decoder interface pour différents protocoles GPS
type Decoder interface {
	Decode(data []byte) (*GPSMessage, error)
	GetProtocolName() string
	Validate(data []byte) bool
}

// GT06Decoder pour le protocole GT06
type GT06Decoder struct{}

func (d *GT06Decoder) GetProtocolName() string {
	return "GT06"
}

func (d *GT06Decoder) Validate(data []byte) bool {
	if len(data) < 5 {
		return false
	}
	// GT06 commence par 0x78 0x78 ou 0x79 0x79
	return (data[0] == 0x78 && data[1] == 0x78) || (data[0] == 0x79 && data[1] == 0x79)
}

func (d *GT06Decoder) Decode(data []byte) (*GPSMessage, error) {
	// Utiliser le package gt06 pour décoder
	packet, err := gt06.DecodeFrame(data)
	if err != nil {
		return nil, fmt.Errorf("erreur décodage trame GT06: %v", err)
	}

	msg := &GPSMessage{
		Protocol:  "GT06",
		Timestamp: time.Now(),
		OtherData: make(map[string]interface{}),
		RawData:   hex.EncodeToString(data),
	}

	// Décoder selon le type de paquet
	var deviceEvent gt06.DeviceEvent

	switch packet.Protocol {
	case 0x01: // Login
		imei := gt06.DecodeLogin(packet)
		msg.IMEI = imei
		msg.OtherData["packet_type"] = "LOGIN"
		msg.OtherData["serial"] = packet.Serial
		msg.Response = gt06.EncodeACK(packet.Protocol, packet.Serial)
		return msg, nil

	case 0x12: // GPS data
		deviceEvent = gt06.DecodeGPS(packet)
		if deviceEvent.Latitude != nil {
			msg.Latitude = *deviceEvent.Latitude
		}
		if deviceEvent.Longitude != nil {
			msg.Longitude = *deviceEvent.Longitude
		}
		if deviceEvent.Speed != nil {
			msg.Speed = *deviceEvent.Speed
		}
		if deviceEvent.Heading != nil {
			msg.Heading = *deviceEvent.Heading
		}
		if deviceEvent.Battery != nil {
			msg.Battery = *deviceEvent.Battery
		}
		if deviceEvent.Signal != nil {
			msg.Signal = *deviceEvent.Signal
		}
		msg.Timestamp = deviceEvent.Time
		msg.OtherData["packet_type"] = "GPS"
		msg.OtherData["serial"] = packet.Serial
		msg.OtherData["gps_valid"] = deviceEvent.GPSValid

	case 0x16: // Alarm
		deviceEvent = gt06.DecodeAlarm(packet)
		if deviceEvent.Latitude != nil {
			msg.Latitude = *deviceEvent.Latitude
		}
		if deviceEvent.Longitude != nil {
			msg.Longitude = *deviceEvent.Longitude
		}
		if deviceEvent.Speed != nil {
			msg.Speed = *deviceEvent.Speed
		}
		if deviceEvent.Heading != nil {
			msg.Heading = *deviceEvent.Heading
		}
		if deviceEvent.AlarmCode != nil {
			msg.OtherData["alarm_code"] = *deviceEvent.AlarmCode
		}
		if deviceEvent.AlarmName != nil {
			alerts := []string{*deviceEvent.AlarmName}
			msg.Alerts = alerts
		}
		if deviceEvent.Battery != nil {
			msg.Battery = *deviceEvent.Battery
		}
		if deviceEvent.Signal != nil {
			msg.Signal = *deviceEvent.Signal
		}
		msg.Timestamp = deviceEvent.Time
		msg.OtherData["packet_type"] = "ALARM"
		msg.OtherData["serial"] = packet.Serial

	case 0x13: // Status
		deviceEvent = gt06.DecodeStatus(packet)
		if deviceEvent.Battery != nil {
			msg.Battery = *deviceEvent.Battery
		}
		if deviceEvent.Signal != nil {
			msg.Signal = *deviceEvent.Signal
		}
		if deviceEvent.Status != nil {
			msg.OtherData["status"] = *deviceEvent.Status
		}
		msg.OtherData["packet_type"] = "STATUS"
		msg.OtherData["serial"] = packet.Serial
		msg.Response = gt06.EncodeACK(packet.Protocol, packet.Serial)

	default:
		msg.OtherData["packet_type"] = fmt.Sprintf("UNKNOWN_0x%02X", packet.Protocol)
		msg.OtherData["protocol_byte"] = packet.Protocol
		msg.OtherData["serial"] = packet.Serial
	}

	return msg, nil
}

// GT06NDecoder pour le protocole GT06N (nouvelle version)
type GT06NDecoder struct{}

func (d *GT06NDecoder) GetProtocolName() string {
	return "GT06N"
}

func (d *GT06NDecoder) Validate(data []byte) bool {
	if len(data) < 5 {
		return false
	}
	// GT06N similaire à GT06 mais avec des différences dans le format
	return (data[0] == 0x78 && data[1] == 0x78) || (data[0] == 0x79 && data[1] == 0x79)
}

func (d *GT06NDecoder) Decode(data []byte) (*GPSMessage, error) {
	// Similaire à GT06 mais avec des améliorations
	decoder := &GT06Decoder{}
	return decoder.Decode(data)
}

// TK102Decoder pour le protocole TK102
type TK102Decoder struct{}

func (d *TK102Decoder) GetProtocolName() string {
	return "TK102"
}

func (d *TK102Decoder) Validate(data []byte) bool {
	if len(data) < 10 {
		return false
	}
	// TK102 commence souvent par "(..." ou des patterns spécifiques
	dataStr := string(data)
	return len(dataStr) > 0 && (dataStr[0] == '(' || dataStr[0] == '[')
}

func (d *TK102Decoder) Decode(data []byte) (*GPSMessage, error) {
	msg := &GPSMessage{
		Protocol:  "TK102",
		Timestamp: time.Now(),
		OtherData: make(map[string]interface{}),
	}

	dataStr := string(data)

	// Extraction IMEI (format TK102: souvent dans les premières données)
	imei := extractIMEI(data)
	if imei != "" {
		msg.IMEI = imei
	}

	// Décodage basique TK102 (format texte)
	// Format typique: (359710049912345,240112,A,2234.4669,N,11354.3287,E,0.11,)
	if len(dataStr) > 20 {
		// Parsing simplifié - le vrai décodage TK102 nécessite plus de logique
		msg.OtherData["raw_text"] = dataStr
	}

	msg.RawData = hex.EncodeToString(data)
	return msg, nil
}

// TK103Decoder pour le protocole TK103
type TK103Decoder struct{}

func (d *TK103Decoder) GetProtocolName() string {
	return "TK103"
}

func (d *TK103Decoder) Validate(data []byte) bool {
	if len(data) < 10 {
		return false
	}
	// TK103 commence par 0x78 0x78 (format binaire)
	// Format: [0x78][0x78][length][protocol][payload...][CRC][0x0D][0x0A]
	return data[0] == 0x78 && data[1] == 0x78
}

func (d *TK103Decoder) Decode(data []byte) (*GPSMessage, error) {
	// Utiliser le package tk103 pour décoder
	packet, err := tk103.DecodeFrame(data)
	if err != nil {
		return nil, fmt.Errorf("erreur décodage trame TK103: %v", err)
	}

	msg := &GPSMessage{
		Protocol:  "TK103",
		Timestamp: time.Now(),
		OtherData: make(map[string]interface{}),
		RawData:   hex.EncodeToString(data),
	}

	// Décoder selon le type de paquet
	var deviceEvent tk103.DeviceEvent

	switch packet.Protocol {
	case 0x01: // Login
		imei := tk103.DecodeLogin(packet)
		msg.IMEI = imei
		msg.OtherData["packet_type"] = "LOGIN"
		msg.OtherData["serial"] = packet.Serial
		// Réponse ACK obligatoire pour le Login
		msg.Response = tk103.EncodeACK(packet.Protocol, packet.Serial)
		return msg, nil

	case 0x13: // Heartbeat
		msg.OtherData["packet_type"] = "HEARTBEAT"
		msg.OtherData["serial"] = packet.Serial
		// Réponse ACK pour le Heartbeat
		msg.Response = tk103.EncodeACK(packet.Protocol, packet.Serial)
		return msg, nil

	case 0x12, 0x1A: // GPS data
		deviceEvent = tk103.DecodeGPS(packet)
		if deviceEvent.Latitude != nil {
			msg.Latitude = *deviceEvent.Latitude
		}
		if deviceEvent.Longitude != nil {
			msg.Longitude = *deviceEvent.Longitude
		}
		if deviceEvent.Speed != nil {
			msg.Speed = float64(*deviceEvent.Speed)
		}
		if deviceEvent.Heading != nil {
			msg.Heading = float64(*deviceEvent.Heading)
		}
		msg.Timestamp = deviceEvent.Time
		msg.OtherData["packet_type"] = "GPS"
		msg.OtherData["raw_protocol"] = deviceEvent.RawProtocol
		msg.OtherData["serial"] = packet.Serial
		msg.OtherData["gps_valid"] = deviceEvent.GPSValid

	case 0x26: // Alarm
		deviceEvent = tk103.DecodeAlarm(packet)
		if deviceEvent.AlarmCode != nil {
			msg.OtherData["alarm_code"] = *deviceEvent.AlarmCode
		}
		if deviceEvent.AlarmName != nil {
			alerts := []string{*deviceEvent.AlarmName}
			msg.Alerts = alerts
		}
		if deviceEvent.Latitude != nil {
			msg.Latitude = *deviceEvent.Latitude
		}
		if deviceEvent.Longitude != nil {
			msg.Longitude = *deviceEvent.Longitude
		}
		msg.Timestamp = deviceEvent.Time
		msg.OtherData["packet_type"] = "ALARM"
		msg.OtherData["raw_protocol"] = deviceEvent.RawProtocol
		msg.OtherData["serial"] = packet.Serial

	default:
		msg.OtherData["packet_type"] = fmt.Sprintf("UNKNOWN_0x%02X", packet.Protocol)
		msg.OtherData["protocol_byte"] = packet.Protocol
		msg.OtherData["serial"] = packet.Serial
	}

	return msg, nil
}

// Protocol303Decoder pour le protocole 303
type Protocol303Decoder struct{}

func (d *Protocol303Decoder) GetProtocolName() string {
	return "303"
}

func (d *Protocol303Decoder) Validate(data []byte) bool {
	if len(data) < 5 {
		return false
	}
	// Protocole 303 a souvent un préfixe spécifique
	// Format peut varier, vérification basique
	return len(data) >= 10
}

func (d *Protocol303Decoder) Decode(data []byte) (*GPSMessage, error) {
	msg := &GPSMessage{
		Protocol:  "303",
		Timestamp: time.Now(),
		OtherData: make(map[string]interface{}),
	}

	imei := extractIMEI(data)
	if imei != "" {
		msg.IMEI = imei
	}

	msg.RawData = hex.EncodeToString(data)
	return msg, nil
}

// FMXXXXDecoder pour le protocole FMXXXX/TELTONIKA (même protocole)
type FMXXXXDecoder struct {
	protocolName string // Nom du protocole (FMXXXX ou TELTONIKA)
}

// NewFMXXXXDecoder crée un nouveau décodeur avec un nom de protocole spécifique
func NewFMXXXXDecoder(protocolName string) *FMXXXXDecoder {
	return &FMXXXXDecoder{protocolName: protocolName}
}

func (d *FMXXXXDecoder) GetProtocolName() string {
	if d.protocolName != "" {
		return d.protocolName
	}
	// Par défaut, retourner "TELTONIKA" pour compatibilité
	return "TELTONIKA"
}

func (d *FMXXXXDecoder) Validate(data []byte) bool {
	return fmxxxx.ValidateFrame(data)
}

func (d *FMXXXXDecoder) Decode(data []byte) (*GPSMessage, error) {
	// Utiliser le package fmxxxx pour décoder (FMXXXX et TELTONIKA utilisent le même format)
	avlDataList, imei, response, err := fmxxxx.DecodeFrame(data)
	if err != nil {
		return nil, fmt.Errorf("erreur décodage trame Teltonika/FMXXXX: %v", err)
	}

	msg := &GPSMessage{
		Protocol:  d.GetProtocolName(),
		IMEI:      imei,
		Response:  response,
		Timestamp: time.Now(),
		OtherData: make(map[string]interface{}),
		RawData:   hex.EncodeToString(data),
	}

	if len(avlDataList) == 0 {
		// Probablement un paquet de login, on a l'IMEI et le Response(ACK)
		return msg, nil
	}

	// Prendre la première donnée AVL (pour le message principal)
	avlData := avlDataList[0]
	msg.Timestamp = avlData.Timestamp

	// Extraire les données GPS
	if avlData.GPS != nil {
		msg.Latitude = avlData.GPS.Latitude
		msg.Longitude = avlData.GPS.Longitude
		msg.Speed = float64(avlData.GPS.Speed) // Valeur en km/h pour Teltonika
		msg.Heading = float64(avlData.GPS.Angle)
		msg.Altitude = float64(avlData.GPS.Altitude)
		msg.Satellites = int(avlData.GPS.Satellites)
	}

	// Extraire les données IO (batterie, signal, etc.)
	if avlData.IO != nil {
		msg.OtherData["event_id"] = avlData.IO.EventID
		msg.OtherData["total_io"] = avlData.IO.TotalIO

		// Batterie (généralement dans les IO 1 byte, ID 66 ou 67)
		if battery, ok := avlData.IO.OneByteIO[66]; ok {
			msg.Battery = int(battery)
		} else if battery, ok := avlData.IO.OneByteIO[67]; ok {
			msg.Battery = int(battery)
		}

		// Signal GSM (généralement dans les IO 1 byte, ID 21)
		if signal, ok := avlData.IO.OneByteIO[21]; ok {
			msg.Signal = int(signal)
		}

		// Stocker toutes les IO pour référence
		msg.OtherData["io_1byte"] = avlData.IO.OneByteIO
		msg.OtherData["io_2byte"] = avlData.IO.TwoByteIO
		msg.OtherData["io_4byte"] = avlData.IO.FourByteIO
	}

	msg.OtherData["priority"] = avlData.Priority
	msg.OtherData["avl_count"] = len(avlDataList)

	return msg, nil
}

// Fonctions utilitaires
func isValidIMEI(data []byte) bool {
	if len(data) != 15 {
		return false
	}
	for _, b := range data {
		if b < '0' || b > '9' {
			return false
		}
	}
	return true
}

func isValidIMEIString(imei string) bool {
	if len(imei) != 15 {
		return false
	}
	for _, c := range imei {
		if c < '0' || c > '9' {
			return false
		}
	}
	return true
}

func extractIMEI(data []byte) string {
	// Cherche un pattern de 15 chiffres consécutifs
	dataStr := string(data)
	for i := 0; i <= len(dataStr)-15; i++ {
		substr := dataStr[i : i+15]
		allDigits := true
		for _, c := range substr {
			if c < '0' || c > '9' {
				allDigits = false
				break
			}
		}
		if allDigits {
			return substr
		}
	}
	return ""
}

// GetDecoder retourne le décodeur approprié pour un protocole
func GetDecoder(protocolName string) Decoder {
	switch protocolName {
	case "GT06":
		return &GT06Decoder{}
	case "GT06N":
		return &GT06NDecoder{}
	case "TK102":
		return &TK102Decoder{}
	case "TK103":
		return &TK103Decoder{}
	case "303":
		return &Protocol303Decoder{}
	case "FMXXXX":
		return NewFMXXXXDecoder("FMXXXX")
	case "TELTONIKA":
		return NewFMXXXXDecoder("TELTONIKA")
	default:
		return &GenericDecoder{}
	}
}

// DetectProtocol détecte le protocole depuis les données
func DetectProtocol(data []byte) string {
	decoders := []Decoder{
		&GT06Decoder{},
		&GT06NDecoder{},
		&TK102Decoder{},
		&TK103Decoder{},
		&Protocol303Decoder{},
		&FMXXXXDecoder{},
	}

	for _, decoder := range decoders {
		if decoder.Validate(data) {
			return decoder.GetProtocolName()
		}
	}

	return "UNKNOWN"
}

// GenericDecoder pour les protocoles non reconnus
type GenericDecoder struct{}

func (d *GenericDecoder) GetProtocolName() string {
	return "UNKNOWN"
}

func (d *GenericDecoder) Validate(data []byte) bool {
	return len(data) > 0
}

func (d *GenericDecoder) Decode(data []byte) (*GPSMessage, error) {
	msg := &GPSMessage{
		Protocol:  "UNKNOWN",
		Timestamp: time.Now(),
		OtherData: make(map[string]interface{}),
		RawData:   hex.EncodeToString(data),
	}

	imei := extractIMEI(data)
	if imei != "" {
		msg.IMEI = imei
	}

	return msg, nil
}
