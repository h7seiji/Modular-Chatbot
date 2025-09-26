#!/bin/bash

# Cloud Run Deployment Script for Modular Chatbot
# This script deploys the application to Google Cloud Run

set -e

# Default values
PROJECT_ID=""
REGION="us-central1"
BACKEND_SERVICE_NAME="modular-chatbot-backend"
FRONTEND_SERVICE_NAME="modular-chatbot-frontend"
REDIS_URL=""
GEMINI_API_KEY=""
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
    echo "  --redis-url URL            Redis connection URL"
    echo "  --gemini-api-key KEY       Gemini API key"
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
        --redis-url)
            REDIS_URL="$2"
            shift 2
            ;;
        --gemini-api-key)
            GEMINI_API_KEY="$2"
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

# Main deployment function
deploy_cloudrun() {
    echo "🚀 Starting Cloud Run deployment for Modular Chatbot..."
    
    # Check if gcloud is installed
    if ! command -v gcloud &> /dev/null; then
        write_error_exit "Google Cloud SDK (gcloud) is not installed. Please install it first."
    fi
    
    # Check if docker is installed
    if ! command -v docker &> /dev/null; then
        write_error_exit "Docker is not installed. Please install it first."
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
    
    # Enable required APIs
    echo "📋 Enabling required Google Cloud APIs..."
    apis=("run.googleapis.com" "cloudbuild.googleapis.com" "artifactregistry.googleapis.com" "secretmanager.googleapis.com")
    for api in "${apis[@]}"; do
        write_verbose "Enabling $api..."
        gcloud services enable "$api" --project="$PROJECT_ID"
    done
    
    # Create Artifact Registry repository
    echo "📦 Setting up Artifact Registry..."
    local repo_name="modular-chatbot"
    if ! gcloud artifacts repositories describe "$repo_name" --location="$REGION" --project="$PROJECT_ID" 2>/dev/null; then
        write_verbose "Creating Artifact Registry repository..."
        gcloud artifacts repositories create "$repo_name" \
            --repository-format=docker \
            --location="$REGION" \
            --project="$PROJECT_ID"
    else
        write_verbose "Artifact Registry repository already exists"
    fi
    
    # Configure Docker for Artifact Registry
    echo "🔧 Configuring Docker authentication..."
    gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet
    
    # Get environment variables
    if [ -z "$REDIS_URL" ]; then
        REDIS_URL="${REDIS_URL:-}"
        if [ -z "$REDIS_URL" ]; then
            read -p "Enter Redis URL (e.g., redis://your-redis-host:6379/0): " REDIS_URL
        fi
    fi
    
    if [ -z "$GEMINI_API_KEY" ]; then
        GEMINI_API_KEY="${GEMINI_API_KEY:-}"
        if [ -z "$GEMINI_API_KEY" ]; then
            read -p "Enter Gemini API Key: " GEMINI_API_KEY
        fi
    fi
    
    # Read Google credentials file content for environment variable
    echo "🔐 Reading Google credentials..."
    if [ ! -f "backend/google-credentials.json" ]; then
        write_error_exit "Google credentials file not found at backend/google-credentials.json"
    fi
    local google_credentials_content
    google_credentials_content=$(cat "backend/google-credentials.json")
    
    # Build backend image
    echo "🏗️  Building backend Docker image..."
    local backend_image_tag="${REGION}-docker.pkg.dev/${PROJECT_ID}/${repo_name}/backend:latest"
    docker build -f backend/Dockerfile -t "$backend_image_tag" ./backend
    
    # Build frontend image
    echo "🏗️  Building frontend Docker image..."
    local frontend_image_tag="${REGION}-docker.pkg.dev/${PROJECT_ID}/${repo_name}/frontend:latest"
    docker build -f frontend/Dockerfile --build-arg REACT_APP_API_URL=https://modular-chatbot-backend-625904623277.us-central1.run.app --build-arg REACT_APP_ENVIRONMENT=production -t "$frontend_image_tag" ./frontend
    
    # Push images to Artifact Registry
    echo "📤 Pushing images to Artifact Registry..."
    docker push "$backend_image_tag"
    docker push "$frontend_image_tag"
    
    # Deploy backend service
    echo "🚀 Deploying backend service to Cloud Run..."
    if ! confirm_action "Deploy backend service?"; then
        echo "Backend deployment cancelled."
        return 1
    fi
    
    gcloud run deploy "$BACKEND_SERVICE_NAME" \
        --image="$backend_image_tag" \
        --region="$REGION" \
        --platform=managed \
        --allow-unauthenticated \
        --cpu=1 \
        --memory=512Mi \
        --max-instances=10 \
        --set-env-vars="ENVIRONMENT=production" \
        --set-env-vars="LOG_LEVEL=INFO" \
        --set-env-vars="REDIS_URL=$REDIS_URL" \
        --set-env-vars="GEMINI_API_KEY=$GEMINI_API_KEY" \
        --set-env-vars="GOOGLE_APPLICATION_CREDENTIALS_CONTENT=$google_credentials_content" \
        --project="$PROJECT_ID"
    
    # Get backend URL
    local backend_url
    backend_url=$(gcloud run services describe "$BACKEND_SERVICE_NAME" \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --format="value(status.url)")
    
    write_verbose "Backend deployed to: $backend_url"
    
    # Deploy frontend service
    echo "🚀 Deploying frontend service to Cloud Run..."
    if ! confirm_action "Deploy frontend service?"; then
        echo "Frontend deployment cancelled."
        return 1
    fi
    
    gcloud run deploy "$FRONTEND_SERVICE_NAME" \
        --image="$frontend_image_tag" \
        --region="$REGION" \
        --platform=managed \
        --allow-unauthenticated \
        --port=80 \
        --cpu=500m \
        --memory=256Mi \
        --max-instances=10 \
        --set-env-vars="REACT_APP_ENVIRONMENT=production" \
        --set-env-vars="REACT_APP_API_URL=/api" \
        --set-env-vars="BACKEND_HOST=backend-service" \
        --project="$PROJECT_ID"
    
    # Get frontend URL
    local frontend_url
    frontend_url=$(gcloud run services describe "$FRONTEND_SERVICE_NAME" \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --format="value(status.url)")
    
    # Show deployment results
    echo "✅ Deployment completed successfully!"
    echo "🌐 Frontend URL: $frontend_url"
    echo "🔧 Backend URL:  $backend_url"
    
    echo ""
    echo "📋 Next steps:"
    echo "1. Test your application at the frontend URL above"
    echo "2. Monitor your services in Google Cloud Console"
    echo "3. Check logs with: gcloud logging tail 'resource.type=cloud_run_revision'"
    echo "4. To undeploy, run: ./undeploy-cloudrun.sh"
}

# Execute deployment
deploy_cloudrun
