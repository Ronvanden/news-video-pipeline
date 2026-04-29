# Use Python 3.9 slim image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Cloud Run sets PORT; default 8080 for local docker run -p 8080:8080
EXPOSE 8080

# Bind 0.0.0.0 so the service is reachable outside the container
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]