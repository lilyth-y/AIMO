FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv \
    git curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY docker/vertex-serve/requirements.txt /app/requirements.txt
RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install torch==2.3.1 --index-url https://download.pytorch.org/whl/cu121 && \
    python3 -m pip install -r /app/requirements.txt

COPY docker/vertex-serve/serve.py /app/serve.py

ENV PORT=8080
EXPOSE 8080

ENTRYPOINT ["python3", "/app/serve.py"]

