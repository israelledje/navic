package gt06

// CRC16 calcule le CRC-16 pour GT06
func CRC16(data []byte) uint16 {
	crc := uint16(0xFFFF)
	polynomial := uint16(0x1021)

	for _, b := range data {
		crc ^= uint16(b) << 8
		for i := 0; i < 8; i++ {
			if crc&0x8000 != 0 {
				crc = (crc << 1) ^ polynomial
			} else {
				crc <<= 1
			}
		}
	}

	return crc
}