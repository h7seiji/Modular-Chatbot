#!/usr/bin/env pwsh

# Cloud Run Undeployment Script for Modular Chatbot
# This script removes the application from Google Cloud Run

param(
    [string]$ProjectId = "",
    [string]$Region = "us-central1",
    [string]$BackendServiceName = "modular-chatbot-backend",
    [string]$FrontendServiceName = "modular-chatbot-frontend",
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

# Main undeployment function
function UndeployCloudRun {
    Write-Host "🗑️  Starting Cloud Run undeployment for Modular Chatbot..." -ForegroundColor Yellow
    
    # Check if gcloud is installed
    if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
        Write-ErrorExit "Google Cloud SDK (gcloud) is not installed. Please install it first."
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
    
    # Check and delete frontend service
    try {
        $frontendExists = gcloud run services describe $FrontendServiceName --region=$Region --project=$ProjectId 2>$null
        if ($frontendExists) {
            Write-Host "🔍 Found frontend service: $FrontendServiceName" -ForegroundColor Cyan
            if (Confirm-Action "Delete frontend service '$FrontendServiceName'?") {
                Write-Host "🗑️  Deleting frontend service..." -ForegroundColor Yellow
                gcloud run services delete $FrontendServiceName --region=$Region --project=$ProjectId --quiet
                Write-Host "✅ Frontend service deleted successfully" -ForegroundColor Green
            }
        }
        else {
            Write-VerboseOutput "Frontend service '$FrontendServiceName' not found"
        }
    }
    catch {
        Write-VerboseOutput "Frontend service '$FrontendServiceName' not found or error checking"
    }
    
    # Check and delete backend service
    try {
        $backendExists = gcloud run services describe $BackendServiceName --region=$Region --project=$ProjectId 2>$null
        if ($backendExists) {
            Write-Host "🔍 Found backend service: $BackendServiceName" -ForegroundColor Cyan
            if (Confirm-Action "Delete backend service '$BackendServiceName'?") {
                Write-Host "🗑️  Deleting backend service..." -ForegroundColor Yellow
                gcloud run services delete $BackendServiceName --region=$Region --project=$ProjectId --quiet
                Write-Host "✅ Backend service deleted successfully" -ForegroundColor Green
            }
        }
        else {
            Write-VerboseOutput "Backend service '$BackendServiceName' not found"
        }
    }
    catch {
        Write-VerboseOutput "Backend service '$BackendServiceName' not found or error checking"
    }
    
    # Ask about removing secrets
    try {
        $secretExists = gcloud secrets describe "google-credentials" --project=$ProjectId 2>$null
        if ($secretExists) {
            Write-Host "🔍 Found secret: google-credentials" -ForegroundColor Cyan
            if (Confirm-Action "Delete Google Cloud secret 'google-credentials'?") {
                Write-Host "🗑️  Deleting secret..." -ForegroundColor Yellow
                gcloud secrets delete "google-credentials" --project=$ProjectId --quiet
                Write-Host "✅ Secret deleted successfully" -ForegroundColor Green
            }
        }
        else {
            Write-VerboseOutput "Secret 'google-credentials' not found"
        }
    }
    catch {
        Write-VerboseOutput "Secret 'google-credentials' not found or error checking"
    }
    
    # Ask about removing Artifact Registry repository
    try {
        $repoExists = gcloud artifacts repositories describe "modular-chatbot" --location=$Region --project=$ProjectId 2>$null
        if ($repoExists) {
            Write-Host "🔍 Found Artifact Registry repository: modular-chatbot" -ForegroundColor Cyan
            if (Confirm-Action "Delete Artifact Registry repository 'modular-chatbot' and all its images?") {
                Write-Host "🗑️  Deleting Artifact Registry repository..." -ForegroundColor Yellow
                gcloud artifacts repositories delete "modular-chatbot" --location=$Region --project=$ProjectId --quiet
                Write-Host "✅ Artifact Registry repository deleted successfully" -ForegroundColor Green
            }
        }
        else {
            Write-VerboseOutput "Artifact Registry repository 'modular-chatbot' not found"
        }
    }
    catch {
        Write-VerboseOutput "Artifact Registry repository 'modular-chatbot' not found or error checking"
    }
    
    Write-Host "✅ Undeployment completed!" -ForegroundColor Green
    Write-Host "`n📋 Note: Some resources may take a few minutes to be fully removed from Google Cloud." -ForegroundColor Yellow
}

# Execute undeployment
UndeployCloudRun
