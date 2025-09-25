#!/bin/bash

# Script to set up Google credentials for Kubernetes
# This script encodes the google-credentials.json file and updates the Kubernetes secret

echo "Setting up Google credentials for Kubernetes deployment..."

# Check if google-credentials.json exists in the backend directory
CREDENTIALS_PATH="backend/google-credentials.json"
if [ ! -f "$CREDENTIALS_PATH" ]; then
    echo "❌ Error: google-credentials.json not found at $CREDENTIALS_PATH"
    echo "Please make sure the file exists in the backend directory."
    exit 1
fi

# Read and encode the credentials file
echo "📖 Reading and encoding google-credentials.json..."
ENCODED_CREDENTIALS=$(cat "$CREDENTIALS_PATH" | base64 -w 0)

# Update the secrets.yaml file
echo "🔄 Updating secrets.yaml with encoded credentials..."
SECRETS_PATH="k8s/secrets.yaml"
if [ ! -f "$SECRETS_PATH" ]; then
    echo "❌ Error: secrets.yaml not found at $SECRETS_PATH"
    exit 1
fi

# Read the current secrets file
SECRETS_CONTENT=$(cat "$SECRETS_PATH")

# Replace the placeholder with the actual encoded credentials
UPDATED_CONTENT=$(echo "$SECRETS_CONTENT" | sed "s/GOOGLE_APPLICATION_CREDENTIALS_CONTENT: your-service-account-json-base64-encoded/GOOGLE_APPLICATION_CREDENTIALS_CONTENT: $ENCODED_CREDENTIALS/")

# Write back to the file
echo "$UPDATED_CONTENT" > "$SECRETS_PATH"

echo "✅ Google credentials have been successfully encoded and added to secrets.yaml"
echo "📄 The credentials file at $CREDENTIALS_PATH has been encoded and stored in the Kubernetes secret."
echo ""
echo "🚀 Next steps:"
echo "1. Apply the secret to your cluster: kubectl apply -f k8s/secrets.yaml"
echo "2. Deploy the backend: kubectl apply -f k8s/backend-deployment.yaml"
echo "3. Check the deployment: kubectl get pods -n modular-chatbot"
