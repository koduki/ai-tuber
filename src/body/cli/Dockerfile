FROM python:3.11-slim

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /workspaces/ai-tuber/src/body/cli

# Install dependencies
COPY src/body/cli/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code (optional)
# COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
