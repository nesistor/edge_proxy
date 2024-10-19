package main

import (
	"go-proxy/internal/cache"
	"go-proxy/internal/proxy"
	"go-proxy/pkg/config"
	"log"
	"net/http"
)

func main() {
	// Wczytanie konfiguracji
	cfg := config.LoadConfig()

	// Inicjalizacja połączenia z Redis
	cache.InitRedis(cfg.RedisAddr)

	// Uruchomienie serwera proxy
	http.HandleFunc("/", proxy.ProxyHandler)
	log.Printf("Proxy server running on port %s", cfg.ServerPort)
	log.Fatal(http.ListenAndServe(":"+cfg.ServerPort, nil))
}
