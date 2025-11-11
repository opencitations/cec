# Base image
FROM python:3.11-slim

# Set environment variables for Flask
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    URL_PREFIX=/cex


# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    build-essential \
    curl

# Set working directory
WORKDIR /app

# Copy requirements first for better layer caching
COPY cex/requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Install grobid_client_python
RUN git clone https://github.com/kermitt2/grobid_client_python && \
    cd grobid_client_python && \
    python3 setup.py install && \
    cd ..

# Copy the entire extractor directory
COPY ./cex /app/extractor

# Set working directory to where the cic module is located
WORKDIR /app/extractor

# Expose port
EXPOSE 5001

# Run with Gunicorn (production-ready)
CMD ["gunicorn", \
     "--workers", "1", \
     "--bind", "0.0.0.0:5001", \
     "--timeout", "900", \
     "--chdir", "/app/extractor", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info", \
     "main:app"]