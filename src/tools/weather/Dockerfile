FROM python:3.11-slim

WORKDIR /app

ENV PYTHONIOENCODING=utf-8
ENV LANG=C.UTF-8
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY src/tools/weather/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code (assuming docker-compose context is root)
COPY src/tools/weather /app/src/tools/weather

# Run the application
CMD ["python", "-m", "src.tools.weather.main"]
