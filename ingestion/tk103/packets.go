package tk103

import (
	"encoding/binary"
)

// LOGIN (0x01)
func DecodeLogin(p *Packet) string {
	if len(p.Payload) < 8 {
		return ""
	}

	imeiBytes := p.Payload[:8]
	imei := ""

	// Les 8 premiers bytes contiennent l'IMEI en BCD
	// Un IMEI fait 15 chiffres, donc on prend 8 bytes (16 chiffres BCD) et on ignore le dernier
	for i, b := range imeiBytes {
		imei += string('0' + (b >> 4))
		// Pour le dernier byte, on ne prend que le premier chiffre (15ème chiffre de l'IMEI)
		if i < 7 {
			imei += string('0' + (b & 0x0F))
		}
		// Le dernier chiffre (16ème) est ignoré car l'IMEI fait 15 chiffres
	}

	// S'assurer que l'IMEI fait exactement 15 caractères
	if len(imei) > 15 {
		imei = imei[:15]
	}

	return imei
}

// GPS (0x12 / 0x1A)
func DecodeGPS(p *Packet) DeviceEvent {
	// 0x12: Time(6) + Q(1) + Lat(4) + Lon(4) + Speed(1) + CourseStatus(2) = 18 bytes
	if len(p.Payload) < 18 {
		return DeviceEvent{}
	}

	t := parseTime(p.Payload[0:6])
	// Byte 6 is Quantity of satellites
	lat := parseCoord(p.Payload[7:11])
	lon := parseCoord(p.Payload[11:15])
	speed := int(p.Payload[15])

	// Course/Status: 2 bytes
	// Bit 15: Differential / GPS Real-time
	// Bit 14: GPS positioning (1=positioned, 0=not)
	// Bit 13: 1=West Lon, 0=East Lon
	// Bit 12: 1=South Lat, 0=North Lat
	// Bits 0-11: Heading/Course
	courseStatus := binary.BigEndian.Uint16(p.Payload[16:18])

	valid := (courseStatus & 0x4000) != 0
	isWest := (courseStatus & 0x2000) != 0
	isSouth := (courseStatus & 0x1000) != 0
	heading := int(courseStatus & 0x03FF) // usually 10 bits for course 0-1023? or 12 bits?

	if isSouth {
		lat = -lat
	}
	if isWest {
		lon = -lon
	}

	return DeviceEvent{
		Time:        t,
		Latitude:    &lat,
		Longitude:   &lon,
		Speed:       &speed,
		Heading:     &heading,
		GPSValid:    valid,
		RawProtocol: p.Protocol,
	}
}

// ALARM (0x26)
func DecodeAlarm(p *Packet) DeviceEvent {
	if len(p.Payload) < 7 {
		return DeviceEvent{}
	}

	code := p.Payload[0]
	t := parseTime(p.Payload[1:7])
	name := AlarmName(code)

	return DeviceEvent{
		Time:        t,
		AlarmCode:   &code,
		AlarmName:   &name,
		RawProtocol: p.Protocol,
	}
}
