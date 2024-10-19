package proxy

import (
	"context"
	"fmt"
	"go-proxy/internal/cache"
	"io"
	"net/http"
)

// ExecuteAndUpdateRequest...
func ExecuteAndUpdateRequest(cacheKey string) error {
	// Sprawdzenie, czy wpis w Redisie ma pole "purpose" ustawione na "refresh"
	data, err := cache.RedisClient.HGetAll(context.Background(), cacheKey).Result()
	if err != nil {
		return fmt.Errorf("error fetching data from Redis: %w", err)
	}

	// Jeżeli pole "purpose" nie jest ustawione na "refresh", nie odświeżamy
	if data["purpose"] != "refresh" {
		return nil
	}

	// Tworzenie nowego żądania do docelowego serwera
	targetURL := data["request"]                       // Zakładam, że pełne URL zapytania jest zapisane w Redisie
	req, err := http.NewRequest("GET", targetURL, nil) // Zmieniamy w zależności od typu żądania (GET/POST)
	if err != nil {
		return fmt.Errorf("error creating request: %w", err)
	}

	// Wykonanie zapytania do docelowego serwera
	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("error sending request to target server: %w", err)
	}
	defer resp.Body.Close()

	// Odczytanie odpowiedzi z docelowego serwera
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return fmt.Errorf("error reading response from server: %w", err)
	}

	// Aktualizacja danych w Redisie (response + ustawienie purpose na empty)
	err = cache.RedisClient.HMSet(context.Background(), cacheKey, map[string]interface{}{
		"response": string(body),
		"purpose":  "empty",
	}).Err()
	if err != nil {
		return fmt.Errorf("error updating Redis: %w", err)
	}

	return nil
}
