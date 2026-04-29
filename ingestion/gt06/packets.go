package gt06

import "encoding/binary"

// DecodeLogin décode un paquet de login (0x01)
func DecodeLogin(p *Packet) string {
	if len(p.Payload) < 8 {
		return ""
	}

	// IMEI en BCD (8 bytes = 16 chiffres, on prend les 15 premiers)
	imeiBytes := p.Payload[:8]
	imei := ""

	for i, b := range imeiBytes {
		imei += string('0' + (b >> 4))
		if i < 7 {
			imei += string('0' + (b & 0x0F))
		}
	}

	if len(imei) > 15 {
		imei = imei[:15]
	}

	return imei
}

// DecodeGPS décode un paquet GPS (0x12)
func DecodeGPS(p *Packet) DeviceEvent {
	// Format: Time(6) + Q(1) + Lat(4) + Lon(4) + Speed(1) + CourseStatus(2) = 18 bytes minimum
	if len(p.Payload) < 18 {
		return DeviceEvent{}
	}

	// Date/Time (6 bytes)
	t := parseTime(p.Payload[0:6])

	// Skip Quantity of satellites (byte 6)

	// Latitude (7-10)
	lat := parseLatitude(p.Payload[7:11])
	// Longitude (11-14)
	lon := parseLongitude(p.Payload[11:15])
	// Speed (15)
	speedRaw := parseSpeed(p.Payload[15])

	// Course/Status (16-17)
	heading, isNorth, isEast, isFixed := parseHeading(p.Payload[16:18])

	if !isNorth {
		lat = -lat
	}
	if !isEast {
		lon = -lon
	}

	// Status Information (MCC/MNC/LAC/CI follow)
	var finalBattery *int
	var finalSignal *int
	var finalStatus *uint32

	// Si on a des données de batterie/signal après
	statusOffset := 18 + 8 // MCC(2)+MNC(1)+LAC(2)+CI(3) = 8 bytes?
	if len(p.Payload) >= statusOffset+4 {
		status := binary.BigEndian.Uint32(p.Payload[statusOffset : statusOffset+4])
		battery := int((status>>4)&0x0F) * 10
		signal := int((status>>8)&0x0F) * 10
		finalBattery = &battery
		finalSignal = &signal
		finalStatus = &status
	}

	speedFloat := float64(speedRaw)
	headingFloat := float64(heading)

	return DeviceEvent{
		Time:        t,
		Latitude:    &lat,
		Longitude:   &lon,
		Speed:       &speedFloat,
		Heading:     &headingFloat,
		GPSValid:    isFixed,
		Battery:     finalBattery,
		Signal:      finalSignal,
		Status:      finalStatus,
		RawProtocol: p.Protocol,
	}
}

// DecodeAlarm décode un paquet d'alarme (0x16)
func DecodeAlarm(p *Packet) DeviceEvent {
	// Les paquets d'alarme ont une structure similaire aux paquets GPS
	// mais avec des flags d'alarme dans le status
	event := DecodeGPS(p)

	// Extraire le code d'alarme depuis le status
	if event.Status != nil {
		alarmCode := byte((*event.Status >> 12) & 0x0F)
		alarmName := AlarmName(alarmCode)
		event.AlarmCode = &alarmCode
		event.AlarmName = &alarmName
	}

	return event
}

// DecodeStatus décode un paquet de status (0x13)
func DecodeStatus(p *Packet) DeviceEvent {
	if len(p.Payload) < 4 {
		return DeviceEvent{}
	}

	status := binary.BigEndian.Uint32(p.Payload[0:4])
	battery := int((status>>4)&0x0F) * 10
	signal := int((status>>8)&0x0F) * 10

	return DeviceEvent{
		Status:      &status,
		Battery:     &battery,
		Signal:      &signal,
		RawProtocol: p.Protocol,
	}
}
