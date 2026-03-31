# AIMO GCP 고정 프로필 (레포·실계정 기준)

GitHub: `https://github.com/lilyth-y/AIMO.git` — Cloud Shell 등에서 `git clone` 후 루트에서 스크립트를 실행한다.

`gcloud`·Vertex API로 **확인한 값**을 기본으로 쓴다. 프로젝트가 바뀌면 본 문서와 [GCP_AUTH.md](GCP_AUTH.md)를 함께 갱신한다.

## 실행 위치 (로컬 지양)

**스모크·평가·모델 추론**은 **로컬 개발 PC에서 기본 실행하지 않는다.**  
인증·스크립트 실행은 **Google Cloud Shell, GCE, Vertex Custom Job, CI** 등 **GCP 안**을 우선한다. 로컬에서는 저장소 편집·커밋·(선택) 단위 테스트 정도만 둔다.

[Hugging Face 로컬 로드](../experiments/ARM_AB_PROTOCOL.md)도 동일하게 **선택**이며, 정책상 **클라우드만**이면 Arm A(HF)는 생략한다.

| 항목 | 값 |
|------|-----|
| **프로젝트 ID** | `gen-lang-client-0300734101` |
| **GCS 버킷** (스테이징·데이터 공용) | `gs://gen-lang-client-0300734101-aimo-vertex-341687483990/` |
| **Online Prediction 엔드포인트** (서울) | ID `2486393813610790912` · displayName `aimo-endpoint-seoul-smoke-redeploy-1774097346` · 리전 `asia-northeast3` |

## 리전을 둘로 나누는 이유

| 용도 | 리전 | 이유 |
|------|------|------|
| **Vertex Gemini** (`vertex_inference.generate_vertex`, Numina+Gemini) | **`us-central1`** | 기본 모델 `gemini-2.5-flash-lite` 등이 **서울 리전에서 404**인 경우가 있음 (동일 프로젝트라도 퍼블리셔 모델 노출이 리전별로 다름). |
| **Vertex AI Platform** (엔드포인트, Custom Job, `aiplatform`) | **`asia-northeast3`** | 실제 엔드포인트·잡이 서울에 배포된 경우가 많음. `gcloud config` 기본 compute region과도 맞춤. |

**한 셸에서** `GOOGLE_CLOUD_LOCATION` 은 **하나만** 쓰이므로, Gemini 스크립트와 엔드포인트 스크립트를 **같은 터미널에서 섞지 말고**, 아래 블록 중 **하나만** 로드한다.

## PowerShell — Gemini 전용 세션

```powershell
$env:GOOGLE_CLOUD_PROJECT = "gen-lang-client-0300734101"
$env:GOOGLE_CLOUD_LOCATION = "us-central1"
# 선택: 모델 고정
# $env:VERTEX_AI_MODEL = "gemini-2.5-flash-lite"
```

## PowerShell — 엔드포인트·eval_vertex_endpoint_quality·서울 리소스

```powershell
$env:GOOGLE_CLOUD_PROJECT = "gen-lang-client-0300734101"
$env:GOOGLE_CLOUD_LOCATION = "asia-northeast3"
$env:AIMO_VERTEX_ENDPOINT_ID = "2486393813610790912"
```

## Custom Job 예시 (버킷·리전만 고정)

`--project gen-lang-client-0300734101`  
`--location asia-northeast3`  
`--staging-bucket gs://gen-lang-client-0300734101-aimo-vertex-341687483990/vertex-staging`  
`--gcs-data-uri` / `--gcs-output-uri` / `--gcs-summary-uri` 는 **같은 버킷** 아래 경로로 두면 된다 (데이터 파일은 업로드 후 URI 지정).

### vertex-eval 이미지 빌드 (Cloud Build — 로컬 Docker 불필요)

Artifact Registry에 `aimo` 리포지토리가 있어야 한다. **Cloud Shell**에서 레포 루트:

```bash
gcloud builds submit --project=gen-lang-client-0300734101 --region=asia-northeast3 \
  --config=docker/vertex-eval/cloudbuild.yaml \
  --substitutions=_IMAGE=asia-northeast3-docker.pkg.dev/gen-lang-client-0300734101/aimo/vertex-eval:latest \
  .
```

완료 후 `--container-image` 에 위 URI를 그대로 쓴다 ([RALPH_VERTEX.md](../run-eval/RALPH_VERTEX.md) 의 `submit_vertex_eval_job.py` 예시).

### Job 제출 (한 줄 예시)

