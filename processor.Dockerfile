# Dockerfile para el Processor
FROM python:3.11-slim

LABEL description="Servicio de procesamiento de noticias económicas"

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY processor/requirements.txt .

# Instalar dependencias Python
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copiar código fuente
COPY processor/ ./processor/
COPY data/ ./data/

# Crear directorios necesarios
RUN mkdir -p data/raw data/processed data/aggregated

# Usuario no-root por seguridad
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Comando por defecto
CMD ["python", "-m", "processor.main"]
