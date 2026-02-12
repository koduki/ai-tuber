FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY src/saint_graph/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app/
ENV PYTHONPATH=/app/src

CMD ["python", "-m", "saint_graph.main"]
