package gt06

// AlarmName retourne le nom de l'alarme selon son code (bits 12-15 du status)
func AlarmName(code byte) string {
	alarmMap := map[byte]string{
		0x00: "Normal",
		0x01: "SOS",
		0x02: "Power Cut",
		0x03: "Vibration",
		0x04: "Fence In",
		0x05: "Fence Out",
		0x06: "Over Speed",
		0x07: "Low Battery",
		0x08: "Power On",
		0x09: "Door",
		0x0A: "GPS First Fix",
		0x0B: "GPS Antenna Cut",
		0x0C: "Pseudo Base Station",
		0x0D: "Jamming",
		0x0E: "Accident",
		0x0F: "Other",
	}

	if name, ok := alarmMap[code]; ok {
		return name
	}
	return "UNKNOWN"
}