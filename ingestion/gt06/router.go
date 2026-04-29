package gt06

import (
	"encoding/binary"
	"errors"
)

// DecodeFrame décode une trame GT06 complète
func DecodeFrame(data []byte) (*Packet, error) {
	if len(data) < 10 {
		return nil, errors.New("frame too short")
	}

	// Vérifier le header (0x78 0x78 ou 0x79 0x79)
	if (data[0] != 0x78 && data[0] != 0x79) || data[1] != data[0] {
		return nil, errors.New("invalid header")
	}

	length := int(data[2])
	proto := data[3]

	// Calculer la position de fin du payload
	payloadEnd := 4 + length

	// Vérifier la longueur totale (header + length + proto + payload + serial + crc + tail)
	if len(data) < payloadEnd+6 {
		return nil, errors.New("invalid length")
	}

	payload := data[4:payloadEnd]

	// Serial number (2 bytes)
	serial := binary.BigEndian.Uint16(data[payloadEnd : payloadEnd+2])

	// CRC (2 bytes)
	crcExpected := binary.BigEndian.Uint16(data[payloadEnd+2 : payloadEnd+4])
	crcComputed := CRC16(data[2:payloadEnd+2])

	if crcExpected != crcComputed {
		return nil, errors.New("CRC mismatch")
	}

	// Stop bits (0x0D 0x0A)
	if data[payloadEnd+4] != 0x0D || data[payloadEnd+5] != 0x0A {
		return nil, errors.New("invalid tail")
	}

	return &Packet{
		Protocol: proto,
		Length:   data[2],
		Payload:  payload,
		Serial:   serial,
	}, nil
}