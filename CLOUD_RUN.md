# Google Cloud Run Deployment Guide

This guide explains how to deploy the Modular Chatbot to Google Cloud Run, a fully managed serverless platform that automatically scales your applications.

## Overview

The Modular Chatbot can be deployed to Google Cloud Run with the following architecture:
- **Frontend**: React application served by NGINX on Cloud Run
- **Backend**: FastAPI application on Cloud Run
- **Redis**: External Redis service (Cloud Memorystore or external provider)
- **Google Credentials**: Managed via Google Cloud Secret Manager

## Prerequisites

1. **Google Cloud Account**: Active GCP account with billing enabled
2. **Google Cloud CLI**: Installed and authenticated (`gcloud init`)
3. **Docker**: Installed for building container images
4. **Redis**: Access to a Redis instance (Cloud Memorystore or external)

## Setup Instructions

### 1. Prepare Google Cloud Project

```bash
# Set your project ID
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    secretmanager.googleapis.com
```

### 2. Create Google Cloud Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to IAM & Admin > Service Accounts
3. Create a new service account with the following roles:
   - Cloud Run Admin
   - Secret Manager Secret Accessor
   - Artifact Registry Administrator
   - Vertex AI User
4. Create a JSON key for the service account and save it as `google-credentials.json` in the project root

### 3. Configure Environment Variables

Copy the example environment file and configure:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Redis Configuration
REDIS_URL=redis://your-redis-host:6379

# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_REGION=us-central1

# Application Configuration
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### 4. Deploy to Cloud Run

#### Using PowerShell (Windows)

```powershell
# Deploy with verbose output
.\deploy-cloudrun.ps1 -Verbose

# Deploy with custom region
.\deploy-cloudrun.ps1 -Region "us-east1"

# Deploy with custom service names
.\deploy-cloudrun.ps1 -FrontendServiceName "modular-chatbot-frontend" -BackendServiceName "modular-chatbot-backend"
```

#### Using Bash (Linux/macOS)

```bash
# Deploy with verbose output
./deploy-cloudrun.sh --verbose

# Deploy with custom region
./deploy-cloudrun.sh --region us-east1

# Deploy with custom service names
./deploy-cloudrun.sh --frontend-service-name modular-chatbot-frontend --backend-service-name modular-chatbot-backend
```

#### Using Makefile

```bash
# Deploy to Cloud Run
make cloudrun-deploy

# Deploy with custom region
make cloudrun-deploy REGION=us-east1

# Deploy with verbose output
make cloudrun-deploy VERBOSE=true
```

## Deployment Process

The deployment scripts perform the following steps:

### 1. Google Cloud Setup
- Enable required APIs (Cloud Run, Cloud Build, Artifact Registry, Secret Manager)
- Create Artifact Registry repository for container images
- Create Google Cloud Secret for credentials

### 2. Build and Push Docker Images
- Build frontend Docker image (React + NGINX)
- Build backend Docker image (FastAPI + Python)
- Push images to Google Artifact Registry

### 3. Deploy Cloud Run Services
- **Frontend Service**: NGINX serving React application
  - Port: 80
  - Memory: 512Mi
  - CPU: 1
  - Max instances: 10
- **Backend Service**: FastAPI application
  - Port: 8000
  - Memory: 1Gi
  - CPU: 2
  - Max instances: 10

### 4. Configure Environment and Secrets
- Set environment variables for both services
- Configure Google credentials as secrets
- Set up Redis connection

## Accessing the Application

After deployment, the scripts will output the service URLs:

- **Frontend URL**: Access the React application
- **Backend URL**: Access the FastAPI API documentation

The frontend will automatically be configured to communicate with the backend service.

## Managing the Deployment

### Check Service Status

```bash
# Using PowerShell
.\deploy-cloudrun.ps1 -Action status

# Using Bash
./deploy-cloudrun.sh --action status

# Using Makefile
make cloudrun-status
```

### View Service Logs

```bash
# Using PowerShell
.\deploy-cloudrun.ps1 -Action logs

# Using Bash
./deploy-cloudrun.sh --action logs

# Using Makefile
make cloudrun-logs
```

### Undeploy Services

```bash
# Using PowerShell
.\deploy-cloudrun.ps1 -Action undeploy

# Using Bash
./deploy-cloudrun.sh --action undeploy

# Using Makefile
make cloudrun-undeploy
```

## Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_CLOUD_PROJECT` | Google Cloud project ID | Required |
| `GOOGLE_CLOUD_REGION` | Deployment region | `us-central1` |
| `REDIS_URL` | Redis connection URL | Required |
| `FRONTEND_SERVICE_NAME` | Frontend service name | `modular-chatbot-frontend` |
| `BACKEND_SERVICE_NAME` | Backend service name | `modular-chatbot-backend` |
| `ARTIFACT_REGISTRY_REPO` | Artifact registry repository | `modular-chatbot` |

