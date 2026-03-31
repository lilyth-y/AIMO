FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements-cloudrun.txt /app/requirements-cloudrun.txt

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git curl ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade pip \
    && pip install -r /app/requirements-cloudrun.txt

# Cloud Run API는 src 코드만 필요합니다.
COPY src /app/src

ENV PORT=8080
EXPOSE 8080

CMD ["uvicorn", "src.service.cloud_run_api:app", "--host", "0.0.0.0", "--port", "8080"]

