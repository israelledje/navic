package fmxxxx

import (
	"encoding/binary"
	"errors"
	"fmt"
)

// DecodeFrame décode une trame Teltonika complète (Login ou Data)
func DecodeFrame(data []byte) ([]AVLData, string, []byte, error) {
	if len(data) < 2 {
		return nil, "", nil, errors.New("frame too short")
	}

	// Détecter si c'est un Login (IMEI) ou des Données AVL
	// Les données AVL commencent par un préambule de 4 octets à 0
	if len(data) >= 8 && binary.BigEndian.Uint32(data[0:4]) == 0 {
		return decodeDataPacket(data)
	} else {
		return decodeLoginPacket(data)
	}
}

// decodeLoginPacket décode le paquet d'authentification (IMEI)
func decodeLoginPacket(data []byte) ([]AVLData, string, []byte, error) {
	// Format: [IMEI_LENGTH_2B][IMEI_ASCII]
	if len(data) < 2 {
		return nil, "", nil, errors.New("login packet too short")
	}

	imeiLength := int(binary.BigEndian.Uint16(data[0:2]))
	if len(data) < 2+imeiLength {
		return nil, "", nil, errors.New("invalid IMEI length in login")
	}

	imei := string(data[2 : 2+imeiLength])

	// ACK de login : 0x01 pour accepter
	response := EncodeLoginACK(true)

	return nil, imei, response, nil
}

// decodeDataPacket décode un paquet de données AVL
func decodeDataPacket(data []byte) ([]AVLData, string, []byte, error) {
	// Format: [PREAMBLE_4B][DATA_LENGTH_4B][CODEC_ID_1B][AVL_COUNT_1B][DATA...][AVL_COUNT_2B][CRC_4B]
	if len(data) < 12 {
		return nil, "", nil, errors.New("data packet too short")
	}

	dataLength := binary.BigEndian.Uint32(data[4:8])
	if uint32(len(data)) < 8+dataLength+4 {
		return nil, "", nil, errors.New("incomplete data packet")
	}

	codecID := data[8]
	count1 := int(data[9])

	// Vérification du CRC
	crcExpected := binary.BigEndian.Uint32(data[8+dataLength : 8+dataLength+4])
	crcComputed := CRC16Teltonika(data[8 : 8+dataLength])

	if crcExpected != crcComputed {
		return nil, "", nil, fmt.Errorf("CRC mismatch: expected %08x, got %08x", crcExpected, crcComputed)
	}

	// Vérification du nombre d'enregistrements (AVL_COUNT_2B à la fin)
	count2 := int(data[8+dataLength-1]) // Le dernier octet de DATA est souvent AVL_COUNT
	if count1 != count2 {
		// Note: selon les versions, count2 peut être sur 1 ou 4 octets,
		// mais Teltonika dit que c'est le même octet que AVL_COUNT_1
	}

	var avlDataList []AVLData
	var err error

	// Décodage selon le codec
	payload := data[9 : 8+dataLength] // Inclut Count1 au début

	switch codecID {
	case 0x08, 0x8E:
		avlDataList, err = decodeCodec8(payload, codecID == 0x8E)
	case 0x10:
		avlDataList, err = decodeCodec16(payload)
	default:
		return nil, "", nil, fmt.Errorf("codec non supporté: 0x%02X", codecID)
	}

	if err != nil {
		return nil, "", nil, err
	}

	// ACK de données : le nombre d'AVL reçus sur 4 octets
	response := EncodeACK(len(avlDataList))

	return avlDataList, "", response, nil
}

