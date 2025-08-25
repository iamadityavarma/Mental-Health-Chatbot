@echo off
REM Build TheraBot Docker image WITH models included (Windows)
setlocal enabledelayedexpansion

echo 🚀 Building TheraBot Docker image with models included...

REM Check if models exist
if not exist "models\int8" (
    echo ❌ Models directory not found at models\int8\
    echo Please ensure you have:
    echo   - models\int8\Modelfile
    echo   - models\int8\threabot_v2.gguf (or other .gguf files^)
    exit /b 1
)

if not exist "models\int8\Modelfile" (
    echo ❌ Modelfile not found at models\int8\Modelfile
    exit /b 1
)

REM Check model files
echo 📊 Model files to be included:
dir /s models\int8\

REM Warning about image size
echo ⚠️  Warning: Including models will create a large Docker image
echo    This is recommended for distribution but not for development.
echo.

set /p CONTINUE="Continue with build? (y/N) "
if /i not "%CONTINUE%"=="y" (
    echo Build cancelled.
    exit /b 1
)

REM Build the image
echo 🔨 Building Docker image...
cd webapp
docker build -t therabot-with-models:latest .

if errorlevel 1 (
    echo ❌ Build failed!
    exit /b 1
) else (
    echo ✅ Build successful!
    echo.
    echo 📋 Image details:
    docker images | findstr therabot-with-models
    echo.
    echo 🚀 To run the image:
    echo    docker run -p 5000:5000 therabot-with-models:latest
    echo.
    echo 📤 To push to registry:
    echo    docker tag therabot-with-models:latest your-registry/therabot:latest
    echo    docker push your-registry/therabot:latest
)

pause