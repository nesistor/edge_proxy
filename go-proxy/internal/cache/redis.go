package cache

import (
	"context"
	"github.com/go-redis/redis/v8"
	"log"
)

var (
	// Zmienna ctx, kt�ra b\u0119dzie u\u017cywana w ca\u0142ej aplikacji do zarz\u0105dzania kontekstem
	ctx = context.Background()

	// RedisClient przechowuje po\u0142\u0105czenie do Redis
	RedisClient *redis.Client
)

// InitRedis inicjalizuje po\u0142\u0105czenie z Redis
func InitRedis(addr string) {
	RedisClient = redis.NewClient(&redis.Options{
		Addr: addr,
	})

	// Sprawdzenie po\u0142\u0105czenia
	_, err := RedisClient.Ping(ctx).Result()
	if err != nil {
		log.Fatalf("Could not connect to Redis: %v", err)
	}
}

// GetContext zwraca globalny kontekst
func GetContext() context.Context {
	return ctx
}
