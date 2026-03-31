# 학습·머지 모델 아티팩트로 Vertex 배포하기

**단계별 가이드**: [STEP1_MERGED_ARTIFACT.md](./STEP1_MERGED_ARTIFACT.md) (머지 준비·검증) → [STEP2_QUALITY_GATES.md](./STEP2_QUALITY_GATES.md) (품질 기준)

**왜 Vertex·GCS·커스텀 서빙 조합을 쓰는지**(다른 연구/대안 대비 이점): [WHY_THIS_VERTEX_STACK.md](./WHY_THIS_VERTEX_STACK.md)

tiny-gpt2 스모크는 **인프라 검증**용입니다. **답 품질**을 보려면 Custom Job으로 학습한 뒤 **`merged/`** HF 디렉터리를 GCS에 두고, 그 경로를 배포에 넣어야 합니다.

### 베이스 HF 수학 모델만 GCS에 올려 배포 (학습 없이)

공개 Hub 모델을 로컬에 받은 뒤 GCS로 올리고 `ARTIFACT_URI`로 배포할 수 있습니다.

- **7B (품질 우선)**: `Qwen/Qwen2.5-Math-7B-Instruct` — GPU·배포 절차: [DEPLOY_QWEN_7B_VERTEX.md](./DEPLOY_QWEN_7B_VERTEX.md)
- **1.5B (스모크·저VRAM)**: `Qwen/Qwen2.5-Math-1.5B-Instruct`

```powershell
# 1) 업로드 예: 1.5B 스모크
python scripts/vertex/upload_hf_model_to_gcs.py `
  --model-id Qwen/Qwen2.5-Math-1.5B-Instruct `
  --gcs-prefix gs://gen-lang-client-0300734101-aimo-vertex-341687483990/aimo/models/hf/Qwen2.5-Math-1.5B-Instruct/

# 2) 배포 (서울)
$env:ARTIFACT_URI = "gs://gen-lang-client-0300734101-aimo-vertex-341687483990/aimo/models/hf/Qwen2.5-Math-1.5B-Instruct/"
$env:SMOKE_PREDICT_TIMEOUT_SECONDS = "900"
python scripts/vertex/track_colab_vertex_smoke_seoul.py
```

첫 온라인 추론은 모델 로드로 **수 분** 걸릴 수 있어, `eval_vertex_endpoint_quality.py`에는 `--predict-timeout`(기본 600초)을 두었습니다.

## 1) 산출물이 나오는 곳

[VERTEX_TRAIN_DEPLOY_QWEN.md](./VERTEX_TRAIN_DEPLOY_QWEN.md) 의 Custom Job 예시에서 `--save-merged` 를 켜면 대략 다음이 생깁니다.

| 경로 (예시) | 용도 |
|-------------|------|
| `gs://YOUR_BUCKET/aimo/models/qwen_numeric/adapter/` | LoRA 어댑터만 |
| `gs://YOUR_BUCKET/aimo/models/qwen_numeric/merged/` | **서빙용**: 베이스+어댑터 병합 HF 포맷 (권장) |

Vertex `Model.upload` 의 `artifact_uri` 에는 **merged 디렉터리**를 가리키는 것이 가장 단순합니다.

## 2) 토크나이저·transformers 호환

`docker/vertex-serve/requirements.txt` 의 `transformers` 버전과 맞지 않는 `tokenizer.json` 등이 있으면 로드 실패할 수 있습니다.  
이전 스모크에서 쓴 **nofast** 아티팩트처럼, 컨테이너 버전에 맞게 파일을 정리한 복사본을 GCS에 두는 방법을 고려하세요.

## 3) 환경변수로 실제 아티팩트 지정

`scripts/vertex/vertex_common.py` 의 `apply_smoke_env_overrides` 는 우선순위가 다음과 같습니다.

1. **`ARTIFACT_URI`** — `gs://.../merged/` (끝 슬래시 권장)
2. **`VERTEX_MERGED_ARTIFACT_URI`** — `ARTIFACT_URI` 가 비어 있을 때 동일 역할
3. 기본값 — **tiny-gpt2 스모크** (개발용)

### PowerShell 예시 (서울 트래킹 스크립트)

```powershell
$env:VERTEX_MERGED_ARTIFACT_URI = "gs://YOUR_BUCKET/aimo/models/qwen_numeric/merged/"
$env:SMOKE_ACCELERATOR_MODE = "CPU"   # 또는 GPU
$env:MACHINE_TYPE = "n1-standard-4"
python scripts/vertex/track_colab_vertex_smoke_seoul.py
```

또는 한 줄로:

```powershell
$env:ARTIFACT_URI = "gs://YOUR_BUCKET/aimo/models/qwen_numeric/merged/"
```

## 4) 대안: `deploy_vertex_endpoint.py`

리전·이름을 명시적으로 주고 싶으면:

```powershell
python scripts/vertex/deploy_vertex_endpoint.py `
  --project gen-lang-client-0300734101 --location us-central1 `
  --model-display-name aimo-qwen-numeric `
  --artifact-uri gs://YOUR_BUCKET/aimo/models/qwen_numeric/merged ` `
  --serving-image us-central1-docker.pkg.dev/gen-lang-client-0300734101/aimo/vertex-serve:latest `
  --machine-type n1-standard-8 --accelerator-type NVIDIA_TESLA_A100 --accelerator-count 1
```

(서울 스모크 트래킹 스크립트는 `asia-northeast3` + LRO 보정 등이 들어 있음.)

## 5) 품질 평가

엔드포인트 생성 후:

```powershell
python scripts/vertex/eval_vertex_endpoint_quality.py --endpoint-id <ID> --n-problems 50
```

자세한 내용은 [VERTEX_SCRIPTS_EVALUATION.md](../VERTEX_SCRIPTS_EVALUATION.md) §7.

### 로컬에서 `merged/` 만으로 평가 (Vertex 전)

GCS에 올리기 전, **동일한 HF 머지 디렉터리**를 디스크 경로로 넘겨 로컬에서 채점할 수 있다.

```powershell
cd C:\startingup\AIMO
python scripts/eval_hf_local_quality.py --model D:\path\to\merged --n-problems 50
```

- 경로는 `config.json` 이 있는 **머지 루트**여야 한다.
- stdout 의 `ans_tag_compliance` / `predicted_nonnull` 과 JSONL 의 `completion_head` 로 프롬프트 준수를 확인한다.
- 상세: [EVAL_REAL_MODEL.md](./EVAL_REAL_MODEL.md).
