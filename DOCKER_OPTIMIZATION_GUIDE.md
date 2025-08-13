# Docker Optimization Guide

## Image Size Optimization Results

| Version | Size | Description |
|---------|------|-------------|
| Original | ~9GB | Full build with PyTorch and large models |
| Optimized | <1GB | Lightweight with FastEmbed and minimal dependencies |

## Key Optimizations Applied

1. **Multi-Stage Build**
   - Builder stage installs all dependencies
   - Final image only contains runtime essentials
   - Reduced size by eliminating build tools

2. **Dependency Optimization**
   - Replaced PyTorch with lightweight alternatives
   - Used FastEmbed instead of sentence-transformers
   - Selective package installation

3. **Embedding Improvements**
   - Switched to FastEmbed with tiny model
   - Cached model in Docker build
   - Model size reduced from 500MB+ to <50MB

4. **Container Management**
   - Added healthcheck endpoint and Docker healthcheck
   - Created convenience scripts for building and running
   - Optimized for production deployment

## How to Build and Run

### Windows
```bash
# Option 1: Using script
docker-build-run.bat

# Option 2: Manual commands
docker build -t hr-bot:latest .
docker run -d --name hr-bot -p 8080:8080 -e GROQ_API_KEY="%GROQ_API_KEY%" hr-bot:latest
```

### Linux/Mac
```bash
# Option 1: Using script
chmod +x docker-build-run.sh
./docker-build-run.sh

# Option 2: Manual commands
docker build -t hr-bot:latest .
docker run -d --name hr-bot -p 8080:8080 -e GROQ_API_KEY="$GROQ_API_KEY" hr-bot:latest
```

## Monitoring and Maintenance

- **Health Check**: The container includes a health endpoint at `/health`
- **Logs**: View logs with `docker logs -f hr-bot`
- **Resource Usage**: Monitor with `docker stats hr-bot`

## Troubleshooting

If the Docker build fails:
1. Check requirements.docker.txt for compatibility
2. Ensure FastEmbed is properly installed
3. Verify file paths in the Dockerfile
4. Check GROQ API key is properly set in environment
