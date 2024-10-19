package proxy

import (
	"fmt"
	"go-proxy/internal/cache"
	"io"
	"net/http"
	"time"
)

// ProxyHandler - główny handler obsługujący proxy
func ProxyHandler(w http.ResponseWriter, r *http.Request) {
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

	// Zapisanie żądania i odpowiedzi do Redis z czasem wygaśnięcia
	cacheKey := fmt.Sprintf("proxy:%s:%d", r.URL.Path, time.Now().Unix())
	err = cache.RedisClient.HSet(cache.GetContext(), cacheKey, "request", r.URL.String(), "response", string(body)).Err()
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
