@echo off
REM Start TheraBot services with proper port configuration
setlocal enabledelayedexpansion

echo 🚀 Starting TheraBot Services with Port Configuration
echo ====================================================

REM Kill any existing processes on the ports we want to use
echo 🧹 Cleaning up existing processes...
netstat -ano | findstr :8000 | for /f "tokens=5" %%a in ('more') do (
    taskkill /f /pid %%a >nul 2>&1
)
netstat -ano | findstr :8002 | for /f "tokens=5" %%a in ('more') do (
    taskkill /f /pid %%a >nul 2>&1
)

echo 📋 Port Configuration:
echo   TheraBot Webapp: http://localhost:8000
echo   MLflow Server:   http://localhost:8002
echo.

REM Start with Docker Compose
echo 🐳 Starting services with Docker Compose...
docker-compose down >nul 2>&1
docker-compose up -d

echo ⏳ Waiting for services to start...
timeout /t 10 /nobreak >nul

REM Check TheraBot webapp
echo 🔍 Checking TheraBot webapp...
curl -f http://localhost:8000 >nul 2>&1
if errorlevel 1 (
    echo ⚠️  TheraBot webapp may still be starting...
) else (
    echo ✅ TheraBot webapp is running at http://localhost:8000
)

REM Check MLflow (if running)
docker-compose ps | findstr mlflow-server >nul 2>&1
if not errorlevel 1 (
    echo 🔍 Checking MLflow server...
    curl -f http://localhost:8002 >nul 2>&1
    if errorlevel 1 (
        echo ⚠️  MLflow server may still be starting...
    ) else (
        echo ✅ MLflow server is running at http://localhost:8002
    )
) else (
    echo ℹ️  MLflow server not started (use --profile mlflow to enable^)
)

echo.
echo 🎉 Services started successfully!
echo.
echo 🌐 Access points:
echo   TheraBot Chat:     http://localhost:8000
echo   MLflow Dashboard:  http://localhost:8002 (if enabled^)
echo.
echo 📊 To run evaluations:
echo   scripts\run_evaluation.bat
echo.
echo 🛑 To stop services:
echo   docker-compose down

pause