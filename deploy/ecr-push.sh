#!/bin/bash

# Configuration
AWS_REGION="us-east-1"
ECR_REPO_NAME="my-app"
IMAGE_TAG="latest"

set -e

echo "Starting ECR deployment process..."

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "AWS Account ID: $AWS_ACCOUNT_ID"

# ECR repository URI
ECR_REPOSITORY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}"
echo "ECR Repository: $ECR_REPOSITORY"

# Check if repository exists, create if it doesn't
if ! aws ecr describe-repositories --repository-names $ECR_REPO_NAME --region $AWS_REGION > /dev/null 2>&1; then
    echo "Creating ECR repository: $ECR_REPO_NAME"
    aws ecr create-repository --repository-name $ECR_REPO_NAME --region $AWS_REGION
fi

# Login to ECR
echo "Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPOSITORY

# Build Docker image
echo "Building Docker image..."
docker build -f Dockerfile.prod -t ${ECR_REPO_NAME}:${IMAGE_TAG} .

# Tag image for ECR
echo "Tagging image for ECR..."
docker tag ${ECR_REPO_NAME}:${IMAGE_TAG} ${ECR_REPOSITORY}:${IMAGE_TAG}

# Optional: Tag with git commit SHA for better versioning
GIT_SHA=$(git rev-parse --short HEAD)
docker tag ${ECR_REPO_NAME}:${IMAGE_TAG} ${ECR_REPOSITORY}:${GIT_SHA}

# Push to ECR
echo "Pushing image to ECR..."
docker push ${ECR_REPOSITORY}:${IMAGE_TAG}
docker push ${ECR_REPOSITORY}:${GIT_SHA}

# List images in repository
echo "Listing images in ECR repository:"
aws ecr list-images --repository-name $ECR_REPO_NAME --region $AWS_REGION

echo "✅ ECR deployment completed successfully!"
echo "📦 Image URI: ${ECR_REPOSITORY}:${IMAGE_TAG}"