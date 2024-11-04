# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including curl
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make sure the application directory is in Python path
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Default command uses development settings with reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
