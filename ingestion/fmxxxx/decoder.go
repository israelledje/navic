package fmxxxx

import (
	"encoding/binary"
	"time"
)

// parseTimestamp décode un timestamp Unix (8 bytes)
func parseTimestamp(b []byte) time.Time {
	if len(b) < 8 {
		return time.Now()
	}
	unixTime := binary.BigEndian.Uint64(b)
	return time.Unix(int64(unixTime)/1000, 0).UTC()
}

// parseCoordinate décode une coordonnée (4 bytes, en degrés * 10000000)
func parseCoordinate(b []byte) float64 {
	if len(b) < 4 {
		return 0.0
	}
	val := int32(binary.BigEndian.Uint32(b))
	return float64(val) / 10000000.0
}
