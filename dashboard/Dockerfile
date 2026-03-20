# ---- Build Stage ----
FROM node:22-slim AS builder

WORKDIR /app

# Dependency installation
COPY package*.json ./
RUN npm install

# Build
COPY src/ ./src/
COPY static/ ./static/
COPY svelte.config.js ./
COPY tsconfig.json ./
COPY vite.config.ts ./
RUN npm run build

# ---- Run Stage ----
FROM node:22-slim

ENV NODE_ENV=production
WORKDIR /app

COPY --from=builder /app/package*.json ./
RUN npm install --omit=dev

# Copy build artifacts
COPY --from=builder /app/build ./build

# Port setting
EXPOSE 8080
ENV PORT=8080

# Start server (SvelteKit adapter-node default entry point is build/index.js or just build)
CMD ["node", "build"]
