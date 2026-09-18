# ============================================================
# Stage 1 — Node dependency installer and builder
# ============================================================
FROM node:22-alpine AS builder

WORKDIR /app

# Copy manifests first for layer caching
COPY package.json package-lock.json ./
RUN npm ci --frozen-lockfile

# Copy source and build
COPY . .

# VITE_API_BASE_URL will be resolved at nginx proxy level
# so we set it to relative path for browser clients
ENV VITE_API_BASE_URL=""

RUN npm run build

# ============================================================
# Stage 2 — Nginx static file server
# ============================================================
FROM nginx:1.27-alpine AS runtime

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Custom nginx config: serve SPA + proxy /api to backend
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
