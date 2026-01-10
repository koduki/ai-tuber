FROM python:3.11-slim

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies
COPY src/body/cli/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code preserving structure
COPY src /app/src

ENV PYTHONIOENCODING=utf-8
ENV LANG=C.UTF-8
ENV PYTHONPATH=/app

CMD ["uvicorn", "src.body.cli.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
