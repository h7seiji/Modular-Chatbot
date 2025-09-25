#!/bin/bash

# Kubernetes deployment script for Modular Chatbot
# This script deploys the entire application stack to Kubernetes

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="modular-chatbot"
KUBECTL_TIMEOUT="300s"
NO_PORT_FORWARD=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-port-forward)
            NO_PORT_FORWARD=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--no-port-forward]"
            echo "  --no-port-forward    Skip automatic port forwarding"
            echo "  -h, --help          Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if kubectl is available
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    # Check if we can connect to the cluster
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    print_status "kubectl is available and connected to cluster"
}

# Function to check if required images exist
check_images() {
    print_status "Checking if Docker images exist..."
    
    # Note: In a real deployment, you would check if images exist in your registry
    print_warning "Make sure the following images are built and pushed to your registry:"
    print_warning "  - modular-chatbot-backend:latest"
    print_warning "  - modular-chatbot-frontend:latest"
    
    read -p "Have you built and pushed the images? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Please build and push the images first"
        exit 1
    fi
}

# Function to create secrets from .env file
create_secrets_from_env() {
    print_status "Creating secrets from .env file..."
    
    # Check if .env file exists
    if [[ ! -f "../.env" ]]; then
        print_error ".env file not found in the project root"
        echo "Please create a .env file from .env.example with your actual values"
        exit 1
    fi
    
    # Check if .env file has content
    if [[ ! -s "../.env" ]]; then
        print_error ".env file is empty"
        echo "Please fill in your environment variables in the .env file"
        exit 1
    fi
    
    # Create namespace first (required for secret creation)
    print_status "Creating namespace..."
    kubectl apply -f namespace.yaml
    
    # Create secret from .env file
    if ! kubectl create secret generic modular-chatbot-secrets \
      --from-env-file="../.env" \
      --namespace=${NAMESPACE} \
      --dry-run=client -o yaml | kubectl apply -f -; then
        print_error "Failed to create secrets from .env file"
        echo "Please check your .env file format and ensure all required variables are set"
        exit 1
    fi
    
    print_status "Secrets created successfully from .env file"
    
    # Show created secrets for verification
    print_status "Verifying created secrets:"
    kubectl get secret modular-chatbot-secrets -n ${NAMESPACE} --show-labels
}

# Function to deploy resources
deploy_resources() {
    print_status "Deploying Kubernetes resources..."
    
    # Namespace is already created by create_secrets_from_env function
    print_status "Namespace already created"
    
    # Deploy ConfigMaps
    print_status "Deploying ConfigMaps..."
    kubectl apply -f configmap.yaml
    
    # Secrets are already created by create_secrets_from_env function
    print_status "Secrets already deployed from .env file"
    
    # Deploy RBAC
    print_status "Deploying RBAC resources..."
    kubectl apply -f rbac.yaml
    
    # Deploy Redis
    print_status "Deploying Redis..."
    kubectl apply -f redis-deployment.yaml
    
    # Wait for Redis to be ready
    print_status "Waiting for Redis to be ready..."
    kubectl wait --for=condition=available --timeout=${KUBECTL_TIMEOUT} deployment/redis-deployment -n ${NAMESPACE}
    
    # Deploy Backend
    print_status "Deploying Backend..."
    kubectl apply -f backend-deployment.yaml
    
    # Wait for Backend to be ready
    print_status "Waiting for Backend to be ready..."
    kubectl wait --for=condition=available --timeout=${KUBECTL_TIMEOUT} deployment/backend-deployment -n ${NAMESPACE}
    
    # Deploy Frontend
    print_status "Deploying Frontend..."
    kubectl apply -f frontend-deployment.yaml
    
    # Wait for Frontend to be ready
    print_status "Waiting for Frontend to be ready..."
    kubectl wait --for=condition=available --timeout=${KUBECTL_TIMEOUT} deployment/frontend-deployment -n ${NAMESPACE}
    
    # Deploy Services
    print_status "Deploying Services..."
    kubectl apply -f services.yaml
    
    # Deploy Ingress
    print_status "Deploying Ingress..."
    kubectl apply -f ingress.yaml
    
    # Deploy additional resources
    print_status "Deploying Network Policy..."
    kubectl apply -f network-policy.yaml
    
    print_status "Deploying Horizontal Pod Autoscalers..."
    kubectl apply -f hpa.yaml
    
    print_status "Deploying Pod Disruption Budgets..."
    kubectl apply -f pod-disruption-budget.yaml
}

