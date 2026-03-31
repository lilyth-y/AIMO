# Cloud Shell — Vertex Endpoint 품질 평가 (최소 설치)

`eval_vertex_endpoint_quality.py`만 돌릴 때는 **`requirements.txt` 전체를 설치하지 않는다** (torch 등으로 디스크 부족).  
고정 프로필·엔드포인트 ID: [../vertex/AIMO_GCP_PROFILE.md](../vertex/AIMO_GCP_PROFILE.md)

## 1) 저장소·브랜치

```bash
cd ~/AIMO
git pull origin changes
```

## 2) `/tmp` 에 최소 패키지

```bash
export PIP_CACHE_DIR=/tmp/pip-cache
mkdir -p /tmp/aimo-pypi
python3 -m pip install --target /tmp/aimo-pypi -r requirements-cloudshell-endpoint-eval.txt
export PYTHONPATH="/tmp/aimo-pypi:${PYTHONPATH}:${PWD}/src"
```

## 3) GCP 환경 (서울 엔드포인트 예시)

```bash
export GOOGLE_CLOUD_PROJECT="gen-lang-client-0300734101"
export GOOGLE_CLOUD_LOCATION="asia-northeast3"
export AIMO_VERTEX_ENDPOINT_ID="2486393813610790912"
# 선택: ADC — Cloud Shell에서는 보통 이미 설정됨
# gcloud auth application-default login
```

## 4) 연결 스모크 (선택)

```bash
bash scripts/vertex/run_aimo_gcp_smoke.sh
```

## 5) 엔드포인트 품질 스모크 (추출·타임아웃)

- **`--dump-predictions`** — 처음 1~2문항에서 원시 `predictions` 페이로드를 stderr에 덤프(스키마 확인).
- **`--predict-timeout 20`** — 벽시계 타임아웃 스모크(지연 감지).
- **`--vertex-predict-retries 0`** — 재시도 없이 1회만.
- 형식 유도 1회만: **`--max-format-retries 0`** (strict-first 1회; `--no-format-gate` 대신 권장).

```bash
python3 scripts/vertex/eval_vertex_endpoint_quality.py \
  --endpoint-id "${AIMO_VERTEX_ENDPOINT_ID}" \
  --n-problems 2 --seed 42 \
  --data-file numina_training_5k.jsonl \
  --dump-predictions 2 \
  --predict-timeout 20 \
  --vertex-predict-retries 0 \
  --max-format-retries 0
```

`numinamath_full.jsonl` 등은 `data/` 또는 GCS에 두고 `--data-file`로 이름만 맞춘다 (`evaluation.config.find_data_file`).

## 6) 대규모(n≥50) — Custom Job

[RALPH_VERTEX.md](RALPH_VERTEX.md) · [AIMO_GCP_PROFILE.md](../vertex/AIMO_GCP_PROFILE.md) (Cloud Build → `vertex-eval` 이미지 → `submit_vertex_eval_job.py` → GCS summary → `ralph_vertex_accuracy_gate.py`).

## 검증 기준 (플랜과 동일)

| 단계 | 조건 |
|------|------|
| Smoke | `n=2`, `api_error==0`, `raw_text_head` 비어 있지 않음 |
| Mini | `n=10`, `graded` ≥ 1 |
| Scale | Custom Job 후 summary JSON + 게이트 스크립트 정상 |
