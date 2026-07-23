# Shared image for the API and the Celery worker — same code, different
# command. Models (bge-m3, reranker, TrOCR, BLIP, Whisper ≈ 4GB) are NOT
# baked in: they download on first use into /models, which compose mounts
# as a named volume so the two containers share one copy that survives
# rebuilds.

FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/models

WORKDIR /app

# curl for the healthcheck; libgomp1 is required by ctranslate2 (faster-whisper).
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Requirements first so dependency layers cache across code changes.
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Non-root. Owns /models and the upload dir so both are writable at runtime.
RUN useradd --create-home --uid 1000 app \
    && mkdir -p /models /app/storage/uploads \
    && chown -R app:app /models /app
USER app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
