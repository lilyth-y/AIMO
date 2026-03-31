# Vertex AI에서 Qwen 튜닝/배포 (PD 연구용)

목표: **증명 제외 + 숫자 답만** 도메인으로 Qwen 계열을 SFT(QLoRA) 튜닝하고, Vertex에서 배포해 AIMO 파이프라인에 연결합니다.

## 0) 전제

- 프로젝트: `gen-lang-client-0300734101` (번호: 341687483990)
- 리전: `us-central1` (권장), 레이트리밋이 심하면 `global`도 고려
- 로컬: Python venv 사용 권장

## 1) gcloud로 Vertex 연결

```powershell
gcloud auth login
gcloud auth application-default login
gcloud config set project gen-lang-client-0300734101
gcloud config set ai/region us-central1
gcloud services enable aiplatform.googleapis.com
gcloud services enable storage.googleapis.com
```

## 2) SDK 설치 + 연결 체크

```powershell
python -m pip install -r requirements-vertex-sdk.txt
python scripts/vertex/vertex_env_check.py --project gen-lang-client-0300734101 --location us-central1
```

## 3) 튜닝 데이터 준비 (proof 제외 + 숫자 답만)

**로컬에 큰 JSONL/폴더(수 GB)가 있으면** → [LOCAL_DATA_PREP.md](./LOCAL_DATA_PREP.md) 의 `prepare_qwen_numeric_dataset_from_local.py` (스트리밍·reservoir).

작은 로컬 샘플만 있을 때:

```powershell
python scripts/vertex/prepare_qwen_numeric_dataset.py --seed 41 --train 3000 --dev 1000 --test 1000
```

⚠️ `data/numina_training_5k.jsonl`만 쓰면 숫자 답 필터 후 표본이 부족할 수 있습니다.  
**대안**: HuggingFace NuminaMath-1.5에서 seed 고정 샘플링:

```powershell
python scripts/vertex/prepare_qwen_numeric_dataset_from_hf.py --seed 41 --train 3000 --dev 1000 --test 1000
```

생성물:
- `data/finetune/qwen_numeric/train.jsonl`
- `data/finetune/qwen_numeric/dev.jsonl`
- `data/finetune/qwen_numeric/test.jsonl`

형식:
- `prompt`: 문제
- `completion`: `<ANS>정답</ANS>`

## 4) (다음 단계) Vertex Custom Training + Endpoint 배포

이 단계는 **컨테이너 이미지(학습 코드 포함)** + **GCS 경로**가 필요합니다.

**머지 학습·자동 GCS 업로드 절차를 한 문서로**: [MERGE_TRAIN_UPLOAD.md](./MERGE_TRAIN_UPLOAD.md)

### 4.1 학습 컨테이너 빌드/푸시(Artifact Registry)

예시(리전/레포는 상황에 맞게):

```powershell
gcloud auth configure-docker us-central1-docker.pkg.dev
gcloud artifacts repositories create aimo --repository-format=docker --location=us-central1

docker build -t us-central1-docker.pkg.dev/gen-lang-client-0300734101/aimo/vertex-train:latest -f docker/vertex-train/Dockerfile .
docker push us-central1-docker.pkg.dev/gen-lang-client-0300734101/aimo/vertex-train:latest
```

### 4.2 데이터 업로드(GCS)

버킷이 없다면:

```powershell
gcloud storage buckets create gs://YOUR_BUCKET --location=us-central1
```

업로드:

```powershell
gcloud storage cp data/finetune/qwen_numeric/train.jsonl gs://YOUR_BUCKET/aimo/finetune/qwen_numeric/train.jsonl
gcloud storage cp data/finetune/qwen_numeric/dev.jsonl   gs://YOUR_BUCKET/aimo/finetune/qwen_numeric/dev.jsonl
gcloud storage cp data/finetune/qwen_numeric/test.jsonl  gs://YOUR_BUCKET/aimo/finetune/qwen_numeric/test.jsonl
```

