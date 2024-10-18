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

## build: manually builds the Docker image
build_llama_proxy:
	@echo "Building Docker image for proxy server..."
	docker-compose build proxy_server
	@echo "Done!"
