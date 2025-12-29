FROM python:3.11-slim

WORKDIR /app

# Install dependencies
# google-genai: Gemini API
# httpx: Async HTTP client
# sseclient-py: For consuming Server-Sent Events from MCP
# google-adk: Agent Development Kit
RUN pip install google-genai httpx sseclient-py google-adk

# Copy source code (optional, since we mount volumes in dev)
# COPY . .

CMD ["python", "-u", "main.py"]