데이터가 `gs://gen-lang-client-0300734101-aimo-vertex-341687483990/aimo/data/numinamath_full.jsonl` 에 있다고 할 때:

```bash
python scripts/vertex/submit_vertex_eval_job.py \
  --project gen-lang-client-0300734101 --location asia-northeast3 \
  --container-image asia-northeast3-docker.pkg.dev/gen-lang-client-0300734101/aimo/vertex-eval:latest \
  --staging-bucket gs://gen-lang-client-0300734101-aimo-vertex-341687483990/vertex-staging \
  --endpoint-id 2486393813610790912 \
  --gcs-data-uri gs://gen-lang-client-0300734101-aimo-vertex-341687483990/aimo/data/numinamath_full.jsonl \
  --gcs-output-uri gs://gen-lang-client-0300734101-aimo-vertex-341687483990/aimo/results/vertex_eval_run.jsonl \
  --gcs-summary-uri gs://gen-lang-client-0300734101-aimo-vertex-341687483990/aimo/results/vertex_summary.json \
  --write-summary-json /tmp/vertex_summary.json \
  --n-problems 20 --data-file numinamath_full.jsonl
```

`--enforce-ralph-accuracy` 는 목표·데이터가 맞을 때만 추가한다. 비용·시간은 `n-problems` 로 조절.

## 확인 명령 (재검증)

```powershell
gcloud config get-value project
gcloud ai endpoints list --region=asia-northeast3 --project=gen-lang-client-0300734101
gcloud storage buckets list --project=gen-lang-client-0300734101
```

## 자동 스모크 (한 번에)

**권장 — Cloud Shell** (레포 클론 후 루트에서):

```bash
chmod +x scripts/vertex/run_aimo_gcp_smoke.sh
./scripts/vertex/run_aimo_gcp_smoke.sh
```

순서: `run_vertex_checks`(서울) → `smoke_gemini_once`(us-central1) → `quick_vertex_endpoint_test`(서울). 프로젝트에 대한 권한이 있어야 한다.

### `run_aimo_gcp_smoke.sh` 가 없을 때

GitHub에 해당 파일이 **아직 푸시되지 않았거나**, **다른 브랜치만** 클론된 경우입니다. 로컬에서 `main`/`changes` 등에 커밋·푸시한 뒤 Cloud Shell에서:

```bash
cd ~/AIMO
git fetch origin
git checkout origin/<브랜치명>   # 스크립트가 있는 브랜치
# 또는: git pull origin main
ls scripts/vertex/run_aimo_gcp_smoke.sh
```

**스크립트 없이도** 아래를 **한 줄씩** 복사해 실행하면 동일하다 (저장소 루트·`python3` 사용):

```bash
cd ~/AIMO
export GOOGLE_CLOUD_PROJECT="gen-lang-client-0300734101"
export GOOGLE_CLOUD_LOCATION="asia-northeast3"
export AIMO_VERTEX_ENDPOINT_ID="2486393813610790912"
python3 scripts/vertex/run_vertex_checks.py --project gen-lang-client-0300734101 --location asia-northeast3
export GOOGLE_CLOUD_LOCATION="us-central1"
python3 scripts/vertex/smoke_gemini_once.py
export GOOGLE_CLOUD_LOCATION="asia-northeast3"
export AIMO_VERTEX_ENDPOINT_ID="2486393813610790912"
python3 examples/quick_vertex_endpoint_test.py
```

(`google-genai` 등이 없으면 `pip install -r requirements-cloudshell-smoke.txt` 또는 [CLOUD_NUMINA_RUN.md](../run-eval/CLOUD_NUMINA_RUN.md) §1 A) 를 먼저 따른다.)

### 흔한 실수

- URL과 `git clone`을 **한 줄에 붙여 넣지 말 것** — `git clone https://github.com/lilyth-y/AIMO.git` 만 실행한다.
- `AIMO` 폴더가 이미 있으면 `git clone` 대신 `cd AIMO && git pull` 로 갱신한다.

**Windows 로컬만** PowerShell 스크립트를 쓸 수 있을 때(비권장·선택):

```powershell
.\scripts\vertex\run_aimo_gcp_smoke.ps1
```

환경만 적용 (PowerShell):

```powershell
. .\scripts\vertex\apply_aimo_gcp_env.ps1 -Profile Gemini
# 또는
. .\scripts\vertex\apply_aimo_gcp_env.ps1 -Profile Seoul
```

---

*엔드포인트 ID·버킷 이름은 `gcloud`로 조회한 시점의 스냅샷이다. 삭제·재배포 후 바뀌면 `endpoints list`로 다시 확인한다.*
