FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set default port (Railway will override with PORT env var)
ENV PORT=8000
EXPOSE 8000

# Run the application using shell form to expand $PORT
CMD uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
