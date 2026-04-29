package main

import (
	"os"
	"strconv"
)

// ProtocolConfig définit la configuration pour un protocole
type ProtocolConfig struct {
	Name          string
	TCPPort       string
	UDPPort       string
	MaxPacketSize int
	ReadTimeout   int // en secondes
	WriteTimeout  int // en secondes
	Enabled       bool
}

// SecurityConfig définit les paramètres de sécurité
type SecurityConfig struct {
	RateLimitPerIP      int // nombre de requêtes par minute par IP
	RateLimitPerIMEI    int // nombre de requêtes par minute par IMEI
	MaxConnections      int // nombre max de connexions simultanées
	MaxPacketSize       int // taille max d'un paquet en bytes
	EnableIMEIWhitelist bool
	BlockDuration       int // durée de blocage en secondes après dépassement de limite
}

// Config contient toute la configuration
type Config struct {
	DjangoURL string
	APIKey    string
	Protocols map[string]ProtocolConfig
	Security  SecurityConfig
	LogLevel  string
	LogFile   string
}

// LoadConfig charge la configuration depuis les variables d'environnement ou utilise les valeurs par défaut
func LoadConfig() *Config {
	config := &Config{
		DjangoURL: getEnv("DJANGO_URL", "http://localhost:8000/api/tracking/ingest/"),
		APIKey:    getEnv("INGESTION_API_KEY", "navic-secret-ingestion-key-2026"),
		LogLevel:  getEnv("LOG_LEVEL", "INFO"),
		LogFile:   getEnv("LOG_FILE", ""),
		Protocols: make(map[string]ProtocolConfig),
		Security: SecurityConfig{
			RateLimitPerIP:      getEnvInt("RATE_LIMIT_PER_IP", 100),
			RateLimitPerIMEI:    getEnvInt("RATE_LIMIT_PER_IMEI", 200),
			MaxConnections:      getEnvInt("MAX_CONNECTIONS", 1000),
			MaxPacketSize:       getEnvInt("MAX_PACKET_SIZE", 4096),
			EnableIMEIWhitelist: getEnvBool("ENABLE_IMEI_WHITELIST", true),
			BlockDuration:       getEnvInt("BLOCK_DURATION", 300), // 5 minutes
		},
	}

	// Configuration des protocoles avec ports dédiés
	config.Protocols["GT06"] = ProtocolConfig{
		Name:          "GT06",
		TCPPort:       getEnv("GT06_TCP_PORT", "5027"),
		UDPPort:       getEnv("GT06_UDP_PORT", "5028"),
		MaxPacketSize: 1024,
		ReadTimeout:   30,
		WriteTimeout:  10,
		Enabled:       getEnvBool("GT06_ENABLED", true),
	}

	config.Protocols["GT06N"] = ProtocolConfig{
		Name:          "GT06N",
		TCPPort:       getEnv("GT06N_TCP_PORT", "5029"),
		UDPPort:       getEnv("GT06N_UDP_PORT", "5030"),
		MaxPacketSize: 1024,
		ReadTimeout:   30,
		WriteTimeout:  10,
		Enabled:       getEnvBool("GT06N_ENABLED", true),
	}

	config.Protocols["TK102"] = ProtocolConfig{
		Name:          "TK102",
		TCPPort:       getEnv("TK102_TCP_PORT", "5031"),
		UDPPort:       getEnv("TK102_UDP_PORT", "5032"),
		MaxPacketSize: 512,
		ReadTimeout:   30,
		WriteTimeout:  10,
		Enabled:       getEnvBool("TK102_ENABLED", true),
	}

	config.Protocols["TK103"] = ProtocolConfig{
		Name:          "TK103",
		TCPPort:       getEnv("TK103_TCP_PORT", "5033"),
		UDPPort:       getEnv("TK103_UDP_PORT", "5034"),
		MaxPacketSize: 512,
		ReadTimeout:   30,
		WriteTimeout:  10,
		Enabled:       getEnvBool("TK103_ENABLED", true),
	}

	config.Protocols["303"] = ProtocolConfig{
		Name:          "303",
		TCPPort:       getEnv("303_TCP_PORT", "5035"),
		UDPPort:       getEnv("303_UDP_PORT", "5036"),
		MaxPacketSize: 1024,
		ReadTimeout:   30,
		WriteTimeout:  10,
		Enabled:       getEnvBool("303_ENABLED", true),
	}

	config.Protocols["FMXXXX"] = ProtocolConfig{
		Name:          "FMXXXX",
		TCPPort:       getEnv("FMXXXX_TCP_PORT", "5039"),
		UDPPort:       getEnv("FMXXXX_UDP_PORT", "5040"),
		MaxPacketSize: 2048,
		ReadTimeout:   60,
		WriteTimeout:  10,
		Enabled:       getEnvBool("FMXXXX_ENABLED", true),
	}

	return config
}

// Fonctions utilitaires pour lire les variables d'environnement
func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func getEnvInt(key string, defaultValue int) int {
	if value := os.Getenv(key); value != "" {
		if intValue, err := strconv.Atoi(value); err == nil {
			return intValue
		}
	}
	return defaultValue
}

func getEnvBool(key string, defaultValue bool) bool {
	if value := os.Getenv(key); value != "" {
		if boolValue, err := strconv.ParseBool(value); err == nil {
			return boolValue
		}
	}
	return defaultValue
}
