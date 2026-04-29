package gt06

import "time"

// Packet représente un paquet GT06 décodé
type Packet struct {
	Protocol byte
	Length   byte
	Payload  []byte
	Serial   uint16
}

// DeviceEvent représente un événement décodé depuis un paquet GT06
type DeviceEvent struct {
	IMEI        string
	Time        time.Time
	Latitude    *float64
	Longitude   *float64
	Speed       *float64 // en km/h
	Heading     *float64 // en degrés
	GPSValid    bool
	Altitude    *float64
	Satellites  *int
	Battery     *int
	Signal      *int
	AlarmCode   *byte
	AlarmName   *string
	Status      *uint32
	RawProtocol byte
}
