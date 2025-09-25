# Kubernetes deployment status check script for Modular Chatbot (Windows PowerShell)
# This script checks the status of your deployment without redeploying

param(
    [string]$Namespace = "modular-chatbot"
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

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Cyan
}

# Function to check if kubectl is available
function Test-Kubectl {
    if (-not (Get-Command kubectl -ErrorAction SilentlyContinue)) {
        Write-Error "kubectl is not installed or not in PATH"
        exit 1
    }
    
    try {
        kubectl cluster-info | Out-Null
        Write-Status "kubectl is available and connected to cluster"
    }
    catch {
        Write-Error "Cannot connect to Kubernetes cluster"
        exit 1
    }
}

# Function to check namespace
function Test-Namespace {
    Write-Status "Checking namespace..."
    try {
        $namespaceInfo = kubectl get namespace $Namespace --no-headers 2>$null
        if ($namespaceInfo) {
            Write-Success "Namespace '$Namespace' exists"
            return $true
        }
        else {
            Write-Error "Namespace '$Namespace' does not exist"
            return $false
        }
    }
    catch {
        Write-Error "Failed to check namespace: $($_.Exception.Message)"
        return $false
    }
}

# Function to check pods
function Test-Pods {
    Write-Status "Checking pods..."
    try {
        $pods = kubectl get pods -n $Namespace --no-headers
        if ($pods) {
            Write-Status "Pods found in namespace '$Namespace':"
            $pods | ForEach-Object {
                $parts = $_ -split '\s+'
                $podName = $parts[0]
                $podStatus = $parts[2]
                $podReady = $parts[3]
                
                if ($podStatus -eq "Running") {
                    Write-Success "  $podName - Status: $podStatus, Ready: $podReady"
                }
                else {
                    Write-Warning "  $podName - Status: $podStatus, Ready: $podReady"
                }
            }
            
            # Check if all pods are running
            $runningPods = $pods | Where-Object { $_ -match "\s+Running\s+" }
            $totalPods = ($pods | Measure-Object).Count
            $runningCount = ($runningPods | Measure-Object). Count
            
            if ($runningCount -eq $totalPods -and $totalPods -gt 0) {
                Write-Success "All pods ($runningCount/$totalPods) are running"
                return $true
            }
            else {
                Write-Warning "Pods status: $runningCount/$totalPods running"
                return $false
            }
        }
        else {
            Write-Warning "No pods found in namespace '$Namespace'"
            return $false
        }
    }
    catch {
        Write-Error "Failed to check pods: $($_.Exception.Message)"
        return $false
    }
}

# Function to check services
function Test-Services {
    Write-Status "Checking services..."
    try {
        $services = kubectl get services -n $Namespace --no-headers
        if ($services) {
            Write-Status "Services found in namespace '$Namespace':"
            $services | ForEach-Object {
                $parts = $_ -split '\s+'
                $serviceName = $parts[0]
                $serviceType = $parts[1]
                $clusterIp = $parts[2]
                $ports = $parts[4]
                
                Write-Success "  $serviceName - Type: $serviceType, ClusterIP: $clusterIp, Ports: $ports"
            }
            return $true
        }
        else {
            Write-Warning "No services found in namespace '$Namespace'"
            return $false
        }
    }
    catch {
        Write-Error "Failed to check services: $($_.Exception.Message)"
        return $false
    }
}

# Function to check deployments
function Test-Deployments {
    Write-Status "Checking deployments..."
    try {
        $deployments = kubectl get deployments -n $Namespace --no-headers
        if ($deployments) {
            Write-Status "Deployments found in namespace '$Namespace':"
            $deployments | ForEach-Object {
                $parts = $_ -split '\s+'
                $deploymentName = $parts[0]
                $ready = $parts[1]
                $upToDate = $parts[2]
                $available = $parts[3]
                
                if ($available -eq $ready) {
                    Write-Success "  $deploymentName - Ready: $ready, Up-to-date: $upToDate, Available: $available"
                }
                else {
                    Write-Warning "  $deploymentName - Ready: $ready, Up-to-date: $upToDate, Available: $available"
                }
            }
            return $true
        }
        else {
            Write-Warning "No deployments found in namespace '$Namespace'"
            return $false
        }
    }
    catch {
        Write-Error "Failed to check deployments: $($_.Exception.Message)"
        return $false
    }
}

