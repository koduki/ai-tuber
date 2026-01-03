FROM python:3.11-slim

WORKDIR /app

# Install dependencies
# google-genai: Gemini API
# httpx: Async HTTP client
# google-adk: Agent Development Kit
RUN pip install google-genai httpx google-adk

# Copy source code
COPY . .

# Set PYTHONPATH to include /app so src module is found
ENV PYTHONPATH=/app

# Run as a module to handle relative imports correctly
CMD ["python", "-m", "src.saint_graph.main"]
