# ULTRA LIGHTWEIGHT DOCKERFILE - Target: Under 1GB
# ========================================================
# STRATEGY: Multi-stage build + minimal dependencies + CPU-only + cache optimization

# STAGE 1: BUILD STAGE - Install all dependencies efficiently
FROM python:3.11-slim as builder

# Set environment variables for build optimization
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Install only essential build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create virtual environment for isolation
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install wheel for faster builds
RUN pip install --upgrade pip setuptools wheel

# Copy standard requirements file
COPY requirements.txt .

# Install optimized dependencies
RUN pip install --no-cache-dir -r requirements.txt
# Remove PyTorch if it gets installed as a dependency (separate step for better error handling)
RUN pip uninstall -y torch torchvision torchaudio || echo "PyTorch not installed, skipping uninstall"

# Create and prepare model cache directory
RUN mkdir -p /tmp/model_cache
WORKDIR /tmp/model_cache

# Print Python and pip versions for debugging
RUN python --version && pip --version

# Copy model caching script
COPY cache_model.py /app/
WORKDIR /app

# Pre-download the tiny embedding model
RUN python cache_model.py

# STAGE 2: FINAL SLIM IMAGE - Copy only what's needed
FROM python:3.11-slim

# Install curl for healthcheck and debugging tools
RUN apt-get update && apt-get install -y \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Install psutil for debugging
RUN pip install psutil

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/venv/bin:$PATH"
ENV HF_HUB_DISABLE_SYMLINKS_WARNING=1

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy model cache
COPY --from=builder /tmp/model_cache /tmp/model_cache

# Set work directory
WORKDIR /app

# Copy environment variables file
COPY .env .env

# Copy only essential application files
COPY run_app.py .
COPY src/ ./src/
COPY documents/ ./documents/
# Include debug tools
COPY debug_retrieval.py .
# Create vectorstore directory if it doesn't exist
RUN mkdir -p ./vectorstore

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8080

# Add healthcheck using $PORT
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

# # Run the application
# CMD ["python", "run_app.py"]

# In the builder stage, add:
RUN pip install gunicorn

# At the bottom, change CMD to:
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "120", "src.api.app_with_integrations:app"]
