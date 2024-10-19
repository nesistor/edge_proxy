package cache

import (
	"context"
	"github.com/go-redis/redis/v8"
	"log"
)

var (
	ctx = context.Background()

	RedisClient *redis.Client
)

// InitRedis inicjalizuje po\u0142\u0105czenie z Redis
func InitRedis(addr string) {
	RedisClient = redis.NewClient(&redis.Options{
		Addr: addr,
	})

	_, err := RedisClient.Ping(ctx).Result()
	if err != nil {
		log.Fatalf("Could not connect to Redis: %v", err)
	}
}

// GetContext zwraca globalny kontekst
func GetContext() context.Context {
	return ctx
}