### 4.3 Vertex Custom Job 제출(QLoRA SFT)

로컬에서 SDK로 제출:

```powershell
python -m pip install -r requirements-vertex-sdk.txt

python scripts/vertex/submit_vertex_custom_job.py `
  --project gen-lang-client-0300734101 --location us-central1 `
  --container-image us-central1-docker.pkg.dev/gen-lang-client-0300734101/aimo/vertex-train:latest `
  --train-gcs gs://YOUR_BUCKET/aimo/finetune/qwen_numeric/train.jsonl `
  --dev-gcs gs://YOUR_BUCKET/aimo/finetune/qwen_numeric/dev.jsonl `
  --gcs-output gs://YOUR_BUCKET/aimo/models/qwen_numeric `
  --base-model Qwen/Qwen2.5-Math-7B-Instruct `
  --save-merged
```

산출물:
- `gs://YOUR_BUCKET/aimo/models/qwen_numeric/adapter/...`
- (옵션) `gs://YOUR_BUCKET/aimo/models/qwen_numeric/merged/...`

## 5) Endpoint 배포(온라인 예측)

### 5.1 서빙 컨테이너 빌드/푸시

```powershell
gcloud auth configure-docker us-central1-docker.pkg.dev
docker build -t us-central1-docker.pkg.dev/gen-lang-client-0300734101/aimo/vertex-serve:latest -f docker/vertex-serve/Dockerfile .
docker push us-central1-docker.pkg.dev/gen-lang-client-0300734101/aimo/vertex-serve:latest
```

### 5.2 Model 업로드 + Endpoint 생성 + Deploy

학습에서 `--save-merged`를 켰다면, `merged/` 디렉터리를 artifact로 쓰는 게 가장 단순합니다.

> **실제 머지 아티팩트만 올리기**: GCS에 `merged/` 가 준비되면 `ARTIFACT_URI` 또는 `VERTEX_MERGED_ARTIFACT_URI` 로 지정해 서울 스모크 트래킹 스크립트를 돌릴 수 있습니다.  
> 상세: [MERGED_MODEL_ARTIFACT.md](./MERGED_MODEL_ARTIFACT.md)

### 5.2b 서울 리전에서 스모크 트래킹 스크립트로 배포 (선택)

`scripts/vertex/track_colab_vertex_smoke_seoul.py` + `vertex_common` — `VERTEX_MERGED_ARTIFACT_URI` / `ARTIFACT_URI` 로 `gs://.../merged/` 를 넣으면 tiny 스모크 대신 실제 모델이 업로드됩니다.

```powershell
python -m pip install -r requirements-vertex-sdk.txt

python scripts/vertex/deploy_vertex_endpoint.py `
  --project gen-lang-client-0300734101 --location us-central1 `
  --model-display-name aimo-qwen-numeric `
  --artifact-uri gs://YOUR_BUCKET/aimo/models/qwen_numeric/merged `
  --serving-image us-central1-docker.pkg.dev/gen-lang-client-0300734101/aimo/vertex-serve:latest `
  --endpoint-display-name aimo-qwen-endpoint `
  --machine-type n1-standard-8 --accelerator-type NVIDIA_TESLA_A100 --accelerator-count 1
```

### 5.3 예측 호출(개념)

Endpoint가 뜬 뒤에는 Vertex Prediction 호출로 `{"instances":[{"prompt":"..."}]}` 형태로 `/predict`에 전달됩니다.
우리 서빙 컨테이너는 `prompt`를 받아 텍스트를 생성합니다.

권장 흐름:
- 학습: Vertex CustomJob(QLoRA) → GCS에 모델 아티팩트 저장
- 배포: Vertex Endpoint에 배포(온라인 예측)
- 연결: AIMO에서 HTTP/SDK로 엔드포인트 호출

원하면 여기까지 자동화 스크립트도 이어서 추가합니다(학습용 Dockerfile/submit 스크립트/배포 스크립트).

