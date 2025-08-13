# HR Policy Bot - Complete System Guide

## 🚀 Overview

The HR Policy Bot is a comprehensive RAG (Retrieval-Augmented Generation) system that provides intelligent answers to HR policy questions using Carnegie Mellon University's HR documentation. The system supports multiple deployment methods and integrations.

## 🏗️ System Architecture

### Core Components
- **Document Processor**: Handles PDF, HTML, CSV, and TXT files
- **Vector Store**: FAISS-based semantic search with FastEmbed embeddings
- **LLM Integration**: GROQ API for question answering
- **Web Interface**: Flask-based REST API
- **Integrations**: Slack, Email, and Web platforms

### Key Features
- **Multi-format Support**: PDF, HTML, CSV, TXT documents
- **Smart Chunking**: Optimized document splitting for better retrieval
- **Content Categorization**: Automatic classification of HR policies
- **Multi-platform**: Web, Slack, and Email interfaces
- **Production Ready**: Docker and direct deployment options

## 📋 Prerequisites

### Required Software
- Python 3.11+
- pip
- Docker (optional, for containerized deployment)
- Git

### API Keys Required
- `GROQ_API_KEY`: For LLM question answering
- `SLACK_BOT_TOKEN`: For Slack integration (optional)
- `NGROK_AUTH_TOKEN`: For external access (optional)

## 🛠️ Local Development Setup

### 1. Clone and Setup
```bash
git clone <your-repository>
cd hr_bot
pip install -r requirements.txt
```

### 2. Environment Configuration
```bash
# Create .env file
cp .env.example .env
# Edit .env with your API keys
```

### 3. Run Locally
```bash
# Development mode
python run_app.py

# Or using module
python -m run_app
```

**Access**: http://localhost:8080

## 🔄 Vector Store Management

### Understanding the Vector Store
The vector store contains embedded representations of your HR documents, enabling semantic search and retrieval.

### Rebuilding Vector Store

#### Option 1: Using rebuild_vectorstore.py
```bash
python rebuild_vectorstore.py
```

**What happens:**
1. Loads documents from `./documents/` directory
2. Processes each document (PDF, HTML, CSV, TXT)
3. Splits into optimized chunks
4. Generates embeddings using FastEmbed
5. Stores in FAISS index at `./src/store/`

#### Option 2: Using Document Processor
```bash
python -c "
from src.core.document_processor import document_processor
document_processor.ingest_and_save_sources('./src/utils/sources.txt', './src/store')
"
```

### Vector Store Files
- `./src/store/index.faiss`: FAISS vector index
- `./src/store/index.pkl`: Document metadata and mappings
- `./tmp/model_cache/`: Cached embedding models

### When to Rebuild
- **New documents added** to `./documents/`
- **Updated source files** in `./src/utils/sources.txt`
- **Embedding model changes**
- **Vector store corruption**

## 🐳 Docker Deployment

### Building the Image
```bash
# Build with docker-compose
docker-compose build --no-cache

# Or build directly
docker build -t hr-bot:latest .
```

### Docker Architecture
- **Multi-stage build** for optimization
- **Lightweight base**: Python 3.11-slim
- **Pre-downloaded models** for faster startup
- **Production WSGI**: Gunicorn with multiple workers

### Running with Docker Compose
```bash
# Start services
docker-compose up

# Background mode
docker-compose up -d

# Stop services
docker-compose down
```

### Docker Services
- **hr-bot**: Main application (port 8080)
- **ngrok**: External access tunnel (port 4040)

### Production Configuration
```yaml
# docker-compose.yml
services:
  hr-bot:
    build: .
    ports:
      - "8080:8080"
    environment:
      - ENV_MODE=production
    volumes:
      - ./vectorstore:/app/vectorstore
```

## 🖥️ Server Deployment

### Direct Python Deployment
```bash
# SSH into your server
ssh user@your-server-ip

# Clone/transfer your code
cd ~/hr-policy-bot

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GROQ_API_KEY="your-api-key"
export ENV_MODE=production
export PORT=8080

# Run the application
python3 run_app.py
```

### Keeping It Running
```bash
# Option 1: nohup
nohup python3 run_app.py > bot.log 2>&1 &

# Option 2: screen (recommended)
screen -S hr-bot
python3 run_app.py
# Ctrl+A, D to detach

# Option 3: tmux
tmux new-session -d -s hr-bot
tmux send-keys -t hr-bot "python3 run_app.py" Enter
```

### Server Access
- **Local**: http://localhost:8080
- **External**: http://YOUR_SERVER_IP:8080
- **API Status**: http://YOUR_SERVER_IP:8080/api/status
- **Health Check**: http://YOUR_SERVER_IP:8080/health

## 🔧 Configuration

