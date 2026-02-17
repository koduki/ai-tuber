FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY scripts/news_collector/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY scripts/news_collector/ /app/scripts/news_collector/
COPY src/infra/ /app/src/infra/
COPY src/saint_graph/__init__.py src/saint_graph/config.py /app/src/saint_graph/

# Set Python path (include src for top-level packages, and app for scripts)
ENV PYTHONPATH=/app/src:/app

# Run the news collector
CMD ["python", "-m", "scripts.news_collector.news_agent"]
