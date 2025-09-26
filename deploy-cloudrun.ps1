#!/usr/bin/env pwsh

# Cloud Run Deployment Script for Modular Chatbot
# This script deploys the application to Google Cloud Run

param(
    [string]$ProjectId = "",
    [string]$Region = "us-central1",
    [string]$BackendServiceName = "modular-chatbot-backend",
    [string]$FrontendServiceName = "modular-chatbot-frontend",
    [string]$RedisUrl = "",
    [string]$GeminiApiKey = "",
    [switch]$NoConfirm = $false,
    [switch]$Verbose = $false
)

# Function to write verbose output
function Write-VerboseOutput {
    param([string]$Message)
    if ($Verbose) {
        Write-Host "[VERBOSE] $Message" -ForegroundColor Cyan
    }
}

# Function to write error and exit
function Write-ErrorExit {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
    exit 1
}

# Function to confirm action
function Confirm-Action {
    param([string]$Message)
    if ($NoConfirm) {
        return $true
    }
    $response = Read-Host "$Message (y/N)"
    return $response -match '^[Yy]$'
}

# Main deployment function
function DeployCloudRun {
    Write-Host "Starting Cloud Run deployment for Modular Chatbot..." -ForegroundColor Green
    
    # Check if gcloud is installed
    if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
        Write-ErrorExit "Google Cloud SDK (gcloud) is not installed. Please install it first."
    }
    
    # Check if docker is installed
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-ErrorExit "Docker is not installed. Please install it first."
    }
    
    # Get project ID if not provided
    if ([string]::IsNullOrEmpty($ProjectId)) {
        $ProjectId = gcloud config get-value project 2>$null
        if ([string]::IsNullOrEmpty($ProjectId)) {
            Write-ErrorExit "No Google Cloud project configured. Please run 'gcloud init' or provide --ProjectId parameter."
        }
    }
    
    Write-VerboseOutput "Using project: $ProjectId"
    Write-VerboseOutput "Using region: $Region"
    
    # Check if user is authenticated
    try {
        $authAccount = gcloud auth list --format="value(account)" --filter="status:ACTIVE" 2>$null
        if ([string]::IsNullOrEmpty($authAccount)) {
            Write-ErrorExit "Not authenticated with Google Cloud. Please run 'gcloud auth login'."
        }
        Write-VerboseOutput "Authenticated as: $authAccount"
    }
    catch {
        Write-ErrorExit "Failed to check authentication status. Please ensure you're logged in with 'gcloud auth login'."
    }
    
    # Enable required APIs
    Write-Host "Enabling required Google Cloud APIs..." -ForegroundColor Yellow
    $apis = @("run.googleapis.com", "cloudbuild.googleapis.com", "artifactregistry.googleapis.com", "secretmanager.googleapis.com")
    foreach ($api in $apis) {
        Write-VerboseOutput "Enabling $api..."
        gcloud services enable $api --project=$ProjectId
    }
    
    # Create Artifact Registry repository
    Write-Host "Setting up Artifact Registry..." -ForegroundColor Yellow
    $repoName = "modular-chatbot"
    try {
        gcloud artifacts repositories describe $repoName --location=$Region --project=$ProjectId 2>$null
        Write-VerboseOutput "Artifact Registry repository already exists"
    }
    catch {
        Write-VerboseOutput "Creating Artifact Registry repository..."
        gcloud artifacts repositories create $repoName `
            --repository-format=docker `
            --location=$Region `
            --project=$ProjectId
    }
    
    # Configure Docker for Artifact Registry
    Write-Host "Configuring Docker authentication..." -ForegroundColor Yellow
    gcloud auth configure-docker $Region-docker.pkg.dev --quiet
    
    # Get environment variables
    if ([string]::IsNullOrEmpty($RedisUrl)) {
        $RedisUrl = $env:REDIS_URL
        if ([string]::IsNullOrEmpty($RedisUrl)) {
            $RedisUrl = Read-Host "Enter Redis URL (e.g., redis://your-redis-host:6379/0)"
        }
    }
    
    if ([string]::IsNullOrEmpty($GeminiApiKey)) {
        $GeminiApiKey = $env:GEMINI_API_KEY
        if ([string]::IsNullOrEmpty($GeminiApiKey)) {
            $GeminiApiKey = Read-Host "Enter Gemini API Key"
        }
    }
    
    # Read Google credentials file content for environment variable
    Write-Host "Reading Google credentials..." -ForegroundColor Yellow
    if (-not (Test-Path "backend/google-credentials.json")) {
        Write-ErrorExit "Google credentials file not found at backend/google-credentials.json"
    }
    $googleCredentialsContent = Get-Content "backend/google-credentials.json" -Raw
    
    # Build backend image
    Write-Host "Building backend Docker image..." -ForegroundColor Yellow
    $backendImageTag = "$Region-docker.pkg.dev/$ProjectId/$repoName/backend:latest"
    docker build -f backend/Dockerfile -t $backendImageTag ./backend
    
    # Build frontend image
    Write-Host "Building frontend Docker image..." -ForegroundColor Yellow
    $frontendImageTag = "$Region-docker.pkg.dev/$ProjectId/$repoName/frontend:latest"
    docker build -f frontend/Dockerfile --build-arg REACT_APP_API_URL=https://modular-chatbot-backend-625904623277.us-central1.run.app --build-arg REACT_APP_ENVIRONMENT=production -t $frontendImageTag ./frontend
    
    # Push images to Artifact Registry
    Write-Host "Pushing images to Artifact Registry..." -ForegroundColor Yellow
    docker push $backendImageTag
    docker push $frontendImageTag
    
    # Deploy backend service
    Write-Host "Deploying backend service to Cloud Run..." -ForegroundColor Yellow
    $backendDeployArgs = @(
        "run", "deploy", $BackendServiceName,
        "--image", $backendImageTag,
        "--region", $Region,
        "--platform", "managed",
        "--allow-unauthenticated",
        "--cpu", "1",
        "--memory", "512Mi",
        "--max-instances", "10",
        "--set-env-vars", "ENVIRONMENT=production",
        "--set-env-vars", "LOG_LEVEL=INFO",
        "--set-env-vars", "REDIS_URL=$RedisUrl",
        "--set-env-vars", "GEMINI_API_KEY=$GeminiApiKey",
        "--set-env-vars", "GOOGLE_APPLICATION_CREDENTIALS_CONTENT=$googleCredentialsContent",
        "--project", $ProjectId
    )
    
    if (-not (Confirm-Action "Deploy backend service?")) {
        Write-Host "Backend deployment cancelled." -ForegroundColor Yellow
        return
    }
    
    gcloud @backendDeployArgs
    
    # Get backend URL
    $backendUrl = gcloud run services describe $BackendServiceName `
        --region=$Region `
        --project=$ProjectId `
        --format="value(status.url)"
    
    Write-VerboseOutput "Backend deployed to: $backendUrl"
    
    # Deploy frontend service
    Write-Host "Deploying frontend service to Cloud Run..." -ForegroundColor Yellow
    $frontendDeployArgs = @(
        "run", "deploy", $FrontendServiceName,
        "--image", $frontendImageTag,
        "--region", $Region,
        "--platform", "managed",
        "--allow-unauthenticated",
        "--port", "80",
        "--cpu", "500m",
        "--memory", "256Mi",
        "--max-instances", "10",
        "--set-env-vars", "REACT_APP_ENVIRONMENT=production",
        "--set-env-vars", "REACT_APP_API_URL=/api",
        "--set-env-vars", "BACKEND_HOST=backend-service",
        "--project", $ProjectId
    )
    
    if (-not (Confirm-Action "Deploy frontend service?")) {
        Write-Host "Frontend deployment cancelled." -ForegroundColor Yellow
        return
    }
    
    gcloud @frontendDeployArgs
    
    # Get frontend URL
    $frontendUrl = gcloud run services describe $FrontendServiceName `
        --region=$Region `
        --project=$ProjectId `
        --format="value(status.url)"
    
    # Show deployment results
    Write-Host "Deployment completed successfully!" -ForegroundColor Green
    Write-Host "Frontend URL: $frontendUrl" -ForegroundColor Cyan
    Write-Host "Backend URL:  $backendUrl" -ForegroundColor Cyan
    
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Test your application at the frontend URL above"
    Write-Host "2. Monitor your services in Google Cloud Console"
    Write-Host "3. Check logs with: gcloud logging tail 'resource.type=cloud_run_revision'"
    Write-Host "4. To undeploy, run: .\undeploy-cloudrun.ps1"
}

# Execute deployment
DeployCloudRun
