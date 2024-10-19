## up: starts all containers in the background without forcing build
up:
	@echo "Starting Docker images..."
	docker-compose up -d
	@echo "Docker images started!"

## up_build: stops docker-compose, builds all projects and starts docker compose
up_build: 
	@echo "Stopping docker images"
	docker-compose down
	@echo "Building and starting docker images..."
	docker-compose up --build -d
	@echo "Docker images built and started!"

## down: stop docker compose
down:
	@echo "Stopping docker compose..."
	docker-compose down
	@echo "Done!"

## restart: restarts the Docker containers
restart: down up
	@echo "Docker containers restarted!"

## logs: show logs for the proxy service
logs:
	@echo "Showing logs for proxy server..."
	docker-compose logs -f proxy_server

build_go_proxy:
	@echo "Building go-proxy binary..."
	cd ../go-proxy && env GOOS=linux CGO_ENABLED=0 go build -o edgeProxy ./cmd/proxy
	@echo "Done!"

## build: manually builds the Docker image
build_llama_service:
	
