#!/usr/bin/env pwsh

# Script to set up Google credentials for Kubernetes
# This script encodes the google-credentials.json file and updates the Kubernetes secret

Write-Host "Setting up Google credentials for Kubernetes deployment..." -ForegroundColor Green

# Check if google-credentials.json exists in the backend directory
$credentialsPath = "backend/google-credentials.json"
if (-not (Test-Path $credentialsPath)) {
    Write-Error "google-credentials.json not found at $credentialsPath"
    Write-Host "Please make sure the file exists in the backend directory." -ForegroundColor Yellow
    exit 1
}

# Read and encode the credentials file
Write-Host "Reading and encoding google-credentials.json..." -ForegroundColor Cyan
$encodedCredentials = Get-Content $credentialsPath -Raw | base64 -w 0

# Update the secrets.yaml file
Write-Host "Updating secrets.yaml with encoded credentials..." -ForegroundColor Cyan
$secretsPath = "k8s/secrets.yaml"
if (-not (Test-Path $secretsPath)) {
    Write-Error "secrets.yaml not found at $secretsPath"
    exit 1
}

# Read the current secrets file
$secretsContent = Get-Content $secretsPath -Raw

# Replace the placeholder with the actual encoded credentials
$updatedContent = $secretsContent -replace "GOOGLE_APPLICATION_CREDENTIALS_CONTENT: your-service-account-json-base64-encoded", "GOOGLE_APPLICATION_CREDENTIALS_CONTENT: $encodedCredentials"

# Write back to the file
Set-Content -Path $secretsPath -Value $updatedContent -NoNewline

Write-Host "✅ Google credentials have been successfully encoded and added to secrets.yaml" -ForegroundColor Green
Write-Host "The credentials file at $credentialsPath has been encoded and stored in the Kubernetes secret." -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Apply the secret to your cluster: kubectl apply -f k8s/secrets.yaml" -ForegroundColor White
Write-Host "2. Deploy the backend: kubectl apply -f k8s/backend-deployment.yaml" -ForegroundColor White
Write-Host "3. Check the deployment: kubectl get pods -n modular-chatbot" -ForegroundColor White
