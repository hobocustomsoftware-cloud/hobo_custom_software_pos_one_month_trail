# Multi-stage: build then Nginx (Node 22 LTS; bookworm = Ubuntu 25.10–friendly)
# Stage 1: Build frontend
FROM node:22-bookworm-slim AS build-stage
ARG VITE_API_URL=/api
ARG VITE_BASE=/app/
ENV VITE_API_URL=$VITE_API_URL VITE_BASE=$VITE_BASE
ENV NODE_OPTIONS="--max-old-space-size=4096"
WORKDIR /app
COPY package*.json ./
RUN npm cache clean --force
RUN npm install --legacy-peer-deps
COPY . .
# Pre-build verification (diagnostic: ensure src/ and public/ are present)
RUN ls -la src/
RUN ls -la public/
RUN npm run build

# Stage 2: Nginx (serve dist) + curl for healthcheck
FROM nginx:stable-alpine
RUN apk add --no-cache curl
# SPA at /app/ so copy dist into html/app/ (index.html + assets/)
COPY --from=build-stage /app/dist /usr/share/nginx/html/app
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
