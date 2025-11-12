# Base image
FROM python:3.11-slim

# Set environment variables for Flask
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

# Copy the entire extractor directory
COPY ./cex .

# Install Python dependencies
RUN pip install --no-cache-dir -r ./requirements.txt

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
     "main:app"]