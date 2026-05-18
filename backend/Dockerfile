# syntax=docker/dockerfile:1
# Multi-stage build for FastAPI backend — SQLite only, single process

# ── Stage 1: Builder ───────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: Runner ────────────────────────────────────────────────────────────
FROM python:3.12-slim AS runner

WORKDIR /app

# Create non-root user for security
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

RUN mkdir -p /app/data && chown -R appuser:appgroup /app

COPY --from=builder /install /usr/local

COPY --chown=appuser:appgroup . .

USER appuser

ENV PRISMA_HOME_DIR=/app/.prisma
ENV PRISMA_BINARY_CACHE_DIR=/app/.prisma/binaries
ENV PRISMA_USE_GLOBAL_NODE=false
ENV PRISMA_USE_NODEJS_BIN=false

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()" || exit 1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]