# Use official Python image from Docker Hub.
FROM python:3.12-slim

# Image description.
LABEL org.opencontainers.image.source=https://github.com/ainglessi/prometheus_asyncua_exporter
LABEL org.opencontainers.image.description="OPC UA exporter for Prometheus"
LABEL org.opencontainers.image.licenses=Apache-2.0

# Set working directory in the container.
WORKDIR /app

# Copy requirements file to the container.
COPY requirements.txt .

# Install dependencies.
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files to the container.
COPY . .

# Command to run the application.
CMD ["python", "exporter.py", "config.yaml"]
