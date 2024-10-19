package config

import (
	"os"
)

// Config struktura dla konfiguracji aplikacji
type Config struct {
	RedisAddr  string
	ServerPort string
}

// LoadConfig wczytuje konfigurację z plików środowiskowych lub domyślną
func LoadConfig() Config {
	redisAddr := os.Getenv("REDIS_ADDR")
	if redisAddr == "" {
		redisAddr = "localhost:6379" // Domyślny adres Redis
	}

	serverPort := os.Getenv("SERVER_PORT")
	if serverPort == "" {
		serverPort = "8080" // Domyślny port serwera
	}

	return Config{
		RedisAddr:  redisAddr,
		ServerPort: serverPort,
	}
}
