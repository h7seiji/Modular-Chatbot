#!/bin/bash

# Cloud Run Undeployment Script for Modular Chatbot
# This script removes the application from Google Cloud Run

set -e

# Default values
PROJECT_ID=""
REGION="us-central1"
BACKEND_SERVICE_NAME="modular-chatbot-backend"
FRONTEND_SERVICE_NAME="modular-chatbot-frontend"
NO_CONFIRM=false
VERBOSE=false

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  --project-id PROJECT_ID    Google Cloud project ID"
    echo "  --region REGION            Cloud region (default: us-central1)"
    echo "  --backend-service NAME     Backend service name (default: modular-chatbot-backend)"
    echo "  --frontend-service NAME    Frontend service name (default: modular-chatbot-frontend)"
    echo "  --no-confirm               Skip confirmation prompts"
    echo "  --verbose                  Enable verbose output"
    echo "  --help                     Show this help message"
    exit 1
}

# Function to write verbose output
write_verbose() {
    if [ "$VERBOSE" = true ]; then
        echo "[VERBOSE] $1" >&2
    fi
}

# Function to write error and exit
write_error_exit() {
    echo "[ERROR] $1" >&2
    exit 1
}

# Function to confirm action
confirm_action() {
    if [ "$NO_CONFIRM" = true ]; then
        return 0
    fi
    read -p "$1 (y/N) " -r
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        return 0
    else
        return 1
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --project-id)
            PROJECT_ID="$2"
            shift 2
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        --backend-service)
            BACKEND_SERVICE_NAME="$2"
            shift 2
            ;;
        --frontend-service)
            FRONTEND_SERVICE_NAME="$2"
            shift 2
            ;;
        --no-confirm)
            NO_CONFIRM=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            show_usage
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            ;;
    esac
done

# Main undeployment function
undeploy_cloudrun() {
    echo "🗑️  Starting Cloud Run undeployment for Modular Chatbot..."
    
    # Check if gcloud is installed
    if ! command -v gcloud &> /dev/null; then
        write_error_exit "Google Cloud SDK (gcloud) is not installed. Please install it first."
    fi
    
    # Get project ID if not provided
    if [ -z "$PROJECT_ID" ]; then
        PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
        if [ -z "$PROJECT_ID" ]; then
            write_error_exit "No Google Cloud project configured. Please run 'gcloud init' or provide --project-id parameter."
        fi
    fi
    
    write_verbose "Using project: $PROJECT_ID"
    write_verbose "Using region: $REGION"
    
    # Check if user is authenticated
    if ! gcloud auth list --format="value(account)" --filter="status:ACTIVE" 2>/dev/null | grep -q "@"; then
        write_error_exit "Not authenticated with Google Cloud. Please run 'gcloud auth login'."
    fi
    
    local auth_account
    auth_account=$(gcloud auth list --format="value(account)" --filter="status:ACTIVE" 2>/dev/null)
    write_verbose "Authenticated as: $auth_account"
    
    # Check and delete frontend service
    if gcloud run services describe "$FRONTEND_SERVICE_NAME" --region="$REGION" --project="$PROJECT_ID" &>/dev/null; then
        echo "🔍 Found frontend service: $FRONTEND_SERVICE_NAME"
        if confirm_action "Delete frontend service '$FRONTEND_SERVICE_NAME'?"; then
            echo "🗑️  Deleting frontend service..."
            gcloud run services delete "$FRONTEND_SERVICE_NAME" --region="$REGION" --project="$PROJECT_ID" --quiet
            echo "✅ Frontend service deleted successfully"
        fi
    else
        write_verbose "Frontend service '$FRONTEND_SERVICE_NAME' not found"
    fi
    
    # Check and delete backend service
    if gcloud run services describe "$BACKEND_SERVICE_NAME" --region="$REGION" --project="$PROJECT_ID" &>/dev/null; then
        echo "🔍 Found backend service: $BACKEND_SERVICE_NAME"
        if confirm_action "Delete backend service '$BACKEND_SERVICE_NAME'?"; then
            echo "🗑️  Deleting backend service..."
            gcloud run services delete "$BACKEND_SERVICE_NAME" --region="$REGION" --project="$PROJECT_ID" --quiet
            echo "✅ Backend service deleted successfully"
        fi
    else
        write_verbose "Backend service '$BACKEND_SERVICE_NAME' not found"
    fi
    
    # Ask about removing secrets
    if gcloud secrets describe "google-credentials" --project="$PROJECT_ID" &>/dev/null; then
        echo "🔍 Found secret: google-credentials"
        if confirm_action "Delete Google Cloud secret 'google-credentials'?"; then
            echo "🗑️  Deleting secret..."
            gcloud secrets delete "google-credentials" --project="$PROJECT_ID" --quiet
            echo "✅ Secret deleted successfully"
        fi
    else
        write_verbose "Secret 'google-credentials' not found"
    fi
    
    # Ask about removing Artifact Registry repository
    if gcloud artifacts repositories describe "modular-chatbot" --location="$REGION" --project="$PROJECT_ID" &>/dev/null; then
        echo "🔍 Found Artifact Registry repository: modular-chatbot"
        if confirm_action "Delete Artifact Registry repository 'modular-chatbot' and all its images?"; then
            echo "🗑️  Deleting Artifact Registry repository..."
            gcloud artifacts repositories delete "modular-chatbot" --location="$REGION" --project="$PROJECT_ID" --quiet
            echo "✅ Artifact Registry repository deleted successfully"
        fi
    else
        write_verbose "Artifact Registry repository 'modular-chatbot' not found"
    fi
    
    echo "✅ Undeployment completed!"
    echo ""
    echo "📋 Note: Some resources may take a few minutes to be fully removed from Google Cloud."
}

# Execute undeployment
undeploy_cloudrun