# Function to check ingress
function Test-Ingress {
    Write-Status "Checking ingress..."
    try {
        $ingress = kubectl get ingress -n $Namespace --no-headers
        if ($ingress) {
            Write-Status "Ingress found in namespace '$Namespace':"
            $ingress | ForEach-Object {
                $parts = $_ -split '\s+'
                $ingressName = $parts[0]
                $hosts = $parts[2]
                $ports = $parts[3]
                
                Write-Success "  $ingressName - Hosts: $hosts, Ports: $ports"
            }
            return $true
        }
        else {
            Write-Warning "No ingress found in namespace '$Namespace' (this may be normal)"
            return $false
        }
    }
    catch {
        Write-Warning "Could not check ingress: $($_.Exception.Message) (this may be normal)"
        return $false
    }
}

# Function to check secrets
function Test-Secrets {
    Write-Status "Checking secrets..."
    try {
        $secrets = kubectl get secrets -n $Namespace --no-headers
        if ($secrets) {
            Write-Status "Secrets found in namespace '$Namespace':"
            $secrets | ForEach-Object {
                $parts = $_ -split '\s+'
                $secretName = $parts[0]
                $secretType = $parts[1]
                $data = $parts[2]
                
                Write-Success "  $secretName - Type: $secretType, Data: $data"
            }
            return $true
        }
        else {
            Write-Warning "No secrets found in namespace '$Namespace'"
            return $false
        }
    }
    catch {
        Write-Error "Failed to check secrets: $($_.Exception.Message)"
        return $false
    }
}

# Function to provide next steps
function Show-NextSteps {
    Write-Host ""
    Write-Status "=== NEXT STEPS ==="
    Write-Host ""
    
    Write-Status "If all resources are healthy, you can:"
    Write-Host "  1. Start port forwarding for local testing:"
    Write-Host "     PowerShell: .\\port-forward.ps1"
    Write-Host "     Bash:      ./port-forward.sh"
    Write-Host ""
    Write-Status "  2. Access the application:"
    Write-Host "     Frontend:  http://localhost:3000"
    Write-Host "     Backend:   http://localhost:8000"
    Write-Host ""
    Write-Status "  3. Check logs:"
    Write-Host "     kubectl logs -f deployment/backend-deployment -n $Namespace"
    Write-Host "     kubectl logs -f deployment/frontend-deployment -n $Namespace"
    Write-Host "     kubectl logs -f deployment/redis-deployment -n $Namespace"
    Write-Host ""
    Write-Status "  4. Troubleshoot issues:"
    Write-Host "     kubectl get events -n $Namespace"
    Write-Host "     kubectl describe pods -n $Namespace"
}

# Main function
function Main {
    Write-Status "Modular Chatbot Deployment Status Check"
    Write-Host "Namespace: $Namespace"
    Write-Host ""
    
    # Pre-checks
    Test-Kubectl
    
    # Check namespace
    $namespaceExists = Test-Namespace
    if (-not $namespaceExists) {
        Write-Error "Namespace '$Namespace' does not exist. Please run the deployment script first."
        exit 1
    }
    
    Write-Host ""
    Write-Status "=== DEPLOYMENT STATUS ==="
    Write-Host ""
    
    # Check various resources
    $podsOk = Test-Pods
    Write-Host ""
    
    $servicesOk = Test-Services
    Write-Host ""
    
    $deploymentsOk = Test-Deployments
    Write-Host ""
    
    $ingressOk = Test-Ingress
    Write-Host ""
    
    $secretsOk = Test-Secrets
    Write-Host ""
    
    # Summary
    Write-Status "=== SUMMARY ==="
    $healthyCount = 0
    $totalCount = 5
    
    if ($podsOk) { $healthyCount++; Write-Success "✓ Pods are healthy" } else { Write-Error "✗ Pods have issues" }
    if ($servicesOk) { $healthyCount++; Write-Success "✓ Services are healthy" } else { Write-Error "✗ Services have issues" }
    if ($deploymentsOk) { $healthyCount++; Write-Success "✓ Deployments are healthy" } else { Write-Error "✗ Deployments have issues" }
    if ($ingressOk) { $healthyCount++; Write-Success "✓ Ingress is healthy" } else { Write-Warning "✗ Ingress has issues (may be normal)" }
    if ($secretsOk) { $healthyCount++; Write-Success "✓ Secrets are healthy" } else { Write-Error "✗ Secrets have issues" }
    
    Write-Host ""
    if ($healthyCount -ge 4) {
        Write-Success "Deployment appears to be healthy ($healthyCount/$totalCount components)"
        Show-NextSteps
    }
    elseif ($healthyCount -ge 2) {
        Write-Warning "Deployment is partially healthy ($healthyCount/$totalCount components)"
        Write-Host "Some components may still be starting up. Check the warnings above."
        Show-NextSteps
    }
    else {
        Write-Error "Deployment has significant issues ($healthyCount/$totalCount components)"
        Write-Host "Please check the errors above and consider redeploying."
    }
}

# Run main function
Main