### Environment Variables
```bash
# Required
GROQ_API_KEY=your-groq-api-key

# Optional
ENV_MODE=production
PORT=8080
MAX_TOKENS=2048
LLM_TIMEOUT=30
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

### Document Sources
Edit `./src/utils/sources.txt`:
```
file, ./documents/hr-policy-1.pdf
file, ./documents/employee-handbook.html
url, https://hr.cmu.edu/policies
```

### Chunking Configuration
- **Chunk Size**: Default 1000 characters
- **Overlap**: Default 200 characters
- **Optimization**: Hierarchical splitting for better context

## 📊 API Endpoints

### Core Endpoints
- `GET /`: Web interface
- `GET /health`: Health check
- `GET /api/status`: Bot status
- `POST /api/ask`: Ask questions
- `POST /api/chat`: Chat interface

### Request Format
```json
{
  "question": "How do I request PTO?",
  "format": "web"
}
```

### Response Format
```json
{
  "answer": "Detailed answer...",
  "sources": ["source1", "source2"],
  "status": "success"
}
```

## 🔍 Troubleshooting

### Common Issues

#### 1. "Bot not ready" Error
**Cause**: Bot initialization incomplete
**Solution**: Wait for full initialization or check logs

#### 2. Vector Store Loading Failed
**Cause**: Missing or corrupted index files
**Solution**: Rebuild vector store or copy from working instance

#### 3. Port Already in Use
**Cause**: Another instance running
**Solution**: 
```bash
# Find and kill process
sudo netstat -tlnp | grep 8080
sudo kill -9 <PID>

# Or use different port
export PORT=5000
```

#### 4. Memory Issues During Rebuild
**Cause**: Large documents or insufficient RAM
**Solution**: 
- Use smaller chunk sizes
- Process documents in batches
- Increase server resources

### Log Analysis
```bash
# View real-time logs
tail -f bot.log

# Search for errors
grep "ERROR" bot.log

# Check bot status
curl http://localhost:8080/api/status
```

## 📈 Performance Optimization

### Embedding Models
- **Default**: BAAI/bge-base-en-v1.5 (768 dimensions)
- **Optimized**: Quantized models for faster inference
- **Caching**: Models cached in `/tmp/model_cache/`

### Vector Store Optimization
- **Index Type**: FAISS with AVX2/AVX512 support
- **Retrieval**: Top 15 documents for comprehensive answers
- **Chunking**: Optimized for 300ms query response time

### Production Settings
- **Workers**: 2-4 Gunicorn workers
- **Timeout**: 120 seconds for long queries
- **Preload**: Application preloaded for faster startup

## 🔐 Security Considerations

### Production Deployment
- **Non-root user**: Container runs as `appuser`
- **Environment isolation**: Virtual environment usage
- **API key protection**: Secure .env file management
- **Port restrictions**: Only necessary ports exposed

### Access Control
- **Internal access**: Server IP restrictions
- **External access**: ngrok tunneling (optional)
- **API rate limiting**: GROQ API limits enforced

## 📚 File Structure

```
hr_bot/
├── src/
│   ├── api/                 # Flask API endpoints
│   ├── core/                # Core bot functionality
│   ├── integrations/        # Slack, Email integrations
│   └── utils/               # Helper functions
├── documents/               # Source documents
├── vectorstore/             # FAISS index files
├── requirements.txt         # Python dependencies
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Multi-service setup
├── run_app.py              # Development server
├── wsgi.py                 # Production WSGI entry
└── .env                    # Environment variables
```

## 🚀 Deployment Checklist

### Pre-deployment
- [ ] API keys configured in .env
- [ ] Documents added to ./documents/
- [ ] Vector store built and tested
- [ ] Dependencies installed
- [ ] Port availability confirmed

### Docker Deployment
- [ ] Image built successfully
- [ ] Containers running without errors
- [ ] Port mappings correct
- [ ] Health checks passing
- [ ] Logs showing successful startup

### Server Deployment
- [ ] Code transferred to server
- [ ] Python environment configured
- [ ] Application running in background
- [ ] External access confirmed
- [ ] Monitoring and logging setup

## 📞 Support and Maintenance

### Regular Maintenance
- **Log rotation**: Prevent log file bloat
- **Vector store updates**: Rebuild when documents change
- **Dependency updates**: Keep packages current
- **Performance monitoring**: Track response times

### Monitoring Commands
```bash
# Check if bot is running
ps aux | grep run_app

# Monitor resource usage
top -p $(pgrep -f run_app)

# Check port status
sudo netstat -tlnp | grep 8080

# Test API endpoints
curl http://localhost:8080/health
```

### Backup Strategy
- **Code**: Git repository
- **Vector store**: Regular backups of ./src/store/
- **Configuration**: .env file backup
- **Documents**: Source document archive

---

## 🎯 Quick Start Commands

```bash
# Local development
python run_app.py

# Rebuild vector store
python rebuild_vectorstore.py

# Docker deployment
docker-compose up --build

# Server deployment
nohup python3 run_app.py > bot.log 2>&1 &
```

---

**Last Updated**: August 13, 2025  
**Version**: 2.0  
**Maintainer**: Your Team
