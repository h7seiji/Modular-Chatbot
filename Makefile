# Makefile for Modular Chatbot Docker operations

.PHONY: help build up down logs clean dev prod test health deploy deploy-no-pf undeploy pf k8s-status k8s-logs cloudrun-deploy cloudrun-undeploy cloudrun-logs cloudrun-status

# Detect operating system
ifeq ($(OS),Windows_NT)
    SHELL_CMD := powershell
    SCRIPT_EXT := ps1
    SHELL_FLAG := -File
    ifeq ($(shell echo %PROCESSOR_ARCHITECTURE%),AMD64)
        ARCH := x64
    endif
    ifeq ($(shell echo %PROCESSOR_ARCHITECTURE%),x86)
        ARCH := x86
    endif
else
    UNAME_S := $(shell uname -s)
    ifeq ($(UNAME_S),Linux)
        SHELL_CMD := bash
        SCRIPT_EXT := sh
        SHELL_FLAG :=
        ARCH := $(shell uname -m)
    endif
    ifeq ($(UNAME_S),Darwin)
        SHELL_CMD := bash
        SCRIPT_EXT := sh
        SHELL_FLAG :=
        ARCH := $(shell uname -m)
    endif
endif

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
	@echo ""
	@echo "Kubernetes commands:"
	@echo "  deploy    - Deploy to Kubernetes with automatic port forwarding"
	@echo "  deploy-no-pf - Deploy to Kubernetes without port forwarding"
	@echo "  undeploy  - Remove Kubernetes deployment"
	@echo "  pf        - Start port forwarding only"
	@echo "  k8s-status- Check Kubernetes deployment status"
	@echo "  k8s-logs  - Show Kubernetes pod logs"
	@echo ""
	@echo "Cloud Run commands:"
	@echo "  cloudrun-deploy - Deploy to Google Cloud Run"
	@echo "  cloudrun-undeploy - Remove Cloud Run deployment"
	@echo "  cloudrun-status - Check Cloud Run service status"
	@echo "  cloudrun-logs - Show Cloud Run service logs"

# Build all images
build:
	docker-compose build
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
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec backend uv run pytest

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

# Kubernetes deployment with automatic port forwarding
deploy:
	@echo "Deploying to Kubernetes with automatic port forwarding..."
	cd k8s && $(SHELL_CMD) $(SHELL_FLAG) deploy.$(SCRIPT_EXT)

# Kubernetes deployment without port forwarding
deploy-no-pf:
	@echo "Deploying to Kubernetes without port forwarding..."
ifeq ($(SHELL_CMD),powershell)
	cd k8s && $(SHELL_CMD) $(SHELL_FLAG) deploy.$(SCRIPT_EXT) -NoPortForward
else
	cd k8s && $(SHELL_CMD) $(SHELL_FLAG) deploy.$(SCRIPT_EXT) --no-port-forward
endif

# Remove Kubernetes deployment
undeploy:
	@echo "Removing Kubernetes deployment..."
	cd k8s && $(SHELL_CMD) $(SHELL_FLAG) undeploy.$(SCRIPT_EXT)

# Start port forwarding only
pf:
	@echo "Starting port forwarding..."
	cd k8s && $(SHELL_CMD) $(SHELL_FLAG) port-forward.$(SCRIPT_EXT)

# Check Kubernetes deployment status
k8s-status:
	@echo "Checking Kubernetes deployment status..."
	cd k8s && $(SHELL_CMD) $(SHELL_FLAG) check-deployment.$(SCRIPT_EXT)

# Show Kubernetes pod logs
k8s-logs:
	@echo "Showing Kubernetes pod logs..."
ifeq ($(SHELL_CMD),powershell)
	cd k8s && $(SHELL_CMD) -Command "kubectl get pods -n modular-chatbot -o name | ForEach-Object { kubectl logs -f $$_ -n modular-chatbot }"
else
	cd k8s && $(SHELL_CMD) -c "kubectl get pods -n modular-chatbot -o name | xargs -I {} kubectl logs -f {} -n modular-chatbot"
endif

# Deploy to Google Cloud Run
cloudrun-deploy:
	@echo "Deploying to Google Cloud Run..."
	$(SHELL_CMD) $(SHELL_FLAG) deploy-cloudrun.$(SCRIPT_EXT)

# Remove Cloud Run deployment
cloudrun-undeploy:
	@echo "Removing Cloud Run deployment..."
	$(SHELL_CMD) $(SHELL_FLAG) undeploy-cloudrun.$(SCRIPT_EXT)

# Check Cloud Run service status
cloudrun-status:
	@echo "Checking Cloud Run service status..."
	ifeq ($(SHELL_CMD),powershell)
		$(SHELL_CMD) -Command "gcloud run services list --project=$$(gcloud config get-value project)"
	else
		$(SHELL_CMD) -c "gcloud run services list --project=$$(gcloud config get-value project)"
	endif

# Show Cloud Run service logs
cloudrun-logs:
	@echo "Showing Cloud Run service logs..."
	ifeq ($(SHELL_CMD),powershell)
		$(SHELL_CMD) -Command "gcloud logging tail 'resource.type=cloud_run_revision' --project=$$(gcloud config get-value project)"
	else
		$(SHELL_CMD) -c "gcloud logging tail 'resource.type=cloud_run_revision' --project=$$(gcloud config get-value project)"
	endif