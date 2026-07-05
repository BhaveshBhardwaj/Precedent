FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PRECEDENT_RECALL_SOURCE=app_state
ENV PRECEDENT_GRAPH_SOURCE=app_state
ENV COGNEE_RECALL_TIMEOUT_SECONDS=3
ENV COGNEE_WRITE_TIMEOUT_SECONDS=8

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY seed ./seed

EXPOSE 8000

CMD python -m seed.seed_data && python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