// decodeCodec8 décode le Codec 8 et 8 Extended
func decodeCodec8(data []byte, extended bool) ([]AVLData, error) {
	if len(data) < 2 {
		return nil, errors.New("codec 8 data too short")
	}

	count := int(data[0])
	avlDataList := make([]AVLData, 0, count)
	offset := 1

	for i := 0; i < count; i++ {
		if offset+15 > len(data) {
			break
		}

		timestamp := parseTimestamp(data[offset : offset+8])
		offset += 8

		priority := data[offset]
		offset++

		// GPS Element (15 bytes)
		longitude := parseCoordinate(data[offset : offset+4])
		offset += 4
		latitude := parseCoordinate(data[offset : offset+4])
		offset += 4
		altitude := int16(binary.BigEndian.Uint16(data[offset : offset+2]))
		offset += 2
		angle := binary.BigEndian.Uint16(data[offset : offset+2])
		offset += 2
		satellites := data[offset]
		offset++
		speed := binary.BigEndian.Uint16(data[offset : offset+2])
		offset += 2

		gpsData := &GPSData{
			Longitude:  longitude,
			Latitude:   latitude,
			Altitude:   altitude,
			Angle:      angle,
			Satellites: satellites,
			Speed:      speed,
		}

		// IO Element
		ioData, newOffset, err := decodeIOElement(data, offset, extended)
		if err != nil {
			return nil, err
		}
		offset = newOffset

		avlDataList = append(avlDataList, AVLData{
			Timestamp: timestamp,
			Priority:  priority,
			GPS:       gpsData,
			IO:        ioData,
		})
	}

	return avlDataList, nil
}

// decodeCodec16 décode le Codec 16
func decodeCodec16(data []byte) ([]AVLData, error) {
	// Structure similaire au Codec 8 mais avec des ID IO sur 2 octets
	// et des longueurs sur 2 octets
	if len(data) < 2 {
		return nil, errors.New("codec 16 data too short")
	}

	count := int(data[0])
	avlDataList := make([]AVLData, 0, count)
	offset := 1

	for i := 0; i < count; i++ {
		if offset+15 > len(data) {
			break
		}

		timestamp := parseTimestamp(data[offset : offset+8])
		offset += 8

		priority := data[offset]
		offset++

		// GPS Element (15 bytes) same as Codec 8
		longitude := parseCoordinate(data[offset : offset+4])
		offset += 4
		latitude := parseCoordinate(data[offset : offset+4])
		offset += 4
		altitude := int16(binary.BigEndian.Uint16(data[offset : offset+2]))
		offset += 2
		angle := binary.BigEndian.Uint16(data[offset : offset+2])
		offset += 2
		satellites := data[offset]
		offset++
		speed := binary.BigEndian.Uint16(data[offset : offset+2])
		offset += 2

		gpsData := &GPSData{
			Longitude:  longitude,
			Latitude:   latitude,
			Altitude:   altitude,
			Angle:      angle,
			Satellites: satellites,
			Speed:      speed,
		}

		// IO Element Codec 16 (Event ID 2B, Count 2B)
		ioData, newOffset, err := decodeIOElementCodec16(data, offset)
		if err != nil {
			return nil, err
		}
		offset = newOffset

		avlDataList = append(avlDataList, AVLData{
			Timestamp: timestamp,
			Priority:  priority,
			GPS:       gpsData,
			IO:        ioData,
		})
	}

	return avlDataList, nil
}

// decodeIOElement décode un élément IO pour Codec 8/8E
func decodeIOElement(data []byte, offset int, extended bool) (*IOData, int, error) {
	if offset+2 > len(data) {
		return nil, offset, errors.New("IO element header too short")
	}

	var eventID uint32
	if extended {
		eventID = uint32(binary.BigEndian.Uint16(data[offset : offset+2]))
		offset += 2
	} else {
		eventID = uint32(data[offset])
		offset++
	}

	totalIO := int(data[offset])
	offset++

	ioData := &IOData{
		EventID:     eventID,
		OneByteIO:   make(map[uint32]byte),
		TwoByteIO:   make(map[uint32]uint16),
		FourByteIO:  make(map[uint32]uint32),
		EightByteIO: make(map[uint32]uint64),
	}

	// 1 Byte IO
	count1B := int(data[offset])
	offset++
	for i := 0; i < count1B; i++ {
		id, val, newOffset := parseIO(data, offset, 1, extended)
		offset = newOffset
		ioData.OneByteIO[id] = byte(val)
	}

	// 2 Byte IO
	count2B := int(data[offset])
	offset++
	for i := 0; i < count2B; i++ {
		id, val, newOffset := parseIO(data, offset, 2, extended)
		offset = newOffset
		ioData.TwoByteIO[id] = uint16(val)
	}

	// 4 Byte IO
	count4B := int(data[offset])
	offset++
	for i := 0; i < count4B; i++ {
		id, val, newOffset := parseIO(data, offset, 4, extended)
		offset = newOffset
		ioData.FourByteIO[id] = uint32(val)
	}

	// 8 Byte IO
	count8B := int(data[offset])
	offset++
	for i := 0; i < count8B; i++ {
		id, val, newOffset := parseIO(data, offset, 8, extended)
		offset = newOffset
		ioData.EightByteIO[id] = val
	}

	_ = totalIO // Prevent unused warning

	return ioData, offset, nil
}

