package tk103

import (
	"encoding/binary"
	"errors"
)

func DecodeFrame(data []byte) (*Packet, error) {
	if len(data) < 10 {
		return nil, errors.New("frame too short")
	}

	if data[0] != 0x78 || data[1] != 0x78 {
		return nil, errors.New("invalid header")
	}

	length := int(data[2])
	proto := data[3]

	payloadEnd := 3 + length
	if payloadEnd+4 > len(data) {
		return nil, errors.New("invalid length")
	}

	serial := binary.BigEndian.Uint16(data[payloadEnd-2 : payloadEnd])
	payload := data[4 : payloadEnd-2]

	crcExpected := binary.BigEndian.Uint16(data[payloadEnd : payloadEnd+2])
	crcComputed := CRCX25(data[2:payloadEnd])

	if crcExpected != crcComputed {
		return nil, errors.New("CRC mismatch")
	}

	if data[payloadEnd+2] != 0x0D || data[payloadEnd+3] != 0x0A {
		return nil, errors.New("invalid tail")
	}

	return &Packet{
		Protocol: proto,
		Serial:   serial,
		Payload:  payload,
	}, nil
}
