# Kubernetes port forwarding script for Modular Chatbot (Windows PowerShell)
# This script automatically sets up port forwarding for local testing

param(
    [string]$Namespace = "modular-chatbot",
    [int]$FrontendPort = 3000,
    [int]$BackendPort = 8000,
    [int]$RedisPort = 6379,
    [switch]$Stop = $false
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

# Function to check if services are running
function Test-Services {
    Write-Status "Checking if services are running..."
    
    $frontendService = kubectl get service frontend-service -n $Namespace --no-headers 2>$null
    $backendService = kubectl get service backend-service -n $Namespace --no-headers 2>$null
    $redisService = kubectl get service redis-service -n $Namespace --no-headers 2>$null
    
    if (-not $frontendService) {
        Write-Error "Frontend service not found. Please deploy the application first."
        exit 1
    }
    
    if (-not $backendService) {
        Write-Error "Backend service not found. Please deploy the application first."
        exit 1
    }
    
    if (-not $redisService) {
        Write-Error "Redis service not found. Please deploy the application first."
        exit 1
    }
    
    Write-Status "All services are running"
}

# Function to stop existing port forwarding processes
function Stop-PortForwarding {
    Write-Status "Stopping existing port forwarding processes..."
    
    # Find and kill processes containing kubectl port-forward
    $processes = Get-Process | Where-Object { $_.ProcessName -eq "kubectl" -and $_.CommandLine -like "*port-forward*" }
    
    if ($processes) {
        foreach ($process in $processes) {
            try {
                Stop-Process -Id $process.Id -Force
                Write-Status "Stopped port forwarding process (PID: $($process.Id))"
            }
            catch {
                Write-Warning "Could not stop process $($process.Id): $($_.Exception.Message)"
            }
        }
    }
    else {
        Write-Status "No existing port forwarding processes found"
    }
}

# Function to start port forwarding
function Start-PortForwarding {
    Write-Status "Starting port forwarding for local testing..."
    Write-Host ""
    Write-Status "Port Forwarding Configuration:"
    Write-Host "  Frontend:  localhost:$FrontendPort -> frontend-service:80"
    Write-Host "  Backend:   localhost:$BackendPort -> backend-service:8000"
    Write-Host "  Redis:     localhost:$RedisPort -> redis-service:6379"
    Write-Host ""
    
    # Start port forwarding in background jobs
    try {
        Write-Status "Starting frontend port forwarding..."
        $frontendJob = Start-Job -ScriptBlock {
            param($ns, $port)
            kubectl port-forward service/frontend-service ${port}:80 -n $ns
        } -ArgumentList $Namespace, $FrontendPort
        
        Write-Status "Starting backend port forwarding..."
        $backendJob = Start-Job -ScriptBlock {
            param($ns, $port)
            kubectl port-forward service/backend-service ${port}:8000 -n $ns
        } -ArgumentList $Namespace, $BackendPort
        
        Write-Status "Starting Redis port forwarding..."
        $redisJob = Start-Job -ScriptBlock {
            param($ns, $port)
            kubectl port-forward service/redis-service ${port}:6379 -n $ns
        } -ArgumentList $Namespace, $RedisPort
        
        # Wait a moment for jobs to start and check if they failed immediately
        Start-Sleep -Seconds 2
        
        $failedJobs = @()
        if ($frontendJob.State -eq "Failed") {
            $failedJobs += "Frontend: " + (Receive-Job -Id $frontendJob.Id -ErrorAction SilentlyContinue -WarningAction SilentlyContinue)
        }
        if ($backendJob.State -eq "Failed") {
            $failedJobs += "Backend: " + (Receive-Job -Id $backendJob.Id -ErrorAction SilentlyContinue -WarningAction SilentlyContinue)
        }
        if ($redisJob.State -eq "Failed") {
            $failedJobs += "Redis: " + (Receive-Job -Id $redisJob.Id -ErrorAction SilentlyContinue -WarningAction SilentlyContinue)
        }
        
        if ($failedJobs.Count -gt 0) {
            Write-Error "Some port forwarding jobs failed to start:"
            foreach ($failure in $failedJobs) {
                Write-Error "  $failure"
            }
            exit 1
        }
        
        Write-Status "All port forwarding processes started in background"
        Write-Host ""
        Write-Status "Access URLs:"
        Write-Host "  Frontend:  http://localhost:$FrontendPort"
        Write-Host "  Backend:   http://localhost:$BackendPort"
        Write-Host "  Redis:     localhost:$RedisPort"
        Write-Host ""
        Write-Warning "Port forwarding is running in background jobs."
        Write-Warning "Use 'Get-Job' to view jobs and 'Stop-Job <JobId>' to stop specific jobs."
        Write-Warning "Use '$PSScriptRoot\port-forward.ps1 -Stop' to stop all port forwarding."
        
    }
    catch {
        Write-Error "Failed to start port forwarding: $($_.Exception.Message)"
        exit 1
    }
}

# Function to show status
function Show-Status {
    Write-Status "Port Forwarding Status:"
    
    $jobs = Get-Job | Where-Object { $_.State -eq "Running" }
    
    if ($jobs) {
        Write-Host "Active port forwarding jobs:"
        foreach ($job in $jobs) {
            Write-Host "  Job ID: $($job.Id) - $($job.Name) - $($job.State)"
        }
    }
    else {
        Write-Warning "No active port forwarding jobs found"
    }
    
    Write-Host ""
    Write-Status "To check if ports are accessible:"
    Write-Host "  Frontend:  Test http://localhost:$FrontendPort in browser"
    Write-Host "  Backend:   Test http://localhost:$BackendPort/api/health"
    Write-Host "  Redis:     Use redis-cli -p $RedisPort"
}

# Main function
function Main {
    Write-Status "Modular Chatbot Port Forwarding Script"
    Write-Host "Namespace: $Namespace"
    Write-Host ""
    
    # Pre-checks
    Test-Kubectl
    Test-Services
    
    if ($Stop) {
        Stop-PortForwarding
    }
    else {
        # Stop existing processes first
        Stop-PortForwarding
        # Start new port forwarding
        Start-PortForwarding
    }
    
    # Show status
    Show-Status
}

# Run main function
Main
