#!/bin/bash

# TheraBot Production Deployment Script
set -e

# Configuration
REGISTRY="ghcr.io"
IMAGE_NAME="your-username/therabot"  # Update with your GitHub username
VERSION="${1:-latest}"
DOMAIN="${2:-your-domain.com}"       # Update with your domain

echo "🚀 Starting TheraBot production deployment..."
echo "📦 Image: $REGISTRY/$IMAGE_NAME:$VERSION"
echo "🌐 Domain: $DOMAIN"

# Function to deploy using different methods
deploy_docker_swarm() {
    echo "🐳 Deploying with Docker Swarm..."
    
    # Initialize swarm if not already done
    docker swarm init 2>/dev/null || true
    
    # Create production compose file
    cat > docker-compose.prod.yml << EOF
version: '3.8'

services:
  therabot-webapp:
    image: $REGISTRY/$IMAGE_NAME:$VERSION
    ports:
      - "80:5000"
    volumes:
      - ./models/int8:/app/models:ro
      - ollama-data:/root/.ollama
    environment:
      - FLASK_ENV=production
      - FLASK_DEBUG=0
    networks:
      - therabot-network
    deploy:
      replicas: 2
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  ollama-data:

networks:
  therabot-network:
    driver: overlay
EOF

    docker stack deploy -c docker-compose.prod.yml therabot
    echo " Deployed to Docker Swarm"
}

deploy_kubernetes() {
    echo "☸️  Deploying with Kubernetes..."
    
    # Create Kubernetes manifests
    mkdir -p k8s/
    
    cat > k8s/deployment.yaml << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: therabot-webapp
  labels:
    app: therabot-webapp
spec:
  replicas: 2
  selector:
    matchLabels:
      app: therabot-webapp
  template:
    metadata:
      labels:
        app: therabot-webapp
    spec:
      containers:
      - name: therabot-webapp
        image: $REGISTRY/$IMAGE_NAME:$VERSION
        ports:
        - containerPort: 5000
        env:
        - name: FLASK_ENV
          value: "production"
        - name: FLASK_DEBUG
          value: "0"
        volumeMounts:
        - name: models
          mountPath: /app/models
          readOnly: true
        livenessProbe:
          httpGet:
            path: /
            port: 5000
          initialDelaySeconds: 60
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: models
        hostPath:
          path: /path/to/models/int8  # Update this path
---
apiVersion: v1
kind: Service
metadata:
  name: therabot-webapp-service
spec:
  selector:
    app: therabot-webapp
  ports:
  - protocol: TCP
    port: 80
    targetPort: 5000
  type: LoadBalancer
EOF

    kubectl apply -f k8s/
    echo " Deployed to Kubernetes"
}

deploy_aws_ecs() {
    echo "🚀 Deploying to AWS ECS..."
    
    # Create ECS task definition
    cat > ecs-task-definition.json << EOF
{
  "family": "therabot-webapp",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::YOUR-ACCOUNT:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "therabot-webapp",
      "image": "$REGISTRY/$IMAGE_NAME:$VERSION",
      "portMappings": [
        {
          "containerPort": 5000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "FLASK_ENV",
          "value": "production"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/therabot-webapp",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
EOF

    # Register task definition and update service
    aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json
    aws ecs update-service --cluster therabot-cluster --service therabot-service --task-definition therabot-webapp
    
    echo " Deployed to AWS ECS"
}

# Check deployment method
case "${3:-docker}" in
    "swarm")
        deploy_docker_swarm
        ;;
    "kubernetes"|"k8s")
        deploy_kubernetes
        ;;
    "aws-ecs")
        deploy_aws_ecs
        ;;
    "docker"|*)
        echo "🐳 Using Docker Swarm as default deployment method"
        deploy_docker_swarm
        ;;
esac

echo "🔍 Checking deployment status..."
sleep 10

# Basic health check
if curl -f "http://$DOMAIN" > /dev/null 2>&1; then
    echo " TheraBot is live at http://$DOMAIN"
else
    echo "  Service may still be starting. Please check manually."
fi

echo "🎉 Production deployment complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Configure SSL/TLS certificates"
echo "   2. Set up monitoring and logging"
echo "   3. Configure backup strategies"
echo "   4. Review security settings"