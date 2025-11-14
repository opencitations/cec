# Base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    URL_PREFIX=/cex \
    GROBID_URL=http://grobid:8070

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    build-essential \
    curl

# Set working directory
WORKDIR /app/extractor/cex

# Copy requirements file
COPY ./cex/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    python -m spacy download en_core_web_lg

# Copy application code
COPY ./cex .

# Create non-root
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 5001

# Run with Gunicorn con preload_app
CMD ["gunicorn", \
     "--workers", "4", \
     "--bind", "0.0.0.0:5001", \
     "--timeout", "900", \
     "--preload", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info", \
     "main:app"]