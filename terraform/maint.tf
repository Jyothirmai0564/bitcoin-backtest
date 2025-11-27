# terraform/main.tf
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# ECR Repository
resource "aws_ecr_repository" "trading_app" {
  name                 = "bitcoin-trading"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Environment = "production"
    Project     = "bitcoin-trading"
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "trading_cluster" {
  name = "bitcoin-trading-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Environment = "production"
  }
}

# ECS Task Definition
resource "aws_ecs_task_definition" "trading_task" {
  family                   = "bitcoin-trading"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 1024
  memory                   = 2048
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn           = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "trading-app"
      image     = "${aws_ecr_repository.trading_app.repository_url}:latest"
      essential = true
      environment = [
        { name = "ENVIRONMENT", value = "production" },
        { name = "PYTHONUNBUFFERED", value = "1" },
        { name = "LOG_LEVEL", value = "INFO" }
      ]
      secrets = [
        { name = "TELEGRAM_BOT_TOKEN", valueFrom = "${aws_secretsmanager_secret.telegram_bot_token.arn}" },
        { name = "GMAIL_USER", valueFrom = "${aws_secretsmanager_secret.gmail_user.arn}" },
        { name = "GMAIL_PASSWORD", valueFrom = "${aws_secretsmanager_secret.gmail_password.arn}" }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = "/ecs/bitcoin-trading"
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "trading-app"
        }
      }
      healthCheck = {
        command     = ["CMD-SHELL", "python -c \"import requests; print('healthy')\""]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 40
      }
    },
    {
      name      = "trading-dashboard"
      image     = "${aws_ecr_repository.trading_app.repository_url}:latest"
      essential = true
      portMappings = [
        {
          containerPort = 8501
          hostPort      = 8501
          protocol      = "tcp"
        }
      ]
      command = ["streamlit", "run", "enhanced_dashboard.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
      environment = [
        { name = "ENVIRONMENT", value = "production" },
        { name = "PYTHONUNBUFFERED", value = "1" }
      ]
      dependsOn = [
        {
          containerName = "trading-app"
          condition     = "HEALTHY"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = "/ecs/bitcoin-trading"
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "trading-dashboard"
        }
      }
    }
  ])

  tags = {
    Environment = "production"
  }
}

# ECS Service
resource "aws_ecs_service" "trading_service" {
  name            = "bitcoin-trading-service"
  cluster         = aws_ecs_cluster.trading_cluster.id
  task_definition = aws_ecs_task_definition.trading_task.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.private.*.id
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.dashboard.arn
    container_name   = "trading-dashboard"
    container_port   = 8501
  }

  depends_on = [aws_lb_listener.dashboard]

  tags = {
    Environment = "production"
  }
}

# Application Load Balancer
resource "aws_lb" "trading" {
  name               = "bitcoin-trading-lb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.lb.id]
  subnets            = aws_subnet.public.*.id

  tags = {
    Environment = "production"
  }
}

resource "aws_lb_target_group" "dashboard" {
  name        = "trading-dashboard"
  port        = 8501
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    path                = "/"
    protocol            = "HTTP"
    interval            = 30
  }

  tags = {
    Environment = "production"
  }
}

resource "aws_lb_listener" "dashboard" {
  load_balancer_arn = aws_lb.trading.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.dashboard.arn
  }
}

# Secrets Manager
resource "aws_secretsmanager_secret" "telegram_bot_token" {
  name = "telegram-bot-token"
}

resource "aws_secretsmanager_secret" "gmail_user" {
  name = "gmail-user"
}

resource "aws_secretsmanager_secret" "gmail_password" {
  name = "gmail-password"
}

# IAM Roles
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "ecsTaskExecutionRole-trading"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "ecs_task_role" {
  name = "ecsTaskRole-trading"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

# VPC
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true

  tags = {
    Name = "trading-vpc"
  }
}

# Variables
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# Outputs
output "load_balancer_url" {
  value = "http://${aws_lb.trading.dns_name}"
}

output "ecr_repository_url" {
  value = aws_ecr_repository.trading_app.repository_url
}