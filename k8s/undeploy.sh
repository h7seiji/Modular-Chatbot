#!/bin/bash

# Kubernetes undeployment script for Modular Chatbot
# This script removes the entire application stack from Kubernetes

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="modular-chatbot"

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

# Function to confirm deletion
confirm_deletion() {
    print_warning "This will delete the entire Modular Chatbot application from Kubernetes"
    print_warning "This includes all data stored in Redis (conversations, etc.)"
    echo
    read -p "Are you sure you want to continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Undeployment cancelled"
        exit 0
    fi
}

# Function to remove resources
remove_resources() {
    print_status "Removing Kubernetes resources..."
    
    # Remove in reverse order of deployment
    
    # Remove Pod Disruption Budgets
    print_status "Removing Pod Disruption Budgets..."
    kubectl delete -f pod-disruption-budget.yaml --ignore-not-found=true
    
    # Remove Horizontal Pod Autoscalers
    print_status "Removing Horizontal Pod Autoscalers..."
    kubectl delete -f hpa.yaml --ignore-not-found=true
    
    # Remove Network Policy
    print_status "Removing Network Policy..."
    kubectl delete -f network-policy.yaml --ignore-not-found=true
    
    # Remove Ingress
    print_status "Removing Ingress..."
    kubectl delete -f ingress.yaml --ignore-not-found=true
    
    # Remove Services
    print_status "Removing Services..."
    kubectl delete -f services.yaml --ignore-not-found=true
    
    # Remove Deployments
    print_status "Removing Frontend deployment..."
    kubectl delete -f frontend-deployment.yaml --ignore-not-found=true
    
    print_status "Removing Backend deployment..."
    kubectl delete -f backend-deployment.yaml --ignore-not-found=true
    
    print_status "Removing Redis deployment..."
    kubectl delete -f redis-deployment.yaml --ignore-not-found=true
    
    # Remove RBAC
    print_status "Removing RBAC resources..."
    kubectl delete -f rbac.yaml --ignore-not-found=true
    
    # Remove ConfigMaps and Secrets
    print_status "Removing ConfigMaps and Secrets..."
    kubectl delete -f secrets.yaml --ignore-not-found=true
    kubectl delete -f configmap.yaml --ignore-not-found=true
    
    # Wait for pods to terminate
    print_status "Waiting for pods to terminate..."
    kubectl wait --for=delete pods --all -n ${NAMESPACE} --timeout=300s || true
    
    # Remove namespace (this will remove any remaining resources)
    print_status "Removing namespace..."
    kubectl delete -f namespace.yaml --ignore-not-found=true
}

# Function to verify removal
verify_removal() {
    print_status "Verifying removal..."
    
    # Check if namespace still exists
    if kubectl get namespace ${NAMESPACE} &> /dev/null; then
        print_warning "Namespace ${NAMESPACE} still exists, waiting for cleanup..."
        kubectl wait --for=delete namespace/${NAMESPACE} --timeout=300s || true
    fi
    
    # Final check
    if kubectl get namespace ${NAMESPACE} &> /dev/null; then
        print_warning "Namespace ${NAMESPACE} still exists. You may need to manually clean up remaining resources."
    else
        print_status "All resources have been successfully removed!"
    fi
}

# Function to show cleanup information
show_cleanup_info() {
    print_status "Undeployment completed!"
    echo
    print_status "Additional cleanup (if needed):"
    echo "  - Check for any remaining PersistentVolumes: kubectl get pv"
    echo "  - Clean up any external resources (LoadBalancers, etc.)"
    echo "  - Remove Docker images if no longer needed"
    echo
    print_status "To redeploy the application, run: ./deploy.sh"
}

# Main undeployment process
main() {
    print_status "Starting Kubernetes undeployment for Modular Chatbot..."
    
    # Pre-undeployment checks
    check_kubectl
    confirm_deletion
    
    # Remove resources
    remove_resources
    
    # Verify removal
    verify_removal
    
    # Show cleanup information
    show_cleanup_info
    
    print_status "Undeployment script completed successfully!"
}

# Run main function
main "$@"