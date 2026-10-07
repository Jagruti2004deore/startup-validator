FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app
COPY ui ./ui

# the database lives in /data, which a host can mount as a persistent disk
RUN useradd --create-home appuser && mkdir -p /data && chown appuser /data
USER appuser
ENV DB_PATH=/data/validator.db

EXPOSE 8000
# hosts such as Render set PORT; locally it falls back to 8000
CMD ["sh", "-c", "uvicorn app.api:app --host 0.0.0.0 --port ${PORT:-8000}"]