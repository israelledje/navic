package gt06

import (
	"encoding/binary"
	"time"
)

// bcd convertit un byte BCD en int
func bcd(b byte) int {
	return int((b>>4)*10 + (b & 0x0F))
}

// parseTime décode une date/heure GT06 (6 bytes BCD)
func parseTime(b []byte) time.Time {
	if len(b) < 6 {
		return time.Now()
	}

	return time.Date(
		2000+bcd(b[0]),
		time.Month(bcd(b[1])),
		bcd(b[2]),
		bcd(b[3]),
		bcd(b[4]),
		bcd(b[5]),
		0,
		time.UTC,
	)
}

// parseLatitude décode la latitude (4 bytes, en millième de minute * 30000?? -> factor 1800000.0)
func parseLatitude(b []byte) float64 {
	if len(b) < 4 {
		return 0.0
	}
	val := binary.BigEndian.Uint32(b)
	return float64(val) / 1800000.0
}

// parseLongitude décode la longitude (4 bytes, factor 1800000.0)
func parseLongitude(b []byte) float64 {
	if len(b) < 4 {
		return 0.0
	}
	val := binary.BigEndian.Uint32(b)
	return float64(val) / 1800000.0
}

// parseSpeed décode la vitesse (1 byte, en km/h)
func parseSpeed(b byte) float64 {
	return float64(b)
}

// parseHeading décode le cap et le statut (2 bytes)
func parseHeading(b []byte) (float64, bool, bool, bool) {
	if len(b) < 2 {
		return 0.0, false, false, false
	}
	val := binary.BigEndian.Uint16(b)

	// Bits 0-9: Heading
	heading := float64(val & 0x03FF)
	// Bit 12: Longitude (1: East, 0: West)
	isEast := (val & 0x0800) != 0
	// Bit 13: Latitude (1: North, 0: South)
	isNorth := (val & 0x1000) != 0
	// Bit 10: GPS fixed? or Bit 11?
	// Concox: Bit 11 is 1: Fixed, 0: Not fixed
	isFixed := (val & 0x0400) != 0

	return heading, isNorth, isEast, isFixed
}
