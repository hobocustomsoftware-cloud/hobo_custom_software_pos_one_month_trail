# Multi-stage: build frontend (Vue) then backend (Django).
# Build context must be repo root: docker compose build backend (from project root).
# တစ်ခါတည်း frontend + backend ပါအောင် build လုပ်မယ်။

# ---- Stage 1: Vue frontend (Node 22 LTS; bookworm = Ubuntu 25.10–friendly) ----
FROM node:22-bookworm-slim AS frontend
WORKDIR /fe
COPY yp_posf/package*.json ./
ENV NODE_OPTIONS="--max-old-space-size=4096"
RUN npm cache clean --force
RUN npm install --legacy-peer-deps
COPY yp_posf/ .
ARG VITE_API_URL=/api
ARG VITE_BASE=/app/
ENV VITE_API_URL=$VITE_API_URL VITE_BASE=$VITE_BASE
RUN ls -la src/
RUN ls -la public/
RUN npm run build

# ---- Stage 2: Django backend (Debian bookworm base; Ubuntu 25.10–friendly) ----
FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gosu \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

COPY WeldingProject/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY WeldingProject/ .
# Copy Vite build: static_frontend for default; frontend_built for runtime copy (volume may override /app/static_frontend)
COPY --from=frontend /fe/dist /app/static_frontend
COPY --from=frontend /fe/dist /app/frontend_built
RUN chown -R appuser:appuser /app
# Entrypoint (runs as root): ensure /app/media/shop writable for logo upload, then run CMD as appuser
COPY WeldingProject/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
USER root

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health/').raise_for_status()" || exit 1
