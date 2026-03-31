# Vertex에 Qwen2.5-Math-7B-Instruct 배포

1.5B 스모크 대비 **추론 품질**을 올리려면 동일 패밀리의 7B를 쓰는 것이 자연스럽다.

## 모델

- **Hugging Face**: `Qwen/Qwen2.5-Math-7B-Instruct`
- **서빙**: `docker/vertex-serve/serve.py` — `float16` + `device_map="auto"` (7B 가중치만으로도 대략 **~14GB+** VRAM, KV·오버헤드 포함 시 더 필요)

## GPU 선택 (중요)

- **T4 16GB**: 7B fp16 로드만으로도 빡빡할 수 있어 **OOM·불안정** 가능성이 있다.
- 권장: **L4(24GB)** 또는 **A100** 등 여유 있는 GPU로 엔드포인트 배포.
- 리전·쿼터에 따라 `nvidia-l4`, `nvidia-tesla-a100` 등 사용 가능 여부가 다르다. `gcloud ai endpoints deploy-model --help` 의 `--accelerator` 목록을 확인한다.

## 1) GCS에 가중치 업로드

```powershell
gcloud config set project gen-lang-client-0300734101
# 버킷/프리픽스는 프로젝트에 맞게 수정
python scripts/vertex/upload_hf_model_to_gcs.py `
  --model-id Qwen/Qwen2.5-Math-7B-Instruct `
  --gcs-prefix gs://gen-lang-client-0300734101-aimo-vertex-341687483990/aimo/models/hf/Qwen2.5-Math-7B-Instruct/
```

업로드 후 **Vertex Model**의 `artifact_uri`는 위 경로 **끝에 `/` 포함**한 `gs://.../Qwen2.5-Math-7B-Instruct/` 를 쓴다.

## 2) 서빙 이미지

기존과 동일: Artifact Registry의 `vertex-serve` 이미지. 가중치는 `artifact_uri`로만 바뀐다.

```powershell
gcloud auth configure-docker us-central1-docker.pkg.dev --quiet
docker build -t us-central1-docker.pkg.dev/gen-lang-client-0300734101/aimo/vertex-serve:latest -f docker/vertex-serve/Dockerfile .
docker push us-central1-docker.pkg.dev/gen-lang-client-0300734101/aimo/vertex-serve:latest
```

## 3) Model 업로드 + Endpoint 배포

- `gcloud ai models upload` — `container-image-uri` = 위 이미지, `artifact-uri` = 7B GCS 경로
- `gcloud ai endpoints deploy-model` — **7B에는 L4 이상 권장** (T4 16GB는 OOM 가능)

**G2 (L4 포함 머신)** 예: `g2-standard-4` 는 vCPU·메모리·**L4 1장**이 묶인 타입이라, 리전에 따라 `--accelerator` 없이 머신 타입만 지정하면 된다. (리전·API 버전별로 다를 수 있으니 [Vertex 추론용 컴퓨팅 설정](https://cloud.google.com/vertex-ai/docs/predictions/configure-compute) 과 `gcloud ai endpoints deploy-model --help` 를 본다.)

**N1 + GPU 조합**을 쓸 때는 PowerShell에서 `--accelerator` 가 깨지지 않게 따옴표로 감싼다:

```text
--accelerator="count=1,type=nvidia-l4"
```

(리전에서 L4 미지원이면 A100 등으로 대체.)

## 월 $10 예산으로 보면 (대략)

[Vertex AI 요금](https://cloud.google.com/vertex-ai/pricing) 표준 **온라인 예측 · G2 시리즈**(서울 `asia-northeast3` 등 표에 포함된 리전, USD, 세전·할인 제외):

| 머신 타입 | 대략 단가 |
|-----------|-----------|
| `g2-standard-4` (L4 1장 포함) | **~$0.81/시간** |

역산:

- **$10 ÷ ~$0.81 ≈ 약 12시간/월** — “이 머신으로만 과금”할 때의 **거친 상한**으로 보면 된다.
- **상시 24시간**이면 같은 단가 기준으로 **월 $500~600대** 수준이므로, **필요할 때만 배포 → eval → undeploy**가 전제다.

GCS 보관·네트워크·**같은 결제 계정의 다른 프로젝트** 과금은 별도다. 콘솔에서 **예산 알림(예: 월 $10)** 을 걸어 두는 것을 권장한다.

## 스모크 테스트 가능 여부

가능하다. 단계별로 비용·목적이 다르다.

| 목적 | 방법 | 비고 |
|------|------|------|
| **인프라만** (이미지·엔드포인트·predict 경로) | `python scripts/vertex/track_colab_vertex_smoke_seoul.py` | 기본 `ARTIFACT_URI`는 **tiny-gpt2** GCS 경로(`vertex_common.DEFAULT_SMOKE_ARTIFACT_URI`). 가벼움. |
| **7B 가중치로 동작 확인** | GCS에 7B 업로드 후 `ARTIFACT_URI`를 그 경로로 두고 동일 스크립트 또는 `gcloud`로 Model 업로드·배포 | **G2 등 GPU 과금** 발생. 짧게 쓰고 **undeploy** 권장. |
| **엔드포인트만 이미 떠 있을 때** | `python examples/quick_vertex_endpoint_test.py` | `AIMO_VERTEX_ENDPOINT_ID` 등 설정 필요. 한 줄 predict 스모크. |
| **품질 샘플 1문항** | `python scripts/vertex/eval_vertex_endpoint_quality.py --endpoint-id ... --n-problems 1` | 실제 채점 경로까지 확인. |

환경 변수 요약: 스모크 트래킹 스크립트는 `ARTIFACT_URI`, `SMOKE_PREDICT_TIMEOUT_SECONDS`, `SMOKE_MAX_NEW_TOKENS` 등 — `scripts/vertex/track_colab_vertex_smoke_seoul.py` 상단 주석 참고.

## 4) 로컬·평가 스크립트 기본값

저장소 기본 HF 모델 ID는 `src/pipeline/settings.py` 의 `AIMO_MODEL` 기본값으로 **7B**에 맞춰 두었다.  
1.5B만 돌리려면:

```powershell
$env:AIMO_MODEL = "Qwen/Qwen2.5-Math-1.5B-Instruct"
```

## 관련 문서

- [MERGED_MODEL_ARTIFACT.md](./MERGED_MODEL_ARTIFACT.md) — 아티팩트·업로드 개요
- [EVAL_REAL_MODEL.md](./EVAL_REAL_MODEL.md) — 로컬/Vertex 품질 eval
