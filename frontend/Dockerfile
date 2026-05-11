FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install --prefer-offline

COPY . .

ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build

RUN mkdir -p /app/public && touch /app/public/.gitkeep

FROM node:20-alpine

WORKDIR /app

RUN addgroup --gid 1001 nodejs && \
    adduser --uid 1001 --ingroup nodejs --disabled-password nodejs

COPY --from=builder --chown=1001:1001 /app/.next/standalone /app/
COPY --from=builder --chown=1001:1001 /app/.next/static /app/.next/static
COPY --from=builder --chown=1001:1001 /app/public /app/public

ENV NODE_ENV=production
ENV PORT=3000

USER nodejs

EXPOSE 3000

CMD ["node", "server.js"]