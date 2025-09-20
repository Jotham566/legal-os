# syntax=docker/dockerfile:1.7

# --- Builder: install dependencies and build wheels ---
FROM python:3.12-slim AS builder
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

# System deps for building some wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy pyproject and lock (if present) first for better cache usage
COPY pyproject.toml .
# If you have poetry.lock, uncomment the next line to leverage caching
# COPY poetry.lock .

# Use pip to install via PEP 517 build, without dev deps
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install poetry \
    && POETRY_VIRTUALENVS_CREATE=false poetry install --no-interaction --no-ansi --only main

# Copy source code
COPY src ./src
COPY README.md .

# --- Final minimal runtime image ---
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

# Create non-root user
RUN useradd -m appuser

# Copy virtual environment and app code from builder
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app /app

ENV PATH="/opt/venv/bin:$PATH"

# Expose the default port
EXPOSE 8000

# Healthcheck hitting liveness endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://127.0.0.1:8000/health/live || exit 1

# Run as non-root
USER appuser

# Default command: uvicorn
CMD ["uvicorn", "legal_os.main:app", "--host", "0.0.0.0", "--port", "8000"]
