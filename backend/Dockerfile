# syntax=docker/dockerfile:1
# Multi-stage build for FastAPI backend

# ── Stage 1: Prisma generator ──────────────────────────────────────────────────
FROM python:3.12-slim AS prisma-generator

WORKDIR /app

# Copy schema before installing prisma (needed for prisma generate)
COPY prisma/schema.prisma ./prisma/schema.prisma

# Prisma CLI needs nodejs + libatomic1 to download its embedded binary
RUN apt-get update && apt-get install -y --no-install-recommends \
        nodejs npm libatomic1 \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir prisma \
    && prisma generate \
    && apt-get remove -y nodejs npm && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# ── Stage 2: Builder ───────────────────────────────────────────────────────────
FROM --platform=$BUILDPLATFORM python:3.12-slim AS builder

ARG TARGETPLATFORM
ARG BUILDPLATFORM

WORKDIR /app

RUN echo "Building for $TARGETPLATFORM"

RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 3: Runner ────────────────────────────────────────────────────────────
FROM python:3.12-slim AS runner

WORKDIR /app

RUN mkdir -p /app/data

RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

# Install Python deps
COPY --from=builder /install /usr/local

# Copy generated Prisma client from prisma-generator stage
COPY --from=prisma-generator /app/app/generated ./app/generated

# Copy application code
COPY --chown=appuser:appgroup . .

# Non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()" || exit 1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]