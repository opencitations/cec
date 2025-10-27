# Base image
FROM python:3.9-slim

# Prevent Python from writing pyc files and ensure output is unbuffered
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    build-essential \
    curl

# Set working directory
WORKDIR /app

# Copy requirements first for better layer caching
COPY ./classifier/requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the entire classifier directory
COPY ./classifier /app/classifier

# Create directories for models (to be mounted or downloaded later)
RUN mkdir -p /app/classifier/cic/src/models/NoSections \
    && mkdir -p /app/classifier/cic/src/models/Sections

# Set working directory to where the cic module is located
WORKDIR /app/classifier

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "-m", "cic.main", "--src_path", "/app/classifier/cic/src", "--prefix", "/cic"]