# Backend-only Dockerfile: no frontend build (saves disk; no Node).
# Pre-built frontend must exist at yp_posf/dist (run "npm run build" in yp_posf first),
# OR use compose/Dockerfile.unified for full build (frontend built once, shared).
# Build from one_month_trial: docker build -f WeldingProject/Dockerfile .

FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

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
# Pre-built frontend: copy from context (run "cd yp_posf && npm run build" first)
COPY yp_posf/dist /app/static_frontend
COPY yp_posf/dist /app/frontend_built
RUN chown -R appuser:appuser /app

COPY WeldingProject/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
USER root

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health/').raise_for_status()" || exit 1