### Service Configuration

#### Frontend Service
- **Memory**: 512Mi (configurable)
- **CPU**: 1 (configurable)
- **Max instances**: 10 (configurable)
- **Port**: 80
- **Health check**: `/`

#### Backend Service
- **Memory**: 1Gi (configurable)
- **CPU**: 2 (configurable)
- **Max instances**: 10 (configurable)
- **Port**: 8000
- **Health check**: `/health`

## Troubleshooting

### Common Issues

1. **Build Failures**
   - Ensure Docker is running
   - Check `google-credentials.json` exists in project root
   - Verify Redis configuration in `.env`

2. **Deployment Failures**
   - Check Google Cloud project billing is enabled
   - Verify required APIs are enabled
   - Ensure service account has proper permissions

3. **Service Not Starting**
   - Check service logs: `make cloudrun-logs`
   - Verify environment variables are set correctly
   - Check Redis connectivity

4. **Google Credentials Issues**
   - Verify service account has Vertex AI User role
   - Check credentials file format and content
   - Ensure Secret Manager API is enabled

### Debug Commands

```bash
# Check Google Cloud authentication
gcloud auth list

# Check enabled APIs
gcloud services list

# View Artifact Registry images
gcloud artifacts images list --repository=modular-chatbot

# Check Cloud Run services
gcloud run services list

# View specific service details
gcloud run services describe modular-chatbot-frontend
```

## Cost Optimization

### Right-Sizing Resources

Adjust memory and CPU allocation based on actual usage:

```bash
# Update frontend service with smaller resources
gcloud run services update modular-chatbot-frontend \
    --memory=256Mi \
    --cpu=1 \
    --region=us-central1

# Update backend service with optimized resources
gcloud run services update modular-chatbot-backend \
    --memory=512Mi \
    --cpu=1 \
    --region=us-central1
```

### Scaling Configuration

Configure minimum and maximum instances:

```bash
# Set minimum instances to 0 for cost savings
gcloud run services update modular-chatbot-frontend \
    --min-instances=0 \
    --max-instances=5 \
    --region=us-central1
```

## Security Considerations

1. **Secrets Management**: Google credentials are stored in Secret Manager
2. **Service Accounts**: Use least-privilege service accounts
3. **Network Security**: Cloud Run services are secure by default
4. **Environment Variables**: Sensitive data should be stored in secrets

## Monitoring and Logging

### Cloud Monitoring

Cloud Run integrates with Google Cloud Monitoring:

```bash
# View metrics in Google Cloud Console
# Navigate to: Monitoring > Cloud Run
```

### Cloud Logging

Access logs through Google Cloud Logging:

```bash
# View logs for a specific service
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=modular-chatbot-frontend"

# Stream logs in real-time
gcloud logging tail "resource.type=cloud_run_revision"
```

## Alternative Deployment Options

### Manual Deployment

If you prefer manual deployment without scripts:

1. **Build and Push Images**
   ```bash
   # Build frontend
   docker build -f frontend/Dockerfile -t us-central1-docker.pkg.dev/your-project/modular-chatbot/frontend:latest .
   
   # Build backend
   docker build -f backend/Dockerfile -t us-central1-docker.pkg.dev/your-project/modular-chatbot/backend:latest .
   
   # Push images
   docker push us-central1-docker.pkg.dev/your-project/modular-chatbot/frontend:latest
   docker push us-central1-docker.pkg.dev/your-project/modular-chatbot/backend:latest
   ```

2. **Deploy Services**
   ```bash
   # Deploy frontend
   gcloud run deploy modular-chatbot-frontend \
       --image=us-central1-docker.pkg.dev/your-project/modular-chatbot/frontend:latest \
       --platform=managed \
       --region=us-central1 \
       --port=80 \
       --memory=512Mi \
       --cpu=1 \
       --set-env-vars=REDIS_URL=redis://your-redis:6379
   
   # Deploy backend
   gcloud run deploy modular-chatbot-backend \
       --image=us-central1-docker.pkg.dev/your-project/modular-chatbot/backend:latest \
       --platform=managed \
       --region=us-central1 \
       --port=8000 \
       --memory=1Gi \
       --cpu=2 \
       --set-env-vars=REDIS_URL=redis://your-redis:6379
   ```

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review service logs: `make cloudrun-logs`
3. Verify Google Cloud project configuration
4. Ensure all prerequisites are met

## Next Steps

After successful deployment:
1. Test the application functionality
2. Set up monitoring and alerting
3. Configure custom domain (if needed)
4. Set up CI/CD pipeline for automated deployments
