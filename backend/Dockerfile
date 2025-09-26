# Multi-stage build for FastAPI backend
FROM python:3.13-slim AS builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create appuser for development
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install uv for faster dependency management
RUN pip install uv

# Set work directory
WORKDIR /app

# Create cache directory for UV and set permissions
RUN mkdir -p /home/appuser/.cache/uv && \
    chown -R appuser:appuser /home/appuser && \
    chown -R appuser:appuser /app

# Google credentials setup - for local development
# In Cloud Run, this will be provided as environment variable
COPY google-credentials.json /home/google-credentials.json
ENV GOOGLE_APPLICATION_CREDENTIALS=/home/google-credentials.json

# Switch to appuser
USER appuser

# Set UV cache directory to a writable location
ENV UV_CACHE_DIR=/tmp/uv-cache
RUN mkdir -p /tmp/uv-cache

# Copy dependency files
COPY --chown=appuser:appuser pyproject.toml ./
COPY --chown=appuser:appuser uv.lock ./

# Copy embeddings
COPY --chown=appuser:appuser infinitepay_faiss_index ./infinitepay_faiss_index

# Install dependencies including dev dependencies using uv
RUN uv sync --all-extras

# Production stage
FROM python:3.13-slim AS production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r appuser && useradd -r -g appuser appuser

# Install uv for running tests
RUN pip install uv

# Copy the virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Set work directory
WORKDIR /app

# Copy application code (specific directories to avoid overwriting .venv)
COPY app/ ./app/
COPY agents/ ./agents/
COPY models/ ./models/
COPY services/ ./services/
COPY tests/ ./tests/
COPY *.py ./
COPY pyproject.toml ./

# Copy credentials file into production container (for local development)
# In Cloud Run, this will be provided as GOOGLE_APPLICATION_CREDENTIALS_CONTENT env var
COPY google-credentials.json /home/google-credentials.json

# Create secrets directory for Cloud Run (optional)
RUN mkdir -p /secrets

# Set default credentials path for local development
# In Cloud Run, this will be overridden by the google_credentials utility
ENV GOOGLE_APPLICATION_CREDENTIALS=/home/google-credentials.json

# Copy FAISS index from builder stage
COPY --from=builder /app/infinitepay_faiss_index ./infinitepay_faiss_index

# Remove any build artifacts and cache directories
RUN rm -rf .eggs *.egg-info __pycache__ .pytest_cache

# Change ownership to appuser
RUN chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

# Expose port
EXPOSE ${PORT:-8080}

# Run the application
CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"