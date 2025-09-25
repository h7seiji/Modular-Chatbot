# Kubernetes deployment script for Modular Chatbot (Windows PowerShell)
# This script deploys the entire application stack to Kubernetes

param(
    [switch]$SkipChecks = $false,
    [string]$Namespace = "modular-chatbot",
    [int]$TimeoutSeconds = 300,
    [switch]$NoPortForward = $false
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

# Function to create secrets from .env file
function Create-SecretsFromEnv {
    if ($SkipChecks) {
        Write-Status "Skipping secrets creation..."
        return
    }
    
    Write-Status "Creating secrets from .env file..."
    
    # Check if .env file exists
    if (-not (Test-Path "..\.env")) {
        Write-Error ".env file not found in the project root"
        Write-Host "Please create a .env file from .env.example with your actual values"
        exit 1
    }
    
    # Check if .env file has content
    $envContent = Get-Content "..\.env" -Raw
    if ([string]::IsNullOrWhiteSpace($envContent)) {
        Write-Error ".env file is empty"
        Write-Host "Please fill in your environment variables in the .env file"
        exit 1
    }
    
    # Check if Google Cloud credentials file exists
    $credentialsPath = "..\backend\google-credentials.json"
    if (-not (Test-Path $credentialsPath)) {
        Write-Warning "Google Cloud credentials file not found at $credentialsPath"
        Write-Host "Please create a google-credentials.json file with your service account credentials"
        Write-Host "You can download this from Google Cloud Console -> IAM & Admin -> Service Accounts"
    }
    
    # Create namespace first (required for secret creation)
    Write-Status "Creating namespace..."
    kubectl apply -f namespace.yaml
    
    # Create secret from .env file and Google credentials
    try {
        Write-Status "Creating Kubernetes secret from .env file..."
        
        # Read the .env file and extract environment variables
        $envContent = Get-Content "..\.env" | Where-Object { $_ -notmatch "^#" -and $_.Trim() -ne "" }
        
        # Build the kubectl create secret command with all environment variables
        $secretCmd = "kubectl create secret generic modular-chatbot-secrets --namespace=$Namespace"
        
        foreach ($line in $envContent) {
            if ($line -match "^(.+?)=(.*)$") {
                $key = $matches[1].Trim()
                $value = $matches[2].Trim()
                # Include empty values to ensure all keys are present in the secret
                $secretCmd += " --from-literal=`"$key=$value`""
            }
        }
        
        # Add Google Cloud credentials if the file exists
        if (Test-Path $credentialsPath) {
            Write-Status "Adding Google Cloud credentials to secret..."
            $credentialsContent = Get-Content $credentialsPath -Raw
            $credentialsBase64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($credentialsContent))
            $secretCmd += " --from-literal=`"GOOGLE_APPLICATION_CREDENTIALS_CONTENT=$credentialsBase64`""
            
            # Extract project_id from the credentials JSON
            try {
                $credentialsJson = $credentialsContent | ConvertFrom-Json
                if ($credentialsJson.project_id) {
                    $secretCmd += " --from-literal=`"GOOGLE_CLOUD_PROJECT=$($credentialsJson.project_id)`""
                    Write-Status "Google Cloud project ID extracted and added to secret"
                } else {
                    Write-Warning "project_id not found in Google credentials file"
                }
                
                # Add Google Cloud region - check if already set in .env, otherwise use default
                $gcpRegionFromEnv = $envVars["GOOGLE_CLOUD_REGION"]
                if ($gcpRegionFromEnv) {
                    $gcpRegion = $gcpRegionFromEnv
                    Write-Status "Google Cloud region from .env: $gcpRegion"
                } else {
                    # Default to us-central1
                    $gcpRegion = "us-central1"
                    Write-Status "Google Cloud region using default: $gcpRegion"
                }
                $secretCmd += " --from-literal=`"GOOGLE_CLOUD_REGION=$gcpRegion`""
            } catch {
                Write-Warning "Failed to parse Google credentials JSON: $_"
            }
            
            Write-Status "Google Cloud credentials added to secret successfully"
        }
        
        # Execute the secret creation command
        Invoke-Expression $secretCmd
        
        Write-Status "Secrets created successfully from .env file"
    }
    catch {
        Write-Error "Failed to create secrets from .env file: $($_.Exception.Message)"
        Write-Host "Please check your .env file format and ensure all required variables are set"
        exit 1
    }
    
    # Show created secrets for verification
    Write-Status "Verifying created secrets:"
    kubectl get secret modular-chatbot-secrets -n $Namespace --show-labels
}

# Function to deploy resources
function Deploy-Resources {
    Write-Status "Deploying Kubernetes resources..."
    
    # Namespace is already created by Create-SecretsFromEnv function
    Write-Status "Namespace already created"
    
    # Deploy ConfigMaps
    Write-Status "Deploying ConfigMaps..."
    try {
        kubectl apply -f configmap.yaml
        Write-Status "ConfigMaps deployed successfully"
    }
    catch {
        Write-Warning "Failed to deploy ConfigMaps: $($_.Exception.Message)"
        Write-Host "Continuing with deployment - ConfigMaps may not be critical"
    }
    
    # Secrets are already created by Create-SecretsFromEnv function
    Write-Status "Secrets already deployed from .env file"
    
    # Deploy RBAC
    Write-Status "Deploying RBAC resources..."
    try {
        kubectl apply -f rbac.yaml
        Write-Status "RBAC resources deployed successfully"
    }
    catch {
        Write-Warning "Failed to deploy RBAC resources: $($_.Exception.Message)"
        Write-Host "Continuing with deployment - RBAC may not be required in your cluster"
    }
    
    # Deploy Redis
    Write-Status "Deploying Redis..."
    try {
        kubectl apply -f redis-deployment.yaml
        Write-Status "Redis deployment started"
    }
    catch {
        Write-Warning "Failed to deploy Redis: $($_.Exception.Message)"
        Write-Host "Continuing with deployment - Redis may already exist or deployment failed"
    }
    
    # Wait for Redis to be ready
    Write-Status "Waiting for Redis to be ready..."
    try {
        kubectl wait --for=condition=available --timeout="$($TimeoutSeconds)s" deployment/redis-deployment -n $Namespace
        Write-Status "Redis is ready"
    }
    catch {
        Write-Warning "Redis deployment is not ready yet: $($_.Exception.Message)"
        Write-Host "Continuing with deployment - Redis will become available shortly"
    }
    
    # Deploy Backend
    Write-Status "Deploying Backend..."
    try {
        kubectl apply -f backend-deployment.yaml
        Write-Status "Backend deployment started"
    }
    catch {
        Write-Warning "Failed to deploy Backend: $($_.Exception.Message)"
        Write-Host "Continuing with deployment - Backend may already exist or deployment failed"
    }
    
    # Wait for Backend to be ready
    Write-Status "Waiting for Backend to be ready..."
    try {
        kubectl wait --for=condition=available --timeout="$($TimeoutSeconds)s" deployment/backend-deployment -n $Namespace
        Write-Status "Backend is ready"
    }
    catch {
        Write-Warning "Backend deployment is not ready yet: $($_.Exception.Message)"
        Write-Host "Continuing with deployment - Backend will become available shortly"
    }
    
    # Deploy Frontend
    Write-Status "Deploying Frontend..."
    try {
        kubectl apply -f frontend-deployment.yaml
        Write-Status "Frontend deployment started"
    }
    catch {
        Write-Warning "Failed to deploy Frontend: $($_.Exception.Message)"
        Write-Host "Continuing with deployment - Frontend may already exist or deployment failed"
    }
    
    # Wait for Frontend to be ready
    Write-Status "Waiting for Frontend to be ready..."
    try {
        kubectl wait --for=condition=available --timeout="$($TimeoutSeconds)s" deployment/frontend-deployment -n $Namespace
        Write-Status "Frontend is ready"
    }
    catch {
        Write-Warning "Frontend deployment is not ready yet: $($_.Exception.Message)"
        Write-Host "Continuing with deployment - Frontend will become available shortly"
    }
    
    # Deploy Services
    Write-Status "Deploying Services..."
    try {
        kubectl apply -f services.yaml
        Write-Status "Services deployed successfully"
    }
    catch {
        Write-Warning "Failed to deploy Services: $($_.Exception.Message)"
        Write-Host "Continuing with deployment - Services may already exist"
    }
    
    # Deploy Ingress
    Write-Status "Deploying Ingress..."
    try {
        kubectl apply -f ingress.yaml
        Write-Status "Ingress deployed successfully"
    }
    catch {
        Write-Warning "Failed to deploy Ingress: $($_.Exception.Message)"
        Write-Host "This is normal if ingress controller is not configured"
    }
    
    # Deploy additional resources
    Write-Status "Deploying Network Policy..."
    try {
        kubectl apply -f network-policy.yaml
        Write-Status "Network Policy deployed successfully"
    }
    catch {
        Write-Warning "Failed to deploy Network Policy: $($_.Exception.Message)"
        Write-Host "This is normal if Network Policies are not supported in your cluster"
    }
    
    Write-Status "Deploying Horizontal Pod Autoscalers..."
    try {
        kubectl apply -f hpa.yaml
        Write-Status "Horizontal Pod Autoscalers deployed successfully"
    }
    catch {
        Write-Warning "Failed to deploy Horizontal Pod Autoscalers: $($_.Exception.Message)"
        Write-Host "This is normal if metrics server is not configured"
    }
    
    Write-Status "Deploying Pod Disruption Budgets..."
    try {
        kubectl apply -f pod-disruption-budget.yaml
        Write-Status "Pod Disruption Budgets deployed successfully"
    }
    catch {
        Write-Warning "Failed to deploy Pod Disruption Budgets: $($_.Exception.Message)"
        Write-Host "This is normal if PDBs are not supported in your cluster"
    }
}

# Function to verify deployment
function Test-Deployment {
    Write-Status "Verifying deployment..."
    
    # Check pod status
    Write-Status "Checking pod status..."
    try {
        kubectl get pods -n $Namespace
    }
    catch {
        Write-Warning "Could not retrieve pod status: $($_.Exception.Message)"
    }
    
    # Check service status
    Write-Status "Checking service status..."
    try {
        kubectl get services -n $Namespace
    }
    catch {
        Write-Warning "Could not retrieve service status: $($_.Exception.Message)"
    }
    
    # Check ingress status
    Write-Status "Checking ingress status..."
    try {
        kubectl get ingress -n $Namespace
    }
    catch {
        Write-Warning "Could not retrieve ingress status: $($_.Exception.Message)"
        Write-Host "This is normal if ingress controller is not configured or resources are still provisioning."
    }
    
    # Check if all pods are running
    try {
        $nonRunningPods = kubectl get pods -n $Namespace --field-selector=status.phase!=Running --no-headers 2>$null
        if ($nonRunningPods) {
            Write-Warning "Some pods are not in Running state:"
            kubectl get pods -n $Namespace --field-selector=status.phase!=Running
            Write-Host ""
            Write-Host "Check pod logs with:"
            Write-Host "  kubectl logs <pod-name> -n $Namespace"
        }
        else {
            Write-Status "All pods are running successfully!"
        }
    }
    catch {
        Write-Warning "Could not check pod running status: $($_.Exception.Message)"
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
    Write-Status "=== AUTOMATED PORT FORWARDING ==="
    Write-Host ""
    Write-Status "For local testing, use the automated port forwarding script:"
    Write-Host "  PowerShell: .\port-forward.ps1"
    Write-Host "  Bash:      ./port-forward.sh"
    Write-Host ""
    Write-Status "Port forwarding will automatically set up:"
    Write-Host "  Frontend:  http://localhost:3000"
    Write-Host "  Backend:   http://localhost:8000"
    Write-Host "  Redis:     localhost:6379"
    Write-Host ""
    Write-Status "To stop port forwarding:"
    Write-Host "  PowerShell: .\port-forward.ps1 -Stop"
    Write-Host "  Bash:      ./port-forward.sh -s"
    Write-Host ""
    Write-Status "Manual port forwarding (if needed):"
    Write-Host "  kubectl port-forward service/frontend-service 3000:80 -n $Namespace"
    Write-Host "  kubectl port-forward service/backend-service 8000:8000 -n $Namespace"
    Write-Host "  kubectl port-forward service/redis-service 6379:6379 -n $Namespace"
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
        Create-SecretsFromEnv
        
        # Deploy resources
        Deploy-Resources
        
        # Verify deployment
        Test-Deployment
        
        # Show access information
        Show-AccessInfo
        
        # Start port forwarding automatically unless NoPortForward is specified
        if (-not $NoPortForward) {
            Write-Status "Starting automatic port forwarding..."
            try {
                Start-Process powershell -ArgumentList "-NoExit", "-File", "$PSScriptRoot\port-forward.ps1" -WindowStyle Normal
                Write-Status "Port forwarding started in a new PowerShell window."
            }
            catch {
                Write-Warning "Failed to start automatic port forwarding. Please run manually:"
                Write-Host "  .\port-forward.ps1"
            }
        }
        else {
            Write-Status "Port forwarding skipped as requested."
        }
        
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
