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

# Function to update secrets
update_secrets() {
    print_status "Updating secrets..."
    print_warning "Please update the secrets in k8s/secrets.yaml with your actual values:"
    print_warning "  - OPENAI_API_KEY: Your OpenAI API key (base64 encoded)"
    print_warning "  - SECRET_KEY: Your application secret key (base64 encoded)"
    print_warning "  - JWT_SECRET: Your JWT secret (base64 encoded)"
    print_warning "  - TLS certificate and key for HTTPS"
    
    read -p "Have you updated the secrets? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Please update the secrets first"
        exit 1
    fi
}

# Function to deploy resources
deploy_resources() {
    print_status "Deploying Kubernetes resources..."
    
    # Create namespace
    print_status "Creating namespace..."
    kubectl apply -f namespace.yaml
    
    # Deploy ConfigMaps and Secrets
    print_status "Deploying ConfigMaps and Secrets..."
    kubectl apply -f configmap.yaml
    kubectl apply -f secrets.yaml
    
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
}

# Main deployment process
main() {
    print_status "Starting Kubernetes deployment for Modular Chatbot..."
    
    # Pre-deployment checks
    check_kubectl
    check_images
    update_secrets
    
    # Deploy resources
    deploy_resources
    
    # Verify deployment
    verify_deployment
    
    # Show access information
    show_access_info
    
    print_status "Deployment script completed successfully!"
}

# Run main function
main "$@"