package fmxxxx

import "encoding/binary"

// CRC16Teltonika calcule le CRC16 Teltonika (IBM/ARC poly 0xA001)
func CRC16Teltonika(data []byte) uint32 {
	var crc uint16 = 0
	for _, b := range data {
		crc ^= uint16(b)
		for i := 0; i < 8; i++ {
			if crc&1 != 0 {
				crc = (crc >> 1) ^ 0xA001
			} else {
				crc >>= 1
			}
		}
	}
	return uint32(crc)
}

// EncodeACK génère un ACK pour les données AVL Teltonika
func EncodeACK(count int) []byte {
	ack := make([]byte, 4)
	binary.BigEndian.PutUint32(ack, uint32(count))
	return ack
}

// EncodeLoginACK génère un ACK pour l'IMEI de login (0x01 = Accept, 0x00 = Reject)
func EncodeLoginACK(accept bool) []byte {
	if accept {
		return []byte{0x01}
	}
	return []byte{0x00}
}
