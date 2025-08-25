# TheraBot Deployment Guide

Complete deployment guide for TheraBot using Docker, Docker Compose, and CI/CD pipelines.

## Quick Start (Local Development)

### Prerequisites
- Docker and Docker Compose installed
- Models directory with GGUF files at `models/int8/`
- Ollama Modelfile configured at `models/int8/Modelfile`

### One-Command Deployment

**Windows:**
```bash
scripts\deploy-local.bat
```

**Linux/Mac:**
```bash
./scripts/deploy-local.sh
```

### Manual Docker Compose

```bash
# Basic deployment
docker-compose up --build -d

# With MLflow tracking
docker-compose --profile mlflow up --build -d

# Production with Nginx
docker-compose --profile production up --build -d
```

## Production Deployment

### 1. Using Docker Swarm
```bash
./scripts/deploy-production.sh latest your-domain.com swarm
```

### 2. Using Kubernetes
```bash
./scripts/deploy-production.sh latest your-domain.com kubernetes
```

### 3. Using AWS ECS
```bash
./scripts/deploy-production.sh latest your-domain.com aws-ecs
```

## CI/CD Pipeline

The project includes GitHub Actions workflows for:

### Continuous Integration (`ci-cd.yml`)
- **Triggers**: Push to main/develop, Pull Requests
- **Features**:
  - Code quality checks (flake8, black, bandit)
  - Security scanning (Trivy)
  - Docker image building and pushing to GitHub Container Registry
  - Multi-architecture builds (AMD64, ARM64)
  - Automated staging/production deployments

### Model Training Pipeline (`model-training.yml`)
- **Trigger**: Manual workflow dispatch
- **Features**:
  - Automated model training with configurable parameters
  - Model evaluation and metrics tracking
  - Artifact uploading and model versioning
  - MLflow integration

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Flask environment | `production` |
| `FLASK_DEBUG` | Debug mode | `0` |
| `OLLAMA_HOST` | Ollama service host | `localhost:11434` |

### Docker Compose Profiles

| Profile | Description | Services |
|---------|-------------|----------|
| default | Basic webapp only | webapp |
| `mlflow` | Include MLflow tracking | webapp, mlflow-server |
| `production` | Full production setup | webapp, nginx, mlflow-server |

### Volume Mounts

```yaml
volumes:
  - ./models/int8:/app/models:ro          # Model files (read-only)
  - ollama-data:/root/.ollama             # Ollama data persistence
  - ./mlruns:/mlflow/mlruns               # MLflow experiments
```

## Health Monitoring

### Health Check Script
```bash
# Basic health check
./scripts/health-check.sh

# Verbose output with system info
./scripts/health-check.sh -v

# Custom URL and timeout
./scripts/health-check.sh -u http://your-domain.com -t 15
```

### Built-in Health Endpoints

- **Webapp**: `GET /` - Main application health
- **Docker**: Built-in health check with curl
- **Nginx**: `GET /health` - Load balancer health

## Security

### Container Security
- Non-root user execution
- Read-only model mounts
- Security scanning with Trivy
- Minimal base images (slim/alpine)

### Network Security
- Rate limiting via Nginx
- Security headers (XSS, CSRF protection)
- Internal network isolation
- HTTPS-ready configuration

### Model Security
- Crisis detection and safety protocols
- Input validation and sanitization
- Logging and audit trails

## Scaling

### Horizontal Scaling
```bash
# Scale webapp containers
docker-compose up --scale therabot-webapp=3 -d

# Docker Swarm scaling
docker service scale therabot_therabot-webapp=3
```

### Resource Limits
```yaml
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 2G
    reservations:
      cpus: '0.5'
      memory: 1G
```

## Troubleshooting

### Common Issues

1. **Container fails to start**
   ```bash
   docker-compose logs -f therabot-webapp
   ```

2. **Model not loading**
   - Check Modelfile exists at `models/int8/Modelfile`
   - Verify GGUF files are present
   - Check Ollama logs: `docker-compose logs -f therabot-webapp | grep ollama`

3. **Port conflicts**
   - Change ports in `docker-compose.yml`
   - Check for running services: `netstat -tulpn | grep :5000`

4. **Memory issues**
   - Increase Docker memory limits
   - Monitor usage: `docker stats`

### Log Management
```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f therabot-webapp

# Export logs
docker-compose logs --no-color > therabot.log
```

## Monitoring and Observability

### MLflow Integration
- Model experiment tracking
- Performance metrics dashboard
- Model versioning and comparison
- Available at: `http://localhost:5001`

### Metrics Collection
- Container health and resource usage
- Response times and error rates
- Model inference metrics
- Crisis detection alerts

## Backup and Recovery

### Data Persistence
```bash
# Backup Ollama data
docker run --rm -v therabot_ollama-data:/data -v $(pwd):/backup alpine tar czf /backup/ollama-backup.tar.gz /data

# Backup MLflow data
cp -r ./mlruns ./backups/mlruns-$(date +%Y%m%d)
```

### Disaster Recovery
```bash
# Restore from backup
docker-compose down
docker run --rm -v therabot_ollama-data:/data -v $(pwd):/backup alpine tar xzf /backup/ollama-backup.tar.gz -C /
docker-compose up -d
```

## Performance Optimization

### Model Optimization
- Use quantized models (INT8/INT4)
- GPU acceleration when available
- Model caching and persistence

### Container Optimization
- Multi-stage builds for smaller images
- Layer caching optimization
- Resource limit tuning

### Network Optimization
- Nginx caching and compression
- CDN integration for static assets
- Connection pooling and keep-alive

## Support

For deployment issues:
1. Check the troubleshooting section
2. Run health check script
3. Review container logs
4. Check system resources
5. Verify model files and configuration