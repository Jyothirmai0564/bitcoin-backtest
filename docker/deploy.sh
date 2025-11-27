#!/bin/bash

# Bitcoin Trading System Deployment Script
echo "🚀 Starting Bitcoin Trading System Deployment..."

# Build Docker image
echo "📦 Building Docker image..."
docker-compose build

# Start services
echo "🔄 Starting services..."
docker-compose up -d

# Check if services are running
echo "🔍 Checking services..."
docker-compose ps

# Show logs
echo "📋 Showing recent logs..."
docker-compose logs --tail=20

echo "✅ Deployment completed!"
echo "📊 Dashboard available at: http://localhost:8502"
echo "🤖 Trading app running on: http://localhost:8501"