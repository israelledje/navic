package fmxxxx

import "time"

// Packet représente un paquet FMXXXX décodé
type Packet struct {
	IMEILength byte
	IMEI       string
	CodecID    byte
	Data       []byte
}

// AVLData représente une donnée AVL (Automatic Vehicle Location)
type AVLData struct {
	Timestamp time.Time
	Priority  byte
	GPS       *GPSData
	IO        *IOData
}

// GPSData contient les informations GPS
type GPSData struct {
	Longitude  float64
	Latitude   float64
	Altitude   int16
	Angle      uint16
	Satellites byte
	Speed      uint16
}

// IOData contient les informations d'entrées/sorties
type IOData struct {
	EventID     uint32
	TotalIO     uint16
	OneByteIO   map[uint32]byte
	TwoByteIO   map[uint32]uint16
	FourByteIO  map[uint32]uint32
	EightByteIO map[uint32]uint64
}
