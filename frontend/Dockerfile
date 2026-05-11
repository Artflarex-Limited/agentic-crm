# syntax=docker/dockerfile:1
# Multi-stage build for Next.js frontend
# Stage 1: Builder
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build application
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build

# Stage 2: Runner
FROM node:20-alpine AS runner

WORKDIR /app

RUN addgroup --gid 1001 nodejs && \
    adduser --uid 1001 --ingroup nodejs --disabled-password nodejs

COPY --from=builder --chown=1001:1001 .next/standalone ./
COPY --from=builder --chown=1001:1001 .next/static ./.next/static
COPY --from=builder --chown=1001:1001 public ./public 2>/dev/null || true

# Set environment for standalone mode
ENV NODE_ENV=production
ENV PORT=3000

USER nodejs

EXPOSE 3000

CMD ["node", "server.js"]