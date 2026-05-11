# syntax=docker/dockerfile:1
# Multi-stage build for Next.js frontend
# Stage 1: Builder
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build application
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build

# Stage 2: Runner
FROM node:20-alpine AS runner

WORKDIR /app

# Security: create non-root user
RUN addgroup --gid 1001 nodejs && \
    adduser --uid 1001 --ingroup nodejs --disabled-password nodejs

# Copy built application
COPY --from=builder --chown=nodejs:nodejs .next/standalone ./
COPY --from=builder --chown=nodejs:nodejs .next/static ./.next/static
COPY --from=builder --chown=nodejs:nodejs public ./public

# Set environment for standalone mode
ENV NODE_ENV=production
ENV PORT=3000

USER nodejs

EXPOSE 3000

CMD ["node", "server.js"]