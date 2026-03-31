# 머지 학습(Vertex Custom Job) + GCS 업로드

학습 컨테이너 `train_qlora_sft.py`는 학습 종료 후 **`--gcs_output`이 `gs://`이면** 어댑터와(옵션) **머지 폴더를 GCS에 자동 업로드**한다. 별도 `gsutil cp` 단계가 필수는 아니다.

업로드 경로 규칙(코드 기준):

- `--gcs-output gs://BUCKET/PREFIX` →  
  `gs://BUCKET/PREFIX/adapter/...` , `gs://BUCKET/PREFIX/merged/...` (`--save_merged` 시)

---

## 0) 사전 준비

```powershell
gcloud auth login
gcloud auth application-default login
gcloud config set project gen-lang-client-0300734101
gcloud services enable aiplatform.googleapis.com storage.googleapis.com
```

```powershell
python -m pip install -r requirements-vertex-sdk.txt
python scripts/vertex/vertex_env_check.py --project gen-lang-client-0300734101 --location us-central1
```

버킷: 기존 `gs://gen-lang-client-0300734101-aimo-vertex-341687483990/` 를 쓰거나, 새 버킷을 만든다.

```powershell
# 새 버킷 예 (리전은 조직 정책에 맞게)
gcloud storage buckets create gs://YOUR_BUCKET --location=us-central1
```

---

## 1) 튜닝용 JSONL 준비 + GCS 업로드

```powershell
cd C:\startingup\AIMO
```

**로컬에 대용량(예: 1.2GB) JSONL이 있는 경우** → [LOCAL_DATA_PREP.md](./LOCAL_DATA_PREP.md):

```powershell
python scripts/vertex/prepare_qwen_numeric_dataset_from_local.py `
  --input-dir "D:\path\to\your\data" `
  --seed 41 --train 3000 --dev 1000 --test 1000
```

**Hugging Face에서 스트리밍** (권장이었던 경로):

```powershell
python scripts/vertex/prepare_qwen_numeric_dataset_from_hf.py --seed 41 --train 3000 --dev 1000 --test 1000
```

업로드 (버킷·접두사는 본인 경로로):

```powershell
$BUCKET = "gen-lang-client-0300734101-aimo-vertex-341687483990"
$PREFIX = "aimo/finetune/qwen_numeric"
gcloud storage cp data/finetune/qwen_numeric/train.jsonl "gs://$BUCKET/$PREFIX/train.jsonl"
gcloud storage cp data/finetune/qwen_numeric/dev.jsonl   "gs://$BUCKET/$PREFIX/dev.jsonl"
```

---

## 2) 학습용 Docker 이미지 빌드·푸시

```powershell
gcloud auth configure-docker us-central1-docker.pkg.dev

docker build -t us-central1-docker.pkg.dev/gen-lang-client-0300734101/aimo/vertex-train:latest -f docker/vertex-train/Dockerfile .
docker push us-central1-docker.pkg.dev/gen-lang-client-0300734101/aimo/vertex-train:latest
```

---

## 3) Custom Job 제출 (QLoRA + **머지 저장·업로드**)

출력·업로드 위치를 한 번에 지정한다 (`--gcs-output` = 어댑터/머지가 올라갈 **프리픽스**).

```powershell
$OUT = "gs://gen-lang-client-0300734101-aimo-vertex-341687483990/aimo/models/qwen_numeric"

python scripts/vertex/submit_vertex_custom_job.py `
  --project gen-lang-client-0300734101 --location us-central1 `
  --container-image us-central1-docker.pkg.dev/gen-lang-client-0300734101/aimo/vertex-train:latest `
  --train-gcs gs://gen-lang-client-0300734101-aimo-vertex-341687483990/aimo/finetune/qwen_numeric/train.jsonl `
  --dev-gcs   gs://gen-lang-client-0300734101-aimo-vertex-341687483990/aimo/finetune/qwen_numeric/dev.jsonl `
  --gcs-output $OUT `
  --base-model Qwen/Qwen2.5-Math-7B-Instruct `
  --save-merged `
  --machine-type n1-standard-8 `
  --accelerator-type NVIDIA_TESLA_A100 `
  --accelerator-count 1
```

- **`--save-merged`**: 로컬 디스크에 `merged/` 생성 후, `--gcs_output` 이 `gs://` 이면 **`OUT/merged/` 로 업로드**.
- 머신/GPU는 쿼터·비용에 맞게 조정 (`submit_vertex_custom_job.py --help`).

작업 로그는 Vertex 콘솔 → Custom training → 해당 Job에서 확인.

---

## 4) 머지 아티팩트 검증

학습이 끝난 뒤:

```powershell
python scripts/vertex/verify_merged_artifact.py `
  --gcs-uri gs://gen-lang-client-0300734101-aimo-vertex-341687483990/aimo/models/qwen_numeric/merged/
```

`[OK]`면 [STEP1_MERGED_ARTIFACT.md](./STEP1_MERGED_ARTIFACT.md) 1단계 통과.

---

## 5) 수동 업로드가 필요한 경우

- **로컬에서만** 학습·머지한 폴더가 있을 때:

```powershell
gcloud storage cp -r D:\path\to\merged "gs://BUCKET/aimo/models/qwen_numeric/merged"
```

끝 슬래시·오브젝트 경로는 `gcloud storage` 동작에 맞게 조정.

---

## 6) 다음 단계

- 로컬 품질: `python scripts/eval_hf_local_quality.py --model D:\...\merged` (또는 GCS 받은 뒤)
- Vertex 배포: [VERTEX_TRAIN_DEPLOY_QWEN.md](./VERTEX_TRAIN_DEPLOY_QWEN.md) §5, [MERGED_MODEL_ARTIFACT.md](./MERGED_MODEL_ARTIFACT.md)
- 품질 기준: [STEP2_QUALITY_GATES.md](./STEP2_QUALITY_GATES.md)

---

## 참고

- 학습 엔트리포인트: `docker/vertex-train/train_qlora_sft.py` (`--save_merged`, GCS 업로드 루프)
- 제출 스크립트: `scripts/vertex/submit_vertex_custom_job.py`
