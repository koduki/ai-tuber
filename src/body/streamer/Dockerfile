FROM python:3.11-slim

WORKDIR /app

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY src/body/streamer/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ /app/src/

# Expose MCP server port
EXPOSE 8000

# Run the MCP server
CMD ["python", "-m", "src.body.streamer.main"]
