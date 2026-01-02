FROM python:3.11-slim

WORKDIR /app

# Copiar requirements e instalar dependencias
COPY data_acquirer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY data_acquirer/ ./data_acquirer/
COPY data/ ./data/

# Crear directorios necesarios
RUN mkdir -p data/raw data/indicators

# Comando por defecto: ejecutar el pipeline completo
CMD ["python", "data_acquirer/main.py"]
