# ── Stage 1: dependency installer ────────────────────────────────────────────
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --only=production


# ── Stage 2: builder ──────────────────────────────────────────────────────────
FROM node:20-alpine AS builder
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# NEXT_PUBLIC_ vars are baked into the JS bundle at build time.
# Use localhost:8000 so the browser (running outside Docker) can reach the backend
# via the host port mapping 0.0.0.0:8000->8000.
ENV NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

RUN npm run build


# ── Stage 3: minimal runtime ──────────────────────────────────────────────────
FROM node:20-alpine AS runtime

RUN addgroup -S vectorhire && adduser -S vectorhire -G vectorhire
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
# Override Docker's default HOSTNAME (container ID) so Next.js standalone
# server binds to 0.0.0.0 (all interfaces) instead of the container's IP.
# Without this, healthchecks inside the container fail because localhost
# (127.0.0.1) is not the interface Next.js is listening on.
ENV HOSTNAME=0.0.0.0

COPY --from=builder --chown=vectorhire:vectorhire /app/.next/standalone ./
COPY --from=builder --chown=vectorhire:vectorhire /app/.next/static ./.next/static
COPY --from=builder --chown=vectorhire:vectorhire /app/public ./public

USER vectorhire
EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000', r => process.exit(r.statusCode < 400 ? 0 : 1)).on('error', () => process.exit(1))"

CMD ["node", "server.js"]