# Function to verify deployment
verify_deployment() {
    print_status "Verifying deployment..."
    
    # Check pod status
    print_status "Checking pod status..."
    kubectl get pods -n ${NAMESPACE}
    
    # Check service status
    print_status "Checking service status..."
    kubectl get services -n ${NAMESPACE}
    
    # Check ingress status
    print_status "Checking ingress status..."
    kubectl get ingress -n ${NAMESPACE}
    
    # Check if all pods are running
    if kubectl get pods -n ${NAMESPACE} | grep -v Running | grep -v Completed | grep -q .; then
        print_warning "Some pods are not in Running state. Check the logs:"
        kubectl get pods -n ${NAMESPACE} --field-selector=status.phase!=Running
    else
        print_status "All pods are running successfully!"
    fi
}

# Function to show access information
show_access_info() {
    print_status "Deployment completed!"
    echo
    print_status "Access Information:"
    echo "  Frontend: https://chatbot.example.com"
    echo "  Backend API: https://api.chatbot.example.com"
    echo
    print_status "To check the status of your deployment:"
    echo "  kubectl get all -n ${NAMESPACE}"
    echo
    print_status "To view logs:"
    echo "  kubectl logs -f deployment/backend-deployment -n ${NAMESPACE}"
    echo "  kubectl logs -f deployment/frontend-deployment -n ${NAMESPACE}"
    echo "  kubectl logs -f deployment/redis-deployment -n ${NAMESPACE}"
    echo
    print_status "To scale deployments:"
    echo "  kubectl scale deployment backend-deployment --replicas=3 -n ${NAMESPACE}"
    echo "  kubectl scale deployment frontend-deployment --replicas=3 -n ${NAMESPACE}"
    echo
    print_status "=== AUTOMATED PORT FORWARDING ==="
    echo
    print_status "For local testing, use the automated port forwarding script:"
    echo "  Bash:      ./port-forward.sh"
    echo "  PowerShell: .\\port-forward.ps1"
    echo
    print_status "Port forwarding will automatically set up:"
    echo "  Frontend:  http://localhost:3000"
    echo "  Backend:   http://localhost:8000"
    echo "  Redis:     localhost:6379"
    echo
    print_status "To stop port forwarding:"
    echo "  Bash:      ./port-forward.sh -s"
    echo "  PowerShell: .\\port-forward.ps1 -Stop"
    echo
    print_status "Manual port forwarding (if needed):"
    echo "  kubectl port-forward service/frontend-service 3000:80 -n ${NAMESPACE}"
    echo "  kubectl port-forward service/backend-service 8000:8000 -n ${NAMESPACE}"
    echo "  kubectl port-forward service/redis-service 6379:6379 -n ${NAMESPACE}"
}

# Main deployment process
main() {
    print_status "Starting Kubernetes deployment for Modular Chatbot..."
    
    # Pre-deployment checks
    check_kubectl
    check_images
    create_secrets_from_env
    
    # Deploy resources
    deploy_resources
    
    # Verify deployment
    verify_deployment
    
    # Show access information
    show_access_info
    
    # Start port forwarding automatically unless --no-port-forward is specified
    if [ "$NO_PORT_FORWARD" = "false" ]; then
        print_status "Starting automatic port forwarding..."
        if command -v gnome-terminal &> /dev/null; then
            gnome-terminal -- bash -c "./port-forward.sh; exec bash"
        elif command -v xterm &> /dev/null; then
            xterm -e "./port-forward.sh" &
        elif command -v osascript &> /dev/null; then
            # macOS
            osascript -e 'tell app "Terminal" to do script "./port-forward.sh"'
        else
            # Fallback: run in background
            print_status "Starting port forwarding in background..."
            ./port-forward.sh &
            print_status "Port forwarding started in background. Use './port-forward.sh -s' to stop."
        fi
    else
        print_status "Port forwarding skipped as requested."
    fi
    
    print_status "Deployment script completed successfully!"
}

# Run main function
main "$@"