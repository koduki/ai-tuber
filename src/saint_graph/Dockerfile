FROM python:3.11-slim

WORKDIR /app
COPY src/saint_graph/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app/
ENV PYTHONPATH=/app

CMD ["python", "-m", "src.saint_graph.main"]
