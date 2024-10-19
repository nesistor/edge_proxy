package proxy

import (
	"context"
	"fmt"
	"go-proxy/internal/cache"
	"io"
	"net/http"
)

// ProxyHandler - główny handler obsługujący proxy
func ProxyHandler(w http.ResponseWriter, r *http.Request) {
	// Klucz do cache na podstawie ścieżki zapytania
	cacheKey := fmt.Sprintf("proxy:%s", r.URL.Path)

	// Sprawdzanie czy odpowiedź znajduje się w cache
	cachedResponse, err := cache.RedisClient.HGetAll(cache.GetContext(), cacheKey).Result()
	if err == nil && len(cachedResponse) > 0 {
		// Jeśli znaleziono w cache, zwracamy odpowiedź z cache
		w.Header().Set("Content-Type", "application/json") // Możesz dostosować nagłówki jeśli potrzebne
		w.Write([]byte(cachedResponse["response"]))
		return
	}

	// Jeśli nie ma w cache, kontynuujemy zapytanie do serwera

	// Docelowy adres serwera (np. zmień na rzeczywisty serwer)
	targetURL := "http://httpbin.org" + r.URL.Path

	// Tworzenie nowego żądania do docelowego serwera
	req, err := http.NewRequest(r.Method, targetURL, r.Body)
	if err != nil {
		http.Error(w, "Error creating request", http.StatusInternalServerError)
		return
	}

	// Kopiowanie nagłówków z oryginalnego żądania
	for name, values := range r.Header {
		for _, value := range values {
			req.Header.Add(name, value)
		}
	}

	// Wykonanie zapytania do docelowego serwera
	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		http.Error(w, "Error sending request to target server", http.StatusInternalServerError)
		return
	}
	defer resp.Body.Close()

	// Odczytanie odpowiedzi z docelowego serwera
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		http.Error(w, "Error reading response", http.StatusInternalServerError)
		return
	}

	purpose := "empty"

	// Zapisanie żądania, odpowiedzi i przeznaczenia do Redis bez TTL (na stałe)
	err = cache.RedisClient.HSet(context.Background(), cacheKey, "request", r.URL.String(), "response", string(body), "purpose", purpose).Err()
	if err != nil {
		http.Error(w, "Error saving data to Redis", http.StatusInternalServerError)
		return
	}

	// Ustawienie nagłówków odpowiedzi
	for name, values := range resp.Header {
		for _, value := range values {
			w.Header().Add(name, value)
		}
	}
	w.WriteHeader(resp.StatusCode)
	w.Write(body)
}
