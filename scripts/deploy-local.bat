@echo off
REM TheraBot Local Deployment Script for Windows
setlocal enabledelayedexpansion

echo 🚀 Starting TheraBot local deployment...

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not installed. Please install Docker Desktop first.
    exit /b 1
)

REM Check if Docker Compose is available
docker compose version >nul 2>&1
if errorlevel 1 (
    docker-compose --version >nul 2>&1
    if errorlevel 1 (
        echo ❌ Docker Compose is not installed. Please install Docker Compose first.
        exit /b 1
    )
    set COMPOSE_CMD=docker-compose
) else (
    set COMPOSE_CMD=docker compose
)

REM Check if models directory exists
if not exist "models\int8" (
    echo ❌ Models directory not found. Please ensure models\int8\ exists with your GGUF files.
    exit /b 1
)

REM Check if Modelfile exists
if not exist "models\int8\Modelfile" (
    echo ❌ Modelfile not found at models\int8\Modelfile
    exit /b 1
)

echo 📦 Building and starting containers...
%COMPOSE_CMD% up --build -d

echo ⏳ Waiting for services to be ready...
timeout /t 10 /nobreak >nul

REM Check if webapp is responding (basic check)
curl -f http://localhost:5000 >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Webapp may still be starting. Check logs with: %COMPOSE_CMD% logs -f
) else (
    echo ✅ TheraBot webapp is running at http://localhost:5000
)

echo 📊 MLflow (if enabled) will be available at http://localhost:5001
echo 🔍 View logs with: %COMPOSE_CMD% logs -f
echo 🛑 Stop with: %COMPOSE_CMD% down

echo 🎉 Deployment complete!
pause