FROM python:3.11-slim

WORKDIR /workspace

# Instalar dependencias del sistema y el cliente de Docker CLI
RUN apt-get update && apt-get install -y \
    curl \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY backend /workspace/backend

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]