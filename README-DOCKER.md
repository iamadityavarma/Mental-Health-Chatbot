# Docker Deployment with Models Included

The Dockerfile now includes the .gguf model files directly in the image, making it completely self-contained for deployment to other computers.

## Building the Image

### Option 1: Automated Build Script

**Windows:**
```bash
scripts\build-with-models.bat
```

**Linux/Mac:**
```bash
./scripts/build-with-models.sh
```

### Option 2: Manual Build

```bash
cd webapp
docker build -t therabot-with-models:latest .
```

## What Gets Included

The Docker image will contain:
-  Python Flask webapp
-  All Python dependencies
-  Ollama service
-  **Your .gguf model files** (from `models/int8/`)
-  **Your Modelfile configuration**
-  Complete safety protocols and crisis detection

## Image Size Considerations

 **Important**: Including .gguf files makes the image large (typically 1-4GB depending on your model size)

**Trade-offs:**
-  **Pros**: Self-contained, works on any computer with Docker
-  **Cons**: Large image size, slower to build/push/pull

## Deployment to Other Computers

### 1. Push to Docker Registry (Recommended)

```bash
# Tag for your registry
docker tag therabot-with-models:latest your-dockerhub/therabot:latest

# Push to registry
docker push your-dockerhub/therabot:latest

# On other computer, just pull and run
docker run -p 5000:5000 your-dockerhub/therabot:latest
```

### 2. Export/Import Image Files

```bash
# Export image to tar file
docker save therabot-with-models:latest > therabot-complete.tar

# Copy therabot-complete.tar to other computer
# Then import on other computer:
docker load < therabot-complete.tar
docker run -p 5000:5000 therabot-with-models:latest
```

### 3. Using Docker Compose (Recommended)

Create this `docker-compose.yml` on the target computer:

```yaml
version: '3.8'
services:
  therabot:
    image: your-dockerhub/therabot:latest  # or therabot-with-models:latest if local
    ports:
      - "5000:5000"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/"]
      interval: 30s
      timeout: 10s
      retries: 3
```

Then run: `docker-compose up -d`

## Verification

After deployment on the new computer:

```bash
# Check if container is running
docker ps

# Check webapp health
curl http://localhost:5000

# View logs
docker logs [container-name]

# Check model is loaded
docker exec [container-name] ollama list
```

## Benefits of This Approach

1. **Complete Self-Containment**: No need to transfer model files separately
2. **Consistent Environment**: Same Python versions, dependencies, and configuration everywhere
3. **Easy Distribution**: Single image contains everything needed
4. **Version Control**: Each image build captures a specific model + code version
5. **No Host Dependencies**: Target computer only needs Docker

## Alternative Approaches

If image size is a concern, you can also:

1. **Hybrid Approach**: Keep base image small, download models at runtime
2. **Multi-Stage Build**: Separate model storage from runtime
3. **External Storage**: Mount models from cloud storage or network drives

The current setup prioritizes **ease of deployment** over image size, making it perfect for distributing your TheraBot to other computers without requiring them to have the model files locally.