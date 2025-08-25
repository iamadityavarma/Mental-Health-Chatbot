#!/bin/bash

# TheraBot Local Deployment Script
set -e

echo "🚀 Starting TheraBot local deployment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Function to use docker compose or docker-compose
docker_compose_cmd() {
    if docker compose version &> /dev/null; then
        docker compose "$@"
    else
        docker-compose "$@"
    fi
}

# Check if models directory exists
if [ ! -d "models/int8" ]; then
    echo "❌ Models directory not found. Please ensure models/int8/ exists with your GGUF files."
    exit 1
fi

# Check if Modelfile exists
if [ ! -f "models/int8/Modelfile" ]; then
    echo "❌ Modelfile not found at models/int8/Modelfile"
    exit 1
fi

echo "📦 Building and starting containers..."
docker_compose_cmd up --build -d

echo " Waiting for services to be ready..."
sleep 10

# Check if webapp is healthy
if curl -f http://localhost:5000 > /dev/null 2>&1; then
    echo " TheraBot webapp is running at http://localhost:5000"
else
    echo "  Webapp may still be starting. Check logs with: docker-compose logs -f"
fi

echo "📊 MLflow (if enabled) will be available at http://localhost:5001"
echo "🔍 View logs with: docker-compose logs -f"
echo "🛑 Stop with: docker-compose down"

echo "🎉 Deployment complete!"