# Kubernetes deployment script for Modular Chatbot (Windows PowerShell)
# This script deploys the entire application stack to Kubernetes

param(
    [switch]$SkipChecks = $false,
    [string]$Namespace = "modular-chatbot",
    [int]$TimeoutSeconds = 300
)

# Configuration
$ErrorActionPreference = "Stop"

# Function to print colored output
function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Function to check if kubectl is available
function Test-Kubectl {
    Write-Status "Checking kubectl availability..."
    
    if (-not (Get-Command kubectl -ErrorAction SilentlyContinue)) {
        Write-Error "kubectl is not installed or not in PATH"
        Write-Host "Please install kubectl: https://kubernetes.io/docs/tasks/tools/install-kubectl-windows/"
        exit 1
    }
    
    # Check if we can connect to the cluster
    try {
        kubectl cluster-info | Out-Null
        Write-Status "kubectl is available and connected to cluster"
    }
    catch {
        Write-Error "Cannot connect to Kubernetes cluster"
        Write-Host "Please ensure your kubeconfig is properly configured"
        exit 1
    }
}

# Function to check if required images exist
function Test-Images {
    if ($SkipChecks) {
        Write-Status "Skipping image checks..."
        return
    }
    
    Write-Status "Checking if Docker images exist..."
    
    Write-Warning "Make sure the following images are built and pushed to your registry:"
    Write-Warning "  - modular-chatbot-backend:latest"
    Write-Warning "  - modular-chatbot-frontend:latest"
    
    $response = Read-Host "Have you built and pushed the images? (y/N)"
    if ($response -notmatch "^[Yy]$") {
        Write-Error "Please build and push the images first"
        Write-Host ""
        Write-Host "To build images:"
        Write-Host "  cd backend"
        Write-Host "  docker build -t your-registry/modular-chatbot-backend:latest ."
        Write-Host "  docker push your-registry/modular-chatbot-backend:latest"
        Write-Host ""
        Write-Host "  cd ../frontend"
        Write-Host "  docker build -t your-registry/modular-chatbot-frontend:latest ."
        Write-Host "  docker push your-registry/modular-chatbot-frontend:latest"
        exit 1
    }
}

# Function to update secrets
function Test-Secrets {
    if ($SkipChecks) {
        Write-Status "Skipping secrets checks..."
        return
    }
    
    Write-Status "Checking secrets configuration..."
    Write-Warning "Please update the secrets in k8s/secrets.yaml with your actual values:"
    Write-Warning "  - OPENAI_API_KEY: Your OpenAI API key (base64 encoded)"
    Write-Warning "  - SECRET_KEY: Your application secret key (base64 encoded)"
    Write-Warning "  - JWT_SECRET: Your JWT secret (base64 encoded)"
    Write-Warning "  - TLS certificate and key for HTTPS"
    Write-Host ""
    Write-Host "To encode secrets in PowerShell:"
    Write-Host '  [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("your_secret_here"))'
    
    $response = Read-Host "Have you updated the secrets? (y/N)"
    if ($response -notmatch "^[Yy]$") {
        Write-Error "Please update the secrets first"
        exit 1
    }
}

# Function to deploy resources
function Deploy-Resources {
    Write-Status "Deploying Kubernetes resources..."
    
    # Create namespace
    Write-Status "Creating namespace..."
    kubectl apply -f namespace.yaml
    
    # Deploy ConfigMaps and Secrets
    Write-Status "Deploying ConfigMaps and Secrets..."
    kubectl apply -f configmap.yaml
    kubectl apply -f secrets.yaml
    
    # Deploy RBAC
    Write-Status "Deploying RBAC resources..."
    kubectl apply -f rbac.yaml
    
    # Deploy Redis
    Write-Status "Deploying Redis..."
    kubectl apply -f redis-deployment.yaml
    
    # Wait for Redis to be ready
    Write-Status "Waiting for Redis to be ready..."
    kubectl wait --for=condition=available --timeout="$($TimeoutSeconds)s" deployment/redis-deployment -n $Namespace
    
    # Deploy Backend
    Write-Status "Deploying Backend..."
    kubectl apply -f backend-deployment.yaml
    
    # Wait for Backend to be ready
    Write-Status "Waiting for Backend to be ready..."
    kubectl wait --for=condition=available --timeout="$($TimeoutSeconds)s" deployment/backend-deployment -n $Namespace
    
    # Deploy Frontend
    Write-Status "Deploying Frontend..."
    kubectl apply -f frontend-deployment.yaml
    
    # Wait for Frontend to be ready
    Write-Status "Waiting for Frontend to be ready..."
    kubectl wait --for=condition=available --timeout="$($TimeoutSeconds)s" deployment/frontend-deployment -n $Namespace
    
    # Deploy Services
    Write-Status "Deploying Services..."
    kubectl apply -f services.yaml
    
    # Deploy Ingress
    Write-Status "Deploying Ingress..."
    kubectl apply -f ingress.yaml
    
    # Deploy additional resources
    Write-Status "Deploying Network Policy..."
    kubectl apply -f network-policy.yaml
    
    Write-Status "Deploying Horizontal Pod Autoscalers..."
    kubectl apply -f hpa.yaml
    
    Write-Status "Deploying Pod Disruption Budgets..."
    kubectl apply -f pod-disruption-budget.yaml
}

