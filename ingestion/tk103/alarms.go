package tk103

// AlarmName retourne le nom de l'alarme selon son code
func AlarmName(code byte) string {
	alarmMap := map[byte]string{
		0x01: "SOS",
		0x02: "Power Cut",
		0x03: "Shock",
		0x04: "GeoFence",
		0x05: "OverSpeed",
		0x06: "Low Battery",
		0x09: "Power On",
		0x10: "GPRS Connect",
		0x11: "Door Alarm",
		0x12: "GPS First Fix",
		0x13: "GPS Antenna Cut",
		0x15: "Jamming",
		0x16: "Accident",
		0x17: "Fatigue Driving",
		0x18: "Sharp Turn",
		0x19: "Sharp Acceleration",
		0x1A: "Sharp Deceleration",
		0x1B: "Idle",
	}

	if name, ok := alarmMap[code]; ok {
		return name
	}
	return "UNKNOWN"
}
