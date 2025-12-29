FROM python:3.11-slim

WORKDIR /app

# Install dependencies
# google-genai: Gemini API
# httpx: Async HTTP client
# google-adk: Agent Development Kit
RUN pip install google-genai httpx google-adk

# Copy source code (optional, since we mount volumes in dev)
# COPY . .

CMD ["python", "-u", "main.py"]
