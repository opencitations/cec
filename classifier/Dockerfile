# Base image
FROM python:3.11-slim

# Set environment variables for Flask
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    SRC_PATH=/app/classifier/cic/src \
    URL_PREFIX=/cic

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    build-essential \
    curl

# Set working directory
WORKDIR /app

# Copy requirements first for better layer caching
COPY ./requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the entire classifier directory
COPY ./ /app/classifier

# Create directories for models (to be mounted or downloaded later)
RUN mkdir -p /app/classifier/cic/src/models/ModelsWithoutSections \
    && mkdir -p /app/classifier/cic/src/models/ModelsWithSections

# Set working directory to where the cic module is located
WORKDIR /app/classifier

# Expose port
EXPOSE 5000

# Run with Gunicorn (production-ready)
CMD ["gunicorn", \
     "--workers", "1", \
     "--bind", "0.0.0.0:5000", \
     "--timeout", "900", \
     "--chdir", "/app/classifier", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info", \
     "cic.main:app"]