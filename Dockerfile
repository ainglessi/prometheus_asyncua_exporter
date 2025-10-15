# Use official Python image from Docker Hub.
FROM python:3.13-slim

# Set working directory in the container.
WORKDIR /app

# Install dependencies.
COPY requirements.txt .
RUN python -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"
RUN /app/venv/bin/pip install --no-cache-dir -r requirements.txt

# Copy application files to the container.
COPY . .

# Command to run the application.
CMD ["venv/bin/python", "exporter.py", "config.yaml"]
