#!/bin/bash

# Start TheraBot services with proper port configuration
set -e

echo "🚀 Starting TheraBot Services with Port Configuration"
echo "===================================================="

# Kill any existing processes on the ports we want to use
echo "🧹 Cleaning up existing processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:8002 | xargs kill -9 2>/dev/null || true

echo "📋 Port Configuration:"
echo "  TheraBot Webapp: http://localhost:8000"
echo "  MLflow Server:   http://localhost:8002"
echo ""

# Start with Docker Compose
echo "🐳 Starting services with Docker Compose..."
docker-compose down 2>/dev/null || true
docker-compose up -d

echo " Waiting for services to start..."
sleep 10

# Check TheraBot webapp
echo "🔍 Checking TheraBot webapp..."
if curl -f http://localhost:8000 > /dev/null 2>&1; then
    echo " TheraBot webapp is running at http://localhost:8000"
else
    echo "  TheraBot webapp may still be starting..."
fi

# Check if MLflow profile is running
if docker-compose --profile mlflow ps | grep mlflow-server > /dev/null 2>&1; then
    echo "🔍 Checking MLflow server..."
    if curl -f http://localhost:8002 > /dev/null 2>&1; then
        echo " MLflow server is running at http://localhost:8002"
    else
        echo "  MLflow server may still be starting..."
    fi
else
    echo "  MLflow server not started (use --profile mlflow to enable)"
fi

echo ""
echo "🎉 Services started successfully!"
echo ""
echo "🌐 Access points:"
echo "  TheraBot Chat:     http://localhost:8000"
echo "  MLflow Dashboard:  http://localhost:8002 (if enabled)"
echo ""
echo "📊 To run evaluations:"
echo "  ./scripts/run_evaluation.sh"
echo ""
echo "🛑 To stop services:"
echo "  docker-compose down"