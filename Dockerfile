# Use official Python image from Docker Hub.
FROM python:3.13-slim

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
