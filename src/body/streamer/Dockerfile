FROM python:3.11-slim

WORKDIR /app

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY src/body/streamer/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ /app/src/

# Expose REST API port
EXPOSE 8000

# Set Python path to include src to allow top-level imports of packages inside src/
ENV PYTHONPATH=/app/src

# Run the streamer
CMD ["python", "-m", "body.streamer.main"]
