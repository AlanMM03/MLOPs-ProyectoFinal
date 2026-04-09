FROM python:3.11-slim

WORKDIR /app

# Copiamos todos los archivos al contenedor
COPY . .

# Instalamos dependencias
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Ejecutamos el script de Python directamente
CMD ["python", "main.py"]