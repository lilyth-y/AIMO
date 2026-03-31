# Ralph 정확도 루프 (Vertex)

로컬 GPU 없이 **Vertex Online Prediction 엔드포인트**만으로 평가할 때의 흐름입니다.

GCP 인증·ADC·서비스 계정 JSON: [../vertex/GCP_AUTH.md](../vertex/GCP_AUTH.md)  
연결 확인: `python scripts/vertex/run_vertex_checks.py --project YOUR_PROJECT --location YOUR_REGION`

## 진행 순서 (Cloud Shell·클라우드)

로컬 PC에서 스모크·평가를 돌리지 않는 것을 기본으로 한다 ([AIMO_GCP_PROFILE.md](../vertex/AIMO_GCP_PROFILE.md) §실행 위치).

| 단계 | 내용 |
|------|------|
| 1 | 저장소 클론·루트·의존성: [CLOUD_NUMINA_RUN.md](CLOUD_NUMINA_RUN.md) |
| 2 | 엔드포인트 eval 전용 최소 설치: [CLOUD_SHELL_ENDPOINT_EVAL.md](CLOUD_SHELL_ENDPOINT_EVAL.md) (`requirements-cloudshell-endpoint-eval.txt`) |
| 3 | 고정 프로젝트·버킷·엔드포인트 ID: [AIMO_GCP_PROFILE.md](../vertex/AIMO_GCP_PROFILE.md) |
| 4 | 연결 스모크: `bash scripts/vertex/run_aimo_gcp_smoke.sh` |
| 5 | `vertex-eval` 이미지: Cloud Build ([AIMO_GCP_PROFILE.md](../vertex/AIMO_GCP_PROFILE.md) §vertex-eval 이미지 빌드) |
| 6 | 평가 데이터 `gs://.../numinamath_full.jsonl` 업로드 후 **Custom Job** 제출 (같은 문서 §Job 제출) |

**엔드포인트 스모크 한 줄** (추출·타임아웃 확인):

`python3 scripts/vertex/eval_vertex_endpoint_quality.py --endpoint-id ... --n-problems 2 --dump-predictions 2 --predict-timeout 20 --vertex-predict-retries 0 --max-format-retries 0`

## 무엇이 “통과”인가

- **Ralph 목표**: 기본 **전체 정확도 ≥ 80%** (`AIMO_RALPH_TARGET_ACCURACY_PCT`, 미설정 시 `src/evaluation/config.py`의 `RALPH_TARGET_ACCURACY_DEFAULT_PCT`).
- **측정 도구**: `scripts/vertex/eval_vertex_endpoint_quality.py` — 요약의 `accuracy`는 **0~1 비율** (내부에서 퍼센트로 변환해 게이트).

## Custom Job으로 한 번에 (권장)

1. 이미지: `docker/vertex-eval/Dockerfile` 빌드 후 Artifact Registry에 push.
2. 제출:

```bash
python scripts/vertex/submit_vertex_eval_job.py \
  --project YOUR_PROJECT --location asia-northeast3 \
  --container-image REGION-docker.pkg.dev/PROJECT/REPO/vertex-eval:latest \
  --staging-bucket gs://YOUR_BUCKET/vertex-staging \
  --endpoint-id ENDPOINT_ID \
  --gcs-data-uri gs://YOUR_BUCKET/data/numinamath_full.jsonl \
  --gcs-output-uri gs://YOUR_BUCKET/results/run.jsonl \
  --gcs-summary-uri gs://YOUR_BUCKET/results/vertex_summary.json \
  --write-summary-json /tmp/vertex_summary.json \
  --enforce-ralph-accuracy \
  --n-problems 50 --data-file numinamath_full.jsonl --difficulty-at-most medium
```

**플레이스홀더 치환 예** (현재 레포에 맞춘 값 — [AIMO_GCP_PROFILE.md](../vertex/AIMO_GCP_PROFILE.md)):

- `YOUR_PROJECT` → `gen-lang-client-0300734101`
- `YOUR_BUCKET` → `gen-lang-client-0300734101-aimo-vertex-341687483990` (버킷 이름)
- `ENDPOINT_ID` → `2486393813610790912`
- `--container-image` / `REGION-docker.pkg.dev/...` 는 Artifact Registry에 올린 **실제 이미지**로 교체

그 외 플래그:

- `--enforce-ralph-accuracy`: Job이 **정확도 목표 미달이면 exit 1** (Custom Job 실패로 표시).
- `--write-summary-json` + `--gcs-summary-uri`: 요약 JSON을 GCS에 올려 두고, 나중에 **다운로드 후** 게이트만 재실행 가능.

## 요약 JSON만으로 게이트 (오프라인)

```bash
gsutil cp gs://YOUR_BUCKET/results/vertex_summary.json .
python scripts/vertex/ralph_vertex_accuracy_gate.py vertex_summary.json
```

`PipelineOrchestrator`용 `scripts/ralph_accuracy_gate.py`와 달리, 이 스크립트는 **Vertex eval 요약 형식**(accuracy 비율)을 처리합니다.

## STEP2 게이트와의 관계

- `STEP2_QUALITY_GATES.md`의 `--enforce-gates` (exit **2**)는 **별도** 임계값(샘플 수·형식률·최소 정확도 0.2 등).
- Ralph `--enforce-ralph-accuracy` (exit **1**)는 **80% 목표**용. 둘 다 켜면 STEP2 실패 시 먼저 exit 2로 종료합니다.

## 관련 문서

- 엔드포인트 평가 상세: `docs/vertex/EVAL_REAL_MODEL.md`
- 제출 스크립트: `scripts/vertex/submit_vertex_eval_job.py`
