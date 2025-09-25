#!/bin/bash

# Kubernetes port forwarding script for Modular Chatbot (Linux/macOS)
# This script automatically sets up port forwarding for local testing

# Configuration
NAMESPACE="modular-chatbot"
FRONTEND_PORT=3000
BACKEND_PORT=8000
REDIS_PORT=6379
STOP=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -n, --namespace NAMESPACE    Kubernetes namespace (default: $NAMESPACE)"
    echo "  -f, --frontend-port PORT     Frontend local port (default: $FRONTEND_PORT)"
    echo "  -b, --backend-port PORT      Backend local port (default: $BACKEND_PORT)"
    echo "  -r, --redis-port PORT        Redis local port (default: $REDIS_PORT)"
    echo "  -s, --stop                   Stop existing port forwarding"
    echo "  -h, --help                   Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                           Start port forwarding with default settings"
    echo "  $0 -n my-namespace          Use custom namespace"
    echo "  $0 -f 8080 -b 9000         Use custom ports"
    echo "  $0 -s                       Stop all port forwarding"
}

# Function to parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -n|--namespace)
                NAMESPACE="$2"
                shift 2
                ;;
            -f|--frontend-port)
                FRONTEND_PORT="$2"
                shift 2
                ;;
            -b|--backend-port)
                BACKEND_PORT="$2"
                shift 2
                ;;
            -r|--redis-port)
                REDIS_PORT="$2"
                shift 2
                ;;
            -s|--stop)
                STOP=true
                shift
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

# Function to check if services are running
check_services() {
    print_status "Checking if services are running..."
    
    if ! kubectl get service frontend-service -n "$NAMESPACE" --no-headers &> /dev/null; then
        print_error "Frontend service not found. Please deploy the application first."
        exit 1
    fi
    
    if ! kubectl get service backend-service -n "$NAMESPACE" --no-headers &> /dev/null; then
        print_error "Backend service not found. Please deploy the application first."
        exit 1
    fi
    
    if ! kubectl get service redis-service -n "$NAMESPACE" --no-headers &> /dev/null; then
        print_error "Redis service not found. Please deploy the application first."
        exit 1
    fi
    
    print_status "All services are running"
}

# Function to stop existing port forwarding processes
stop_port_forwarding() {
    print_status "Stopping existing port forwarding processes..."
    
    # Find and kill kubectl port-forward processes
    local pids
    pids=$(pgrep -f "kubectl.*port-forward")
    
    if [[ -n "$pids" ]]; then
        echo "$pids" | xargs -r kill -9
        print_status "Stopped existing port forwarding processes"
    else
        print_status "No existing port forwarding processes found"
    fi
}

# Function to start port forwarding
start_port_forwarding() {
    print_status "Starting port forwarding for local testing..."
    echo ""
    print_status "Port Forwarding Configuration:"
    echo "  Frontend:  localhost:$FRONTEND_PORT -> frontend-service:80"
    echo "  Backend:   localhost:$BACKEND_PORT -> backend-service:8000"
    echo "  Redis:     localhost:$REDIS_PORT -> redis-service:6379"
    echo ""
    
    # Create background processes for port forwarding
    print_status "Starting frontend port forwarding..."
    kubectl port-forward service/frontend-service "$FRONTEND_PORT":80 -n "$NAMESPACE" &
    local frontend_pid=$!
    
    print_status "Starting backend port forwarding..."
    kubectl port-forward service/backend-service "$BACKEND_PORT":8000 -n "$NAMESPACE" &
    local backend_pid=$!
    
    print_status "Starting Redis port forwarding..."
    kubectl port-forward service/redis-service "$REDIS_PORT":6379 -n "$NAMESPACE" &
    local redis_pid=$!
    
    # Save PIDs to a file for later cleanup
    echo "$frontend_pid" > "/tmp/modular-chatbot-port-forward-frontend.pid"
    echo "$backend_pid" > "/tmp/modular-chatbot-port-forward-backend.pid"
    echo "$redis_pid" > "/tmp/modular-chatbot-port-forward-redis.pid"
    
    print_status "All port forwarding processes started in background"
    echo ""
    print_status "Access URLs:"
    echo "  Frontend:  http://localhost:$FRONTEND_PORT"
    echo "  Backend:   http://localhost:$BACKEND_PORT"
    echo "  Redis:     localhost:$REDIS_PORT"
    echo ""
    print_warning "Port forwarding is running in background processes."
    print_warning "Process IDs saved to /tmp/modular-chatbot-port-forward-*.pid"
    print_warning "Use '$0 -s' to stop all port forwarding."
    print_warning "Use 'ps aux | grep kubectl' to view running processes."
}

# Function to show status
show_status() {
    print_status "Port Forwarding Status:"
    
    # Check if processes are running
    if [[ -f "/tmp/modular-chatbot-port-forward-frontend.pid" ]]; then
        local frontend_pid
        frontend_pid=$(cat "/tmp/modular-chatbot-port-forward-frontend.pid")
        if ps -p "$frontend_pid" > /dev/null 2>&1; then
            echo "  Frontend:  Running (PID: $frontend_pid)"
        else
            echo "  Frontend:  Not running"
        fi
    else
        echo "  Frontend:  Not running"
    fi
    
    if [[ -f "/tmp/modular-chatbot-port-forward-backend.pid" ]]; then
        local backend_pid
        backend_pid=$(cat "/tmp/modular-chatbot-port-forward-backend.pid")
        if ps -p "$backend_pid" > /dev/null 2>&1; then
            echo "  Backend:   Running (PID: $backend_pid)"
        else
            echo "  Backend:   Not running"
        fi
    else
        echo "  Backend:   Not running"
    fi
    
    if [[ -f "/tmp/modular-chatbot-port-forward-redis.pid" ]]; then
        local redis_pid
        redis_pid=$(cat "/tmp/modular-chatbot-port-forward-redis.pid")
        if ps -p "$redis_pid" > /dev/null 2>&1; then
            echo "  Redis:     Running (PID: $redis_pid)"
        else
            echo "  Redis:     Not running"
        fi
    else
        echo "  Redis:     Not running"
    fi
    
    echo ""
    print_status "To check if ports are accessible:"
    echo "  Frontend:  Test http://localhost:$FRONTEND_PORT in browser"
    echo "  Backend:   Test http://localhost:$BACKEND_PORT/api/health"
    echo "  Redis:     Use redis-cli -p $REDIS_PORT"
}

# Main function
main() {
    print_status "Modular Chatbot Port Forwarding Script"
    echo "Namespace: $NAMESPACE"
    echo ""
    
    # Pre-checks
    check_kubectl
    check_services
    
    if [[ "$STOP" == true ]]; then
        stop_port_forwarding
    else
        # Stop existing processes first
        stop_port_forwarding
        # Start new port forwarding
        start_port_forwarding
    fi
    
    # Show status
    show_status
}

# Parse command line arguments
parse_args "$@"

# Run main function
main "$@"
