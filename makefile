# Makefile
.PHONY: aws-init aws-infra aws-build aws-push aws-deploy aws-logs aws-destroy aws-secrets

# AWS Configuration
AWS_ACCOUNT := $(shell aws sts get-caller-identity --query Account --output text)
AWS_REGION := us-east-1
ECR_URL := $(AWS_ACCOUNT).dkr.ecr.$(AWS_REGION).amazonaws.com/bitcoin-trading

# Initialize AWS setup
aws-init:
	@echo "🚀 Initializing AWS deployment..."
	aws configure
	@echo "✅ AWS CLI configured"

# Deploy infrastructure with Terraform
aws-infra:
	@echo "🏗️ Deploying AWS infrastructure..."
	cd terraform && terraform init
	cd terraform && terraform apply -auto-approve
	@echo "✅ Infrastructure deployed"

# Build Docker image
aws-build:
	@echo "📦 Building Docker image..."
	docker build -t bitcoin-trading:latest .
	docker tag bitcoin-trading:latest $(ECR_URL):latest
	@echo "✅ Image built and tagged"

# Push to ECR
aws-push:
	@echo "📤 Pushing to ECR..."
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(ECR_URL)
	docker push $(ECR_URL):latest
	@echo "✅ Image pushed to ECR"

# Deploy to ECS
aws-deploy:
	@echo "🚀 Deploying to ECS..."
	aws ecs update-service --cluster bitcoin-trading-cluster --service bitcoin-trading-service --force-new-deployment
	@echo "✅ Deployment triggered"

# View logs
aws-logs:
	@echo "📋 Showing logs..."
	@echo "Trading App:"
	aws logs tail /ecs/bitcoin-trading --log-stream-name-prefix trading-app --follow
	@echo "Trading Dashboard:"
	aws logs tail /ecs/bitcoin-trading --log-stream-name-prefix trading-dashboard --follow

# Set secrets in AWS Secrets Manager
aws-secrets:
	@echo "🔐 Setting up secrets..."
	aws secretsmanager put-secret-value --secret-id telegram-bot-token --secret-string "$$TELEGRAM_BOT_TOKEN"
	aws secretsmanager put-secret-value --secret-id gmail-user --secret-string "$$GMAIL_USER"
	aws secretsmanager put-secret-value --secret-id gmail-password --secret-string "$$GMAIL_PASSWORD"
	@echo "✅ Secrets stored"

# Full deployment pipeline
aws-full-deploy: aws-build aws-push aws-deploy
	@echo "🎉 Full deployment completed! Your app will be available at:"
	@cd terraform && terraform output load_balancer_url

# Destroy infrastructure
aws-destroy:
	@echo "🗑️ Destroying infrastructure..."
	cd terraform && terraform destroy -auto-approve
	@echo "✅ Infrastructure destroyed"

# Get application URL
aws-url:
	@cd terraform && terraform output load_balancer_url

# Check ECS service status
aws-status:
	@echo "🔍 Checking service status..."
	aws ecs describe-services --cluster bitcoin-trading-cluster --services bitcoin-trading-service

# Run one-off tasks (like backtest)
aws-run-backtest:
	@echo "🤖 Running backtest in AWS..."
	aws ecs run-task --cluster bitcoin-trading-cluster \
		--task-definition bitcoin-trading \
		--launch-type FARGATE \
		--network-configuration "awsvpcConfiguration={subnets=[$(shell cd terraform && terraform output -raw subnet_ids)],securityGroups=[$(shell cd terraform && terraform output -raw security_group_ids)]}" \
		--overrides '{"containerOverrides": [{"name": "trading-app", "command": ["python", "optimized_backtest.py"]}]}'

# Local development (for reference)
dev:
	docker-compose up -d

local-logs:
	docker-compose logs -f

local-stop:
	docker-compose down