# ============================================================
# AI Contract Risk Analysis System — Frontend
# React + Vite + Tailwind → served via nginx
# ============================================================

FROM node:20-alpine AS build

WORKDIR /app

# Install dependencies (copy lockfile if present)
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install

# Copy full frontend source and build
COPY frontend .
RUN npm run build

# ---- Production stage ----
FROM nginx:alpine

# Custom nginx config for SPA routing + API proxy
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built React app
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget -qO- http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
