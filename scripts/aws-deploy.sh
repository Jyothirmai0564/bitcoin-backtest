#!/bin/bash
# scripts/aws-deploy.sh

set -e

echo "🚀 Starting AWS deployment..."

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not installed. Please install it first."
    exit 1
fi

# Check if logged in
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ Not logged into AWS. Please run 'aws configure'"
    exit 1
fi

# Build and push
echo "📦 Building and pushing Docker image..."
make aws-build
make aws-push

# Deploy
echo "🚀 Deploying to ECS..."
make aws-deploy

# Wait for deployment
echo "⏳ Waiting for deployment to complete..."
sleep 30

# Get URL
echo "🌐 Your application is deployed at:"
make aws-url

echo "✅ Deployment completed!"