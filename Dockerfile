# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./src ./src
COPY ./photos_input ./photos_input

# Set the Python path
ENV PYTHONPATH=/app

# Command could be set here, but often overridden in docker-compose
# CMD ["python", "src/flow.py"] # Example, not ideal for Prefect agent setup