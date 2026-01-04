FROM python:3.11-slim

WORKDIR /workspaces/ai-tuber

# Install dependencies
COPY src/saint_graph/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code (optional, since we mount volumes in dev)
# COPY . .

# Run as a module to handle relative imports correctly
CMD ["python", "-m", "src.saint_graph.main"]
