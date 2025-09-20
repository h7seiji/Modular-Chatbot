# Kubernetes YAML validation script for Windows PowerShell
# This script validates the YAML syntax of all Kubernetes manifests

param(
    [switch]$Verbose = $false
)

$ErrorActionPreference = "Continue"

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

# Function to validate YAML files
function Test-YamlFiles {
    Write-Status "Validating Kubernetes YAML files..."
    
    $yamlFiles = Get-ChildItem -Path "." -Filter "*.yaml" | Where-Object { $_.Name -ne "README.md" }
    $validationErrors = 0
    
    foreach ($file in $yamlFiles) {
        Write-Host "Validating $($file.Name)..." -NoNewline
        
        try {
            # Try to parse YAML using kubectl dry-run (client-side only)
            $result = kubectl apply --dry-run=client --validate=false -f $file.Name 2>&1
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host " OK" -ForegroundColor Green
                if ($Verbose) {
                    Write-Host "  $result" -ForegroundColor Gray
                }
            } else {
                Write-Host " FAILED" -ForegroundColor Red
                Write-Error "  $result"
                $validationErrors++
            }
        }
        catch {
            Write-Host " FAILED" -ForegroundColor Red
            Write-Error "  Failed to validate: $($_.Exception.Message)"
            $validationErrors++
        }
    }
    
    return $validationErrors
}

# Function to check required tools
function Test-Prerequisites {
    Write-Status "Checking prerequisites..."
    
    # Check kubectl
    if (-not (Get-Command kubectl -ErrorAction SilentlyContinue)) {
        Write-Error "kubectl is not installed or not in PATH"
        Write-Host "Please install kubectl: https://kubernetes.io/docs/tasks/tools/install-kubectl-windows/"
        return $false
    } else {
        Write-Status "kubectl is available"
    }
    
    return $true
}

# Function to show file summary
function Show-FileSummary {
    Write-Status "Kubernetes manifest files:"
    
    $yamlFiles = Get-ChildItem -Path "." -Filter "*.yaml"
    foreach ($file in $yamlFiles) {
        $content = Get-Content $file.Name -Raw
        $resourceCount = ($content | Select-String "^kind:" -AllMatches).Matches.Count
        Write-Host "  $($file.Name) - $resourceCount resource(s)" -ForegroundColor Cyan
    }
}

# Main validation process
function Main {
    Write-Status "Starting Kubernetes YAML validation..."
    Write-Host ""
    
    # Check prerequisites
    if (-not (Test-Prerequisites)) {
        exit 1
    }
    
    # Show file summary
    Show-FileSummary
    Write-Host ""
    
    # Validate YAML files
    $errors = Test-YamlFiles
    
    Write-Host ""
    if ($errors -eq 0) {
        Write-Status "All YAML files are valid!"
        Write-Host ""
        Write-Status "Next steps:"
        Write-Host "  1. Update image references in deployment files"
        Write-Host "  2. Update secrets in secrets.yaml"
        Write-Host "  3. Update domain names in ingress.yaml and configmap.yaml"
        Write-Host "  4. Run .\deploy.ps1 to deploy to Kubernetes"
    } else {
        Write-Error "Found $errors validation error(s)"
        Write-Host ""
        Write-Host "Please fix the errors above before deploying."
        exit 1
    }
}

# Run main function
Main