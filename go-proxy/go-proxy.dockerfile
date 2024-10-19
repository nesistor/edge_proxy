# Użyj oficjalnego obrazu Go jako bazowego
FROM golang:1.18-alpine AS builder

# Ustaw zmienną środowiskową do pracy z Go
ENV GO111MODULE=on

# Stwórz katalog roboczy
WORKDIR /app

# Skopiuj pliki projektu
COPY go.mod go.sum ./
RUN go mod download

COPY . .

# Zbuduj aplikację
RUN go build -o /go-proxy ./cmd/proxy

# Użyj minimalnego obrazu Alpine jako podstawy do uruchomienia aplikacji
FROM alpine:3.16

# Skopiuj zbudowaną aplikację z poprzedniego etapu
COPY --from=builder /go-proxy /go-proxy

# Ustawienie zmiennych środowiskowych (można nadpisać w docker-compose)
ENV SERVER_PORT=8080
ENV REDIS_ADDR=redis:6379

# Wystawienie portu aplikacji
EXPOSE 8080

# Uruchom aplikację
CMD ["/go-proxy"]
