package fmxxxx

import "encoding/binary"

// ValidateFrame valide une trame FMXXXX (Login ou Data)
func ValidateFrame(data []byte) bool {
	if len(data) < 2 {
		return false
	}

	// Login packet: [Length 2B] [IMEI]
	// Data packet: [0x00000000] ...

	if len(data) >= 8 && binary.BigEndian.Uint32(data[0:4]) == 0 {
		return true // Data
	}

	// Si ce n'est pas des données, on vérifie si c'est un login IMEI
	imeiLength := int(binary.BigEndian.Uint16(data[0:2]))
	return imeiLength > 0 && imeiLength <= 15 && len(data) >= 2+imeiLength
}
