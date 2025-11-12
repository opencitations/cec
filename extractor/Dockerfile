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

# Copy the entire extractor directory
COPY ./cex /app/extractor/cex

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/extractor/cex/requirements.txt

# Set working directory to extractor
WORKDIR /app/extractor

# Expose port
EXPOSE 5001

# Run with Gunicorn (production-ready)
CMD ["gunicorn", \
     "--workers", "1", \
     "--bind", "0.0.0.0:5001", \
     "--timeout", "900", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "debug", \
     "cex.main:app"]