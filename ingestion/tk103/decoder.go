package tk103

import (
	"encoding/binary"
	"time"
)

func bcd(b byte) int {
	return int((b>>4)*10 + (b & 0x0F))
}

func parseTime(b []byte) time.Time {
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

func parseCoord(b []byte) float64 {
	v := binary.BigEndian.Uint32(b)
	deg := v / 1000000
	min := (v % 1000000) / 10000
	sec := float64(v%10000) / 10000.0
	return float64(deg) + (float64(min)+sec)/60.0
}
