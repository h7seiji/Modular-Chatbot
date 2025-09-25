# Kubernetes undeployment script for Modular Chatbot (Windows PowerShell)
# This script removes the entire application stack from Kubernetes

param(
    [switch]$Force = $false,
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
        exit 1
    }
    
    # Check if we can connect to the cluster
    try {
        kubectl cluster-info | Out-Null
        Write-Status "kubectl is available and connected to cluster"
    }
    catch {
        Write-Error "Cannot connect to Kubernetes cluster"
        exit 1
    }
}

# Function to confirm deletion
function Confirm-Deletion {
    if ($Force) {
        Write-Status "Force flag specified, skipping confirmation..."
        return
    }
    
    Write-Warning "This will delete the entire Modular Chatbot application from Kubernetes"
    Write-Warning "This includes all data stored in Redis (conversations, etc.)"
    Write-Host ""
    
    $response = Read-Host "Are you sure you want to continue? (y/N)"
    if ($response -notmatch "^[Yy]$") {
        Write-Status "Undeployment cancelled"
        exit 0
    }
}

# Function to remove resources
function Remove-Resources {
    Write-Status "Removing Kubernetes resources..."
    
    # Remove in reverse order of deployment
    
    # Remove Pod Disruption Budgets
    Write-Status "Removing Pod Disruption Budgets..."
    kubectl delete -f pod-disruption-budget.yaml --ignore-not-found=true 2>$null
    
    # Remove Horizontal Pod Autoscalers
    Write-Status "Removing Horizontal Pod Autoscalers..."
    kubectl delete -f hpa.yaml --ignore-not-found=true 2>$null
    
    # Remove Network Policy
    Write-Status "Removing Network Policy..."
    kubectl delete -f network-policy.yaml --ignore-not-found=true 2>$null
    
    # Remove Ingress
    Write-Status "Removing Ingress..."
    kubectl delete -f ingress.yaml --ignore-not-found=true 2>$null
    
    # Remove Services
    Write-Status "Removing Services..."
    kubectl delete -f services.yaml --ignore-not-found=true 2>$null
    
    # Remove Deployments
    Write-Status "Removing Frontend deployment..."
    kubectl delete -f frontend-deployment.yaml --ignore-not-found=true 2>$null
    
    Write-Status "Removing Backend deployment..."
    kubectl delete -f backend-deployment.yaml --ignore-not-found=true 2>$null
    
    Write-Status "Removing Redis deployment..."
    kubectl delete -f redis-deployment.yaml --ignore-not-found=true 2>$null
    
    # Remove RBAC
    Write-Status "Removing RBAC resources..."
    kubectl delete -f rbac.yaml --ignore-not-found=true 2>$null
    
    # Remove ConfigMaps and Secrets
    Write-Status "Removing ConfigMaps and Secrets..."
    # kubectl delete -f secrets.yaml --ignore-not-found=true 2>$null
    kubectl delete -f configmap.yaml --ignore-not-found=true 2>$null
    
    # Wait for pods to terminate
    Write-Status "Waiting for pods to terminate..."
    try {
        kubectl wait --for=delete pods --all -n $Namespace --timeout="$($TimeoutSeconds)s" 2>$null
    }
    catch {
        Write-Warning "Some pods may still be terminating..."
    }
    
    # Remove namespace (this will remove any remaining resources)
    Write-Status "Removing namespace..."
    kubectl delete -f namespace.yaml --ignore-not-found=true 2>$null
}

# Function to verify removal
function Test-Removal {
    Write-Status "Verifying removal..."
    
    # Check if namespace still exists
    try {
        $namespaceExists = kubectl get namespace $Namespace 2>$null
        if ($namespaceExists) {
            Write-Warning "Namespace $Namespace still exists, waiting for cleanup..."
            try {
                kubectl wait --for=delete namespace/$Namespace --timeout="$($TimeoutSeconds)s" 2>$null
            }
            catch {
                Write-Warning "Timeout waiting for namespace deletion"
            }
        }
    }
    catch {
        # Namespace doesn't exist, which is what we want
    }
    
    # Final check
    try {
        $finalCheck = kubectl get namespace $Namespace 2>$null
        if ($finalCheck) {
            Write-Warning "Namespace $Namespace still exists. You may need to manually clean up remaining resources."
            Write-Host "Run: kubectl get all -n $Namespace"
        }
        else {
            Write-Status "All resources have been successfully removed!"
        }
    }
    catch {
        Write-Status "All resources have been successfully removed!"
    }
}

# Function to show cleanup information
function Show-CleanupInfo {
    Write-Status "Undeployment completed!"
    Write-Host ""
    Write-Status "Additional cleanup (if needed):"
    Write-Host "  - Check for any remaining PersistentVolumes: kubectl get pv"
    Write-Host "  - Clean up any external resources (LoadBalancers, etc.)"
    Write-Host "  - Remove Docker images if no longer needed:"
    Write-Host "    docker rmi modular-chatbot-backend:latest"
    Write-Host "    docker rmi modular-chatbot-frontend:latest"
    Write-Host ""
    Write-Status "To redeploy the application:"
    Write-Host "  .\deploy.ps1"
    Write-Host ""
    Write-Status "To check for any remaining resources:"
    Write-Host "  kubectl get all --all-namespaces | Select-String 'modular-chatbot'"
}

# Main undeployment process
function Main {
    Write-Status "Starting Kubernetes undeployment for Modular Chatbot..."
    Write-Host "Namespace: $Namespace"
    Write-Host "Timeout: $TimeoutSeconds seconds"
    Write-Host ""
    
    try {
        # Pre-undeployment checks
        Test-Kubectl
        Confirm-Deletion
        
        # Remove resources
        Remove-Resources
        
        # Verify removal
        Test-Removal
        
        # Show cleanup information
        Show-CleanupInfo
        
        Write-Status "Undeployment script completed successfully!"
    }
    catch {
        Write-Error "Undeployment failed: $($_.Exception.Message)"
        Write-Host ""
        Write-Host "To troubleshoot:"
        Write-Host "  kubectl get all -n $Namespace"
        Write-Host "  kubectl describe namespace $Namespace"
        Write-Host ""
        Write-Host "To force cleanup:"
        Write-Host "  kubectl delete namespace $Namespace --force --grace-period=0"
        exit 1
    }
}

# Run main function
Main