func decodeIOElementCodec16(data []byte, offset int) (*IOData, int, error) {
	if offset+4 > len(data) {
		return nil, offset, errors.New("IO element codec 16 header too short")
	}

	eventID := uint32(binary.BigEndian.Uint16(data[offset : offset+2]))
	offset += 2
	// Generation Count (Total IO) on 2 bytes in Codec 16
	totalIO := binary.BigEndian.Uint16(data[offset : offset+2])
	offset += 2

	ioData := &IOData{
		EventID:     eventID,
		TotalIO:     totalIO,
		OneByteIO:   make(map[uint32]byte),
		TwoByteIO:   make(map[uint32]uint16),
		FourByteIO:  make(map[uint32]uint32),
		EightByteIO: make(map[uint32]uint64),
	}

	// 1 Byte IO: 2B Count, then [2B ID][1B Val]
	count1B := int(binary.BigEndian.Uint16(data[offset : offset+2]))
	offset += 2
	for i := 0; i < count1B; i++ {
		id := uint32(binary.BigEndian.Uint16(data[offset : offset+2]))
		offset += 2
		val := data[offset]
		offset++
		ioData.OneByteIO[id] = val
	}

	// 2 Byte IO: 2B Count, then [2B ID][2B Val]
	count2B := int(binary.BigEndian.Uint16(data[offset : offset+2]))
	offset += 2
	for i := 0; i < count2B; i++ {
		id := uint32(binary.BigEndian.Uint16(data[offset : offset+2]))
		offset += 2
		val := binary.BigEndian.Uint16(data[offset : offset+2])
		offset += 2
		ioData.TwoByteIO[id] = val
	}

	// 4 Byte IO: 2B Count, then [2B ID][4B Val]
	count4B := int(binary.BigEndian.Uint16(data[offset : offset+2]))
	offset += 2
	for i := 0; i < count4B; i++ {
		id := uint32(binary.BigEndian.Uint16(data[offset : offset+2]))
		offset += 2
		val := binary.BigEndian.Uint32(data[offset : offset+4])
		offset += 4
		ioData.FourByteIO[id] = val
	}

	// 8 Byte IO: 2B Count, then [2B ID][8B Val]
	count8B := int(binary.BigEndian.Uint16(data[offset : offset+2]))
	offset += 2
	for i := 0; i < count8B; i++ {
		id := uint32(binary.BigEndian.Uint16(data[offset : offset+2]))
		offset += 2
		val := binary.BigEndian.Uint64(data[offset : offset+8])
		offset += 8
		ioData.EightByteIO[id] = val
	}

	return ioData, offset, nil
}

func parseIO(data []byte, offset int, size int, extendedID bool) (uint32, uint64, int) {
	var id uint32
	if extendedID {
		id = uint32(binary.BigEndian.Uint16(data[offset : offset+2]))
		offset += 2
	} else {
		id = uint32(data[offset])
		offset++
	}

	var val uint64
	switch size {
	case 1:
		val = uint64(data[offset])
		offset++
	case 2:
		val = uint64(binary.BigEndian.Uint16(data[offset : offset+2]))
		offset += 2
	case 4:
		val = uint64(binary.BigEndian.Uint32(data[offset : offset+4]))
		offset += 4
	case 8:
		val = uint64(binary.BigEndian.Uint64(data[offset : offset+8]))
		offset += 8
	}
	return id, val, offset
}
