# ---- Build Stage ----
FROM node:20-slim AS builder

WORKDIR /app

# ルートの依存関係
COPY package*.json ./
RUN npm install

# クライアントの依存関係とビルド
COPY client/package*.json ./client/
RUN cd client && npm install
COPY client/ ./client/

# サーバーのソースとビルド
COPY tsconfig.json ./
COPY src/ ./src/
RUN npm run build

# ---- Run Stage ----
FROM node:20-slim

# 実行環境の構築
ENV NODE_ENV=production
WORKDIR /app

COPY package*.json ./
RUN npm install --omit=dev

# ビルド成果物のコピー
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/client/dist ./client/dist
COPY public/ ./public/

# ポート設定
EXPOSE 8080

# サーバー起動
CMD ["node", "dist/server.js"]
