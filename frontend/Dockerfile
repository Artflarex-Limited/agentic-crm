# syntax=docker/dockerfile:1
# Multi-stage build for Next.js frontend
# Stage 1: Builder
FROM --platform=$BUILDPLATFORM node:20-alpine AS builder

WORKDIR /app

ARG TARGETPLATFORM
ARG BUILDPLATFORM
ARG NEXT_PUBLIC_API_URL

COPY package.json package-lock.json* ./
RUN npm install --ignore-scripts

COPY . .

ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL} NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# Stage 2: Runner
FROM node:20-alpine AS runner

WORKDIR /app

RUN addgroup --gid 1001 nodejs && \
    adduser --uid 1001 --ingroup nodejs --disabled-password nodejs

COPY --from=builder --chown=1001:1001 /app/.next/standalone/. ./
COPY --from=builder --chown=1001:1001 /app/public ./public

ENV NODE_ENV=production PORT=3000

USER nodejs

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD wget -qO- http://localhost:3000 || exit 1

EXPOSE 3000

CMD ["node", "server.js"]