# Function to verify deployment
function Test-Deployment {
    Write-Status "Verifying deployment..."
    
    # Check pod status
    Write-Status "Checking pod status..."
    kubectl get pods -n $Namespace
    
    # Check service status
    Write-Status "Checking service status..."
    kubectl get services -n $Namespace
    
    # Check ingress status
    Write-Status "Checking ingress status..."
    kubectl get ingress -n $Namespace
    
    # Check if all pods are running
    $nonRunningPods = kubectl get pods -n $Namespace --field-selector=status.phase!=Running --no-headers 2>$null
    if ($nonRunningPods) {
        Write-Warning "Some pods are not in Running state:"
        kubectl get pods -n $Namespace --field-selector=status.phase!=Running
        Write-Host ""
        Write-Host "Check pod logs with:"
        Write-Host "  kubectl logs <pod-name> -n $Namespace"
    } else {
        Write-Status "All pods are running successfully!"
    }
}

# Function to show access information
function Show-AccessInfo {
    Write-Status "Deployment completed!"
    Write-Host ""
    Write-Status "Access Information:"
    Write-Host "  Frontend: https://chatbot.example.com"
    Write-Host "  Backend API: https://api.chatbot.example.com"
    Write-Host ""
    Write-Status "To check the status of your deployment:"
    Write-Host "  kubectl get all -n $Namespace"
    Write-Host ""
    Write-Status "To view logs:"
    Write-Host "  kubectl logs -f deployment/backend-deployment -n $Namespace"
    Write-Host "  kubectl logs -f deployment/frontend-deployment -n $Namespace"
    Write-Host "  kubectl logs -f deployment/redis-deployment -n $Namespace"
    Write-Host ""
    Write-Status "To scale deployments:"
    Write-Host "  kubectl scale deployment backend-deployment --replicas=3 -n $Namespace"
    Write-Host "  kubectl scale deployment frontend-deployment --replicas=3 -n $Namespace"
    Write-Host ""
    Write-Status "To port-forward for local testing:"
    Write-Host "  kubectl port-forward service/frontend-service 3000:80 -n $Namespace"
    Write-Host "  kubectl port-forward service/backend-service 8000:8000 -n $Namespace"
}

# Main deployment process
function Main {
    Write-Status "Starting Kubernetes deployment for Modular Chatbot..."
    Write-Host "Namespace: $Namespace"
    Write-Host "Timeout: $TimeoutSeconds seconds"
    Write-Host ""
    
    try {
        # Pre-deployment checks
        Test-Kubectl
        Test-Images
        Test-Secrets
        
        # Deploy resources
        Deploy-Resources
        
        # Verify deployment
        Test-Deployment
        
        # Show access information
        Show-AccessInfo
        
        Write-Status "Deployment script completed successfully!"
    }
    catch {
        Write-Error "Deployment failed: $($_.Exception.Message)"
        Write-Host ""
        Write-Host "To troubleshoot:"
        Write-Host "  kubectl get events -n $Namespace"
        Write-Host "  kubectl describe pods -n $Namespace"
        Write-Host "  kubectl logs -n $Namespace --selector=app=modular-chatbot"
        exit 1
    }
}

# Run main function
Main