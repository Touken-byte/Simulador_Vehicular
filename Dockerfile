# Imagen base ligera con Python 3.11
FROM python:3.11-slim

# Dependencias de sistema necesarias para compilar geopandas/osmnx (GDAL, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgdal-dev \
    libspatialindex-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Por defecto, muestra el menú de ayuda; el comando real se pasa en docker-compose o docker run
CMD ["python", "main.py"]
