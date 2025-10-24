# Base image
FROM python:3.9-slim

# Ensure Python output is unbuffered
ENV PYTHONUNBUFFERED=1

# Install system dependencies required for Python package compilation
# We clean up apt cache after installation to reduce image size
RUN apt-get update && \
    apt-get install -y \
    git \
    python3-dev \
    build-essential && \
    rm -rf /var/lib/apt/lists/*

# Imposta la working directory
WORKDIR /app

# Copia i file dalla cartella classifier nella working directory
COPY ./classifier /app/classifier

# Installa le dipendenze Python
RUN pip install --no-cache-dir -r /app/classifier/requirements.txt

# Comando per avviare l'applicazione
CMD ["python", "-m", "cic.main", "--src_path", "/app/classifier/cic/src"]