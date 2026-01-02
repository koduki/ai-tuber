FROM python:3.11-slim

WORKDIR /app

# Install dependencies
# google-genai: Gemini API
# httpx: Async HTTP client
# google-adk: Agent Development Kit
RUN pip install google-genai httpx google-adk

# Copy source code (optional, since we mount volumes in dev)
# COPY . .

# Run as a module to handle relative imports correctly
CMD ["python", "-m", "src.saint_graph.main"]
