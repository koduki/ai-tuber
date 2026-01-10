FROM python:3.11-slim

WORKDIR /app

ENV PYTHONIOENCODING=utf-8
ENV LANG=C.UTF-8

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY src/body/weather/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code (assuming docker-compose context is root)
COPY src/body/weather /app/src/body/weather

# Run the application
CMD ["python", "-m", "src.body.weather.main"]
