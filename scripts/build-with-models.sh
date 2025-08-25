#!/bin/bash

# Build TheraBot Docker image WITH models included
set -e

echo "🚀 Building TheraBot Docker image with models included..."

# Check if models exist
if [ ! -d "models/int8" ]; then
    echo "❌ Models directory not found at models/int8/"
    echo "Please ensure you have:"
    echo "  - models/int8/Modelfile"
    echo "  - models/int8/threabot_v2.gguf (or other .gguf files)"
    exit 1
fi

if [ ! -f "models/int8/Modelfile" ]; then
    echo "❌ Modelfile not found at models/int8/Modelfile"
    exit 1
fi

# Check model file sizes
echo "📊 Model files to be included:"
ls -lh models/int8/

# Get total size
TOTAL_SIZE=$(du -sh models/int8/ | cut -f1)
echo "📦 Total model size: $TOTAL_SIZE"

# Warning about image size
echo "  Warning: Including models will create a large Docker image (~$TOTAL_SIZE + base image)"
echo "   This is recommended for distribution but not for development."
echo ""

read -p "Continue with build? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Build cancelled."
    exit 1
fi

# Build the image
echo "🔨 Building Docker image..."
cd webapp
docker build -t therabot-with-models:latest .

# Check if build succeeded
if [ $? -eq 0 ]; then
    echo " Build successful!"
    echo ""
    echo "📋 Image details:"
    docker images | grep therabot-with-models
    echo ""
    echo "🚀 To run the image:"
    echo "   docker run -p 5000:5000 therabot-with-models:latest"
    echo ""
    echo "📤 To push to registry:"
    echo "   docker tag therabot-with-models:latest your-registry/therabot:latest"
    echo "   docker push your-registry/therabot:latest"
else
    echo "❌ Build failed!"
    exit 1
fi