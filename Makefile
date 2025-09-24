# Makefile for Modular Chatbot Docker operations

.PHONY: help build up down logs clean dev prod test health

# Default target
help:
	@echo "Available commands:"
	@echo "  build     - Build all Docker images"
	@echo "  up        - Start all services in production mode"
	@echo "  dev       - Start all services in development mode with hot reloading"
	@echo "  down      - Stop all services"
	@echo "  logs      - Show logs from all services"
	@echo "  clean     - Remove all containers, images, and volumes"
	@echo "  test      - Run tests in containers"
	@echo "  health    - Check health of all services"
	@echo "  backend   - Start only backend services (backend + redis)"
	@echo "  frontend  - Start only frontend service"

# Build all images
build:
	docker-compose build

# Start services in production mode
up:
	docker-compose up -d

# Start services in development mode
dev:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Stop all services
down:
	docker-compose down

# Show logs
logs:
	docker-compose logs -f

# Clean up everything
clean:
	docker-compose down -v --rmi all --remove-orphans
	docker system prune -f

# Run tests
test:
	docker-compose exec backend uv run pytest
	docker-compose exec frontend npm test -- --run

# Check service health
health:
	@echo "Checking service health..."
	@docker-compose ps
	@echo "\nBackend health:"
	@curl -f http://localhost:8000/health || echo "Backend unhealthy"
	@echo "\nFrontend health:"
	@curl -f http://localhost:3000/health || echo "Frontend unhealthy"
	@echo "\nRedis health:"
	@docker-compose exec redis redis-cli ping || echo "Redis unhealthy"

# Start only backend services
backend:
	docker-compose up -d redis backend

# Start only frontend
frontend:
	docker-compose up -d frontend

# Restart specific service
restart-%:
	docker-compose restart $*

# View logs for specific service
logs-%:
	docker-compose logs -f $*

# Execute shell in service
shell-%:
	docker-compose exec $* /bin/sh

# Install dependencies
install:
	docker-compose exec backend uv pip install --system -e .
	docker-compose exec frontend npm install