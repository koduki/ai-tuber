FROM python:3.11-slim

WORKDIR /app

# Install dependencies
# fastapi, uvicorn: For the HTTP server
# sse-starlette: For Server-Sent Events support
RUN pip install fastapi uvicorn sse-starlette

# Copy source code (optional)
# COPY . .

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
