FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY scripts/news_collector/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY scripts/news_collector/ /app/scripts/news_collector/
COPY src/saint_graph/config.py /app/src/saint_graph/config.py

# Set Python path
ENV PYTHONPATH=/app

# Run the news collector
CMD ["python", "-m", "scripts.news_collector.news_agent"]
