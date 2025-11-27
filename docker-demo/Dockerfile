# Use official Python runtime as base image
FROM python:3.11-slim

# Set working directory in container
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Jakarta

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy the crawler script
COPY crawler.py .

# Create output directory
RUN mkdir -p /app/output

# Run the crawler when container launches
CMD ["python", "crawler.py"]
