package tk103

import "time"

type Packet struct {
	Protocol byte
	Serial   uint16
	Payload  []byte
}

type DeviceEvent struct {
	IMEI        string
	Time        time.Time
	Latitude    *float64
	Longitude   *float64
	Speed       *int
	Heading     *int
	GPSValid    bool
	AlarmCode   *byte
	AlarmName   *string
	RawProtocol byte
}
