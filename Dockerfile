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

# Set the working directory
WORKDIR /app

# Copy files from the classifier folder into the working directory
COPY ./classifier /app/classifier

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/classifier/requirements.txt

WORKDIR /app/classifier

# Command to start the application
CMD ["python", "-m", "cic.main", "--src_path", "/app/classifier/cic/src"]