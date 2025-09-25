#!/bin/bash

# Kubernetes deployment status check script for Modular Chatbot (Linux/macOS)
# This script checks the status of your deployment without redeploying

# Configuration
NAMESPACE="modular-chatbot"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

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

print_success() {
    echo -e "${CYAN}[SUCCESS]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -n, --namespace NAMESPACE    Kubernetes namespace (default: $NAMESPACE)"
    echo "  -h, --help                   Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                           Check deployment with default namespace"
    echo "  $0 -n my-namespace          Check deployment with custom namespace"
}

# Function to parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -n|--namespace)
                NAMESPACE="$2"
                shift 2
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
}

# Function to check if kubectl is available
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    print_status "kubectl is available and connected to cluster"
}

# Function to check namespace
check_namespace() {
    print_status "Checking namespace..."
    if kubectl get namespace "$NAMESPACE" --no-headers &> /dev/null; then
        print_success "Namespace '$NAMESPACE' exists"
        return 0
    else
        print_error "Namespace '$NAMESPACE' does not exist"
        return 1
    fi
}

# Function to check pods
check_pods() {
    print_status "Checking pods..."
    if kubectl get pods -n "$NAMESPACE" --no-headers &> /dev/null; then
        print_status "Pods found in namespace '$NAMESPACE':"
        
        local total_pods=0
        local running_pods=0
        
        while IFS= read -r line; do
            ((total_pods++))
            local pod_name=$(echo "$line" | awk '{print $1}')
            local pod_status=$(echo "$line" | awk '{print $3}')
            local pod_ready=$(echo "$line" | awk '{print $4}')
            
            if [[ "$pod_status" == "Running" ]]; then
                ((running_pods++))
                print_success "  $pod_name - Status: $pod_status, Ready: $pod_ready"
            else
                print_warning "  $pod_name - Status: $pod_status, Ready: $pod_ready"
            fi
        done < <(kubectl get pods -n "$NAMESPACE" --no-headers)
        
        if [[ $running_pods -eq $total_pods && $total_pods -gt 0 ]]; then
            print_success "All pods ($running_pods/$total_pods) are running"
            return 0
        else
            print_warning "Pods status: $running_pods/$total_pods running"
            return 1
        fi
    else
        print_warning "No pods found in namespace '$NAMESPACE'"
        return 1
    fi
}

# Function to check services
check_services() {
    print_status "Checking services..."
    if kubectl get services -n "$NAMESPACE" --no-headers &> /dev/null; then
        print_status "Services found in namespace '$NAMESPACE':"
        
        while IFS= read -r line; do
            local service_name=$(echo "$line" | awk '{print $1}')
            local service_type=$(echo "$line" | awk '{print $2}')
            local cluster_ip=$(echo "$line" | awk '{print $3}')
            local ports=$(echo "$line" | awk '{print $5}')
            
            print_success "  $service_name - Type: $service_type, ClusterIP: $cluster_ip, Ports: $ports"
        done < <(kubectl get services -n "$NAMESPACE" --no-headers)
        
        return 0
    else
        print_warning "No services found in namespace '$NAMESPACE'"
        return 1
    fi
}

# Function to check deployments
check_deployments() {
    print_status "Checking deployments..."
    if kubectl get deployments -n "$NAMESPACE" --no-headers &> /dev/null; then
        print_status "Deployments found in namespace '$NAMESPACE':"
        
        while IFS= read -r line; do
            local deployment_name=$(echo "$line" | awk '{print $1}')
            local ready=$(echo "$line" | awk '{print $2}')
            local up_to_date=$(echo "$line" | awk '{print $3}')
            local available=$(echo "$line" | awk '{print $4}')
            
            if [[ "$available" == "$ready" ]]; then
                print_success "  $deployment_name - Ready: $ready, Up-to-date: $up_to_date, Available: $available"
            else
                print_warning "  $deployment_name - Ready: $ready, Up-to-date: $up_to_date, Available: $available"
            fi
        done < <(kubectl get deployments -n "$NAMESPACE" --no-headers)
        
        return 0
    else
        print_warning "No deployments found in namespace '$NAMESPACE'"
        return 1
    fi
}

# Function to check ingress
check_ingress() {
    print_status "Checking ingress..."
    if kubectl get ingress -n "$NAMESPACE" --no-headers &> /dev/null; then
        print_status "Ingress found in namespace '$NAMESPACE':"
        
        while IFS= read -r line; do
            local ingress_name=$(echo "$line" | awk '{print $1}')
            local hosts=$(echo "$line" | awk '{print $3}')
            local ports=$(echo "$line" | awk '{print $4}')
            
            print_success "  $ingress_name - Hosts: $hosts, Ports: $ports"
        done < <(kubectl get ingress -n "$NAMESPACE" --no-headers)
        
        return 0
    else
        print_warning "No ingress found in namespace '$NAMESPACE' (this may be normal)"
        return 1
    fi
}

# Function to check secrets
check_secrets() {
    print_status "Checking secrets..."
    if kubectl get secrets -n "$NAMESPACE" --no-headers &> /dev/null; then
        print_status "Secrets found in namespace '$NAMESPACE':"
        
        while IFS= read -r line; do
            local secret_name=$(echo "$line" | awk '{print $1}')
            local secret_type=$(echo "$line" | awk '{print $2}')
            local data=$(echo "$line" | awk '{print $3}')
            
            print_success "  $secret_name - Type: $secret_type, Data: $data"
        done < <(kubectl get secrets -n "$NAMESPACE" --no-headers)
        
        return 0
    else
        print_warning "No secrets found in namespace '$NAMESPACE'"
        return 1
    fi
}

# Function to provide next steps
show_next_steps() {
    echo ""
    print_status "=== NEXT STEPS ==="
    echo ""
    
    print_status "If all resources are healthy, you can:"
    echo "  1. Start port forwarding for local testing:"
    echo "     Bash:      ./port-forward.sh"
    echo "     PowerShell: .\\\\port-forward.ps1"
    echo ""
    print_status "  2. Access the application:"
    echo "     Frontend:  http://localhost:3000"
    echo "     Backend:   http://localhost:8000"
    echo ""
    print_status "  3. Check logs:"
    echo "     kubectl logs -f deployment/backend-deployment -n $NAMESPACE"
    echo "     kubectl logs -f deployment/frontend-deployment -n $NAMESPACE"
    echo "     kubectl logs -f deployment/redis-deployment -n $NAMESPACE"
    echo ""
    print_status "  4. Troubleshoot issues:"
    echo "     kubectl get events -n $NAMESPACE"
    echo "     kubectl describe pods -n $NAMESPACE"
}

# Main function
main() {
    print_status "Modular Chatbot Deployment Status Check"
    echo "Namespace: $NAMESPACE"
    echo ""
    
    # Pre-checks
    check_kubectl
    
    # Check namespace
    if ! check_namespace; then
        print_error "Namespace '$NAMESPACE' does not exist. Please run the deployment script first."
        exit 1
    fi
    
    echo ""
    print_status "=== DEPLOYMENT STATUS ==="
    echo ""
    
    # Check various resources
    check_pods
    local pods_ok=$?
    echo ""
    
    check_services
    local services_ok=$?
    echo ""
    
    check_deployments
    local deployments_ok=$?
    echo ""
    
    check_ingress
    local ingress_ok=$?
    echo ""
    
    check_secrets
    local secrets_ok=$?
    echo ""
    
    # Summary
    print_status "=== SUMMARY ==="
    local healthy_count=0
    local total_count=5
    
    if [[ $pods_ok -eq 0 ]]; then 
        ((healthy_count++))
        print_success "✓ Pods are healthy"
    else 
        print_error "✗ Pods have issues"
    fi
    
    if [[ $services_ok -eq 0 ]]; then 
        ((healthy_count++))
        print_success "✓ Services are healthy"
    else 
        print_error "✗ Services have issues"
    fi
    
    if [[ $deployments_ok -eq 0 ]]; then 
        ((healthy_count++))
        print_success "✓ Deployments are healthy"
    else 
        print_error "✗ Deployments have issues"
    fi
    
    if [[ $ingress_ok -eq 0 ]]; then 
        ((healthy_count++))
        print_success "✓ Ingress is healthy"
    else 
        print_warning "✗ Ingress has issues (may be normal)"
    fi
    
    if [[ $secrets_ok -eq 0 ]]; then 
        ((healthy_count++))
        print_success "✓ Secrets are healthy"
    else 
        print_error "✗ Secrets have issues"
    fi
    
    echo ""
    if [[ $healthy_count -ge 4 ]]; then
        print_success "Deployment appears to be healthy ($healthy_count/$total_count components)"
        show_next_steps
    elif [[ $healthy_count -ge 2 ]]; then
        print_warning "Deployment is partially healthy ($healthy_count/$total_count components)"
        echo "Some components may still be starting up. Check the warnings above."
        show_next_steps
    else
        print_error "Deployment has significant issues ($healthy_count/$total_count components)"
        echo "Please check the errors above and consider redeploying."
    fi
}

# Parse command line arguments
parse_args "$@"

# Run main function
main "$@"
