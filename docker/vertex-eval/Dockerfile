# Vertex Custom Job: 엔드포인트 predict 품질 평가 (로컬 GPU·torch 불필요)
# 빌드: 저장소 루트에서
#   docker build -f docker/vertex-eval/Dockerfile -t REGION-docker.pkg.dev/PROJECT/REPO/vertex-eval:latest .

FROM python:3.11-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app/src

WORKDIR /app

COPY docker/vertex-eval/requirements.txt /app/requirements.txt
RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install -r /app/requirements.txt

COPY src /app/src
COPY scripts/vertex /app/scripts/vertex

ENTRYPOINT ["python3", "/app/scripts/vertex/vertex_eval_job_entrypoint.py"]
