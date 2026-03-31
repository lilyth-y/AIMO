# Vertex 최소 실행 플레이북

이 문서는 Vertex 학습/배포/평가를 **최소 단계로 1회 재현**하기 위한 단일 실행 가이드다.

## 0) 사전 설치

```bash
python -m pip install -r requirements-vertex-sdk.txt
python -m pip install -r requirements-vertex-tools.txt
python -m pip install -r requirements-vertex-bq.txt
```

## 1) 인증 및 기본 환경

```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project <PROJECT_ID>
gcloud services enable aiplatform.googleapis.com
```

권장 환경변수:

```bash
set PROJECT_ID=<PROJECT_ID>
set LOCATION=asia-northeast3
```

## 2) 환경 점검

```bash
python scripts/vertex/vertex_env_check.py
```

성공 시 Vertex SDK 연결 OK가 출력된다.

## 3) 데이터 준비 (train/dev/test)

```bash
python scripts/vertex/prepare_qwen_numeric_dataset_from_local.py ^
  --input data/numinamath_full.jsonl ^
  --output-dir data/finetune/qwen_numeric
```

생성된 JSONL을 GCS에 업로드한다.

## 4) 학습 이미지 준비

`docker/vertex-train` 이미지를 빌드/푸시한다.

## 5) Vertex Custom Job 실행

```bash
python scripts/vertex/submit_vertex_custom_job.py ^
  --project %PROJECT_ID% ^
  --location %LOCATION% ^
  --container-image <TRAIN_IMAGE_URI> ^
  --train-gcs gs://<BUCKET>/data/train.jsonl ^
  --dev-gcs gs://<BUCKET>/data/dev.jsonl ^
  --gcs-output gs://<BUCKET>/runs/qwen_numeric ^
  --save-merged
```

## 6) 머지 아티팩트 검증

```bash
python scripts/vertex/verify_merged_artifact.py ^
  --gcs-uri gs://<BUCKET>/runs/qwen_numeric/<JOB_ID>/merged/
```

## 7) 서빙 이미지 준비

`docker/vertex-serve` 이미지를 빌드/푸시한다.

## 8) 엔드포인트 배포 (기본 CPU)

```bash
python scripts/vertex/deploy_vertex_endpoint.py ^
  --project %PROJECT_ID% ^
  --location %LOCATION% ^
  --model-display-name aimo-qwen-numeric ^
  --artifact-uri gs://<BUCKET>/runs/qwen_numeric/<JOB_ID>/merged/ ^
  --serving-image <SERVE_IMAGE_URI> ^
  --machine-type n1-standard-4
```

GPU가 필요할 때만 다음을 추가한다.

```bash
--accelerator-type NVIDIA_TESLA_T4 --accelerator-count 1
```

## 9) 품질 평가 (게이트 판정)

```bash
python scripts/vertex/eval_vertex_endpoint_quality.py ^
  --endpoint-id <ENDPOINT_ID> ^
  --project %PROJECT_ID% ^
  --location %LOCATION% ^
  --n-problems 50 ^
  --enforce-gates
```

합격 기준은 `docs/vertex/STEP2_QUALITY_GATES.md`를 따른다. `--enforce-gates` 로 미충족 시 exit code 2.

## 10) 결과 업로드 (선택)

```bash
python scripts/vertex/upload_vertex_eval_to_bigquery.py results/<EVAL_JSONL> ^
  --table <PROJECT_ID>.aimo_vertex.eval_runs ^
  --endpoint-id <ENDPOINT_ID>
```

## 실패/종료 시 정리 절차

스모크/실험 리소스를 정리한다.

```bash
python scripts/vertex/cleanup_vertex_region.py --dry-run
python scripts/vertex/cleanup_vertex_region.py --yes
```

리전 전체 정리가 필요할 때만:

```bash
python scripts/vertex/cleanup_vertex_region.py --all --yes
```

## 체크리스트 (Go/No-Go)

- `vertex_env_check.py` 성공
- merged 아티팩트 검증 성공
- endpoint 배포 성공
- `n-problems >= 50` 평가 완료
- `STEP2_QUALITY_GATES.md`의 모든 임계값 충족
