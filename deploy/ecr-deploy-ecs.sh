#!/bin/bash

# ECS Deployment after ECR push
set -e

AWS_REGION="us-east-1"
CLUSTER_NAME="my-app-cluster"
SERVICE_NAME="my-app-service"
TASK_DEFINITION="my-app-task"

echo "Deploying to ECS..."

# Update ECS service with new task definition
aws ecs update-service \
    --cluster $CLUSTER_NAME \
    --service $SERVICE_NAME \
    --force-new-deployment \
    --region $AWS_REGION

echo "ECS deployment triggered. Waiting for service to stabilize..."

# Wait for service to become stable
aws ecs wait services-stable \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --region $AWS_REGION

echo "✅ ECS deployment completed successfully!"