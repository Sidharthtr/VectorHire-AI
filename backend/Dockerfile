# ── Stage 1: dependency builder ───────────────────────────────────────────────
# Install Python deps in a separate layer so Docker cache works:
# code changes don't re-download packages.
FROM python:3.11-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# ── Stage 2: runtime image ────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# Runtime system deps only (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root user for security
RUN useradd -m -u 1000 vectorhire
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Persistent data directories (mounted as Docker volumes in production)
RUN mkdir -p app/data/chroma app/data/resumes app/data && \
    chown -R vectorhire:vectorhire app/data

USER vectorhire

# Copy application code
COPY --chown=vectorhire:vectorhire app/ ./app/
COPY --chown=vectorhire:vectorhire alembic/ ./alembic/
COPY --chown=vectorhire:vectorhire alembic.ini ./

EXPOSE 8000

# Health check — Docker marks container unhealthy if this fails
# start-period=90s: gives alembic + uvicorn bind time before checks begin
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=5 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run DB migrations then start server
# --workers 2: two uvicorn processes, each handles requests independently
CMD alembic upgrade head && \
    uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --workers 2 \
        --log-level info
