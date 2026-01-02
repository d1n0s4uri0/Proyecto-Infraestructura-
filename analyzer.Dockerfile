# Dockerfile para el Analyzer/API
FROM python:3.11-slim

LABEL maintainer="juan.jose.paredes@univalle.edu.co"
LABEL description="Servicio de análisis y API REST"

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY analyzer/requirements.txt .

# Instalar dependencias Python
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copiar código fuente
COPY analyzer/ ./analyzer/
COPY data/ ./data/

# Crear directorios necesarios
RUN mkdir -p data/aggregated data/aggregated/plots

# Usuario no-root por seguridad
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Exponer puerto de la API
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/v1/health')"

# Comando por defecto
CMD ["python", "-m", "analyzer.main"]
