# GCP 인증 (Vertex / Custom Job)

키·JSON 서비스 계정 파일은 **리포지토리에 넣지 말고**, 로컬 또는 CI 시크릿에만 둡니다.

**프로젝트·버킷·엔드포인트 ID·리전(Gemini vs 서울) 고정값**은 [AIMO_GCP_PROFILE.md](AIMO_GCP_PROFILE.md)에 정리해 두었다. 여기서는 인증 방법만 다룬다.

## 방식 A: Application Default Credentials (ADC)

개발 PC·**Cloud Shell**·GCE 등에서 동일하게 쓴다.

```powershell
gcloud auth application-default login
gcloud config set project gen-lang-client-0300734101
```

Python SDK(`google-cloud-aiplatform`, `google-genai`)는 보통 ADC를 자동으로 씁니다.  
`gcloud auth application-default print-access-token` 이 되면 `vertex_env_check.py`도 동일하게 동작하는 경우가 많습니다.

## 방식 B: 서비스 계정 JSON (CI·헤드리스)

```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:\secure\sa.json"
$env:GOOGLE_CLOUD_PROJECT = "gen-lang-client-0300734101"
$env:GOOGLE_CLOUD_LOCATION = "asia-northeast3"
```

(프로젝트·리전은 [AIMO_GCP_PROFILE.md](AIMO_GCP_PROFILE.md)와 맞출 것. 엔드포인트·Job은 `asia-northeast3`, Vertex Gemini 단독 세션은 `us-central1`일 수 있음.)

`GOOGLE_APPLICATION_CREDENTIALS`가 설정되면 ADC가 이 키를 사용합니다.

## 권장 환경 변수 (평가·Job 제출)

| 변수 | 설명 |
|------|------|
| `GOOGLE_CLOUD_PROJECT` | 프로젝트 ID (고정 예: `gen-lang-client-0300734101`) |
| `GOOGLE_CLOUD_LOCATION` | **용도별로 다름**: 엔드포인트·Custom Job·`aiplatform` → `asia-northeast3` 권장; Vertex Gemini(`generate_vertex`)만 → `us-central1` 권장 ([AIMO_GCP_PROFILE.md](AIMO_GCP_PROFILE.md) §리전을 둘로 나누는 이유). |
| `GOOGLE_APPLICATION_CREDENTIALS` | (선택) SA JSON 경로 |
| `AIMO_VERTEX_ENDPOINT_ID` | Online Prediction 엔드포인트 ID (`eval_vertex_endpoint_quality`용; 프로필 예: `2486393813610790912`) |
| `VERTEX_AI_MODEL` | (선택) Gemini 모델 ID; 기본 `gemini-2.5-flash-lite` |

`scripts/vertex/vertex_common.py`의 기본값은 **서울 리전·프로젝트**에 맞춰져 있다. `src/pipeline/vertex_inference.py` 기본 리전은 **`us-central1`** 이다 — 혼동 시 프로필 문서를 본다.

## 확인 순서

1. 한 번에(권장): `python scripts/vertex/run_vertex_checks.py --project gen-lang-client-0300734101 --location asia-northeast3`  
   - 엔드포인트 preflight까지 보려면 같은 셸에 `AIMO_VERTEX_ENDPOINT_ID` 를 설정하거나 [AIMO_GCP_PROFILE.md](AIMO_GCP_PROFILE.md) 의 값을 맞춘다.
2. 개별: `python scripts/vertex/preflight_vertex.py` → `python scripts/vertex/vertex_env_check.py --project ... --location ...`

성공 시 마지막에 `OK: all Vertex checks passed` 및 `OK: Vertex SDK 연결 성공` 이 출력됩니다.

인증 후 **한 번에** 점검은 **Cloud Shell** 등에서 `scripts/vertex/run_aimo_gcp_smoke.sh` ([AIMO_GCP_PROFILE.md](AIMO_GCP_PROFILE.md)). 로컬 PC에서 돌리지 않는 것을 기본으로 한다.

### Gemini 스모크 404 (`Publisher Model ... was not found`)

`src/pipeline/vertex_inference.py` 기본 리전은 **`us-central1`**, 기본 모델은 **`gemini-2.5-flash-lite`** 이다. 리전마다 노출 모델이 다르므로, `GOOGLE_CLOUD_LOCATION=asia-northeast3` 등에서 **`scripts/vertex/smoke_gemini_once.py` 가 404**이면 아래 중 하나를 쓴다.

- `GOOGLE_CLOUD_LOCATION=us-central1` (또는 리전 미설정 시 코드 기본값과 동일)
- 또는 해당 리전에 배포된 모델 ID로 `VERTEX_AI_MODEL` 설정

## 다음 단계

- Vertex 문서 목록: [README.md](README.md)
- 엔드포인트 품질 평가·Ralph 게이트: [../run-eval/RALPH_VERTEX.md](../run-eval/RALPH_VERTEX.md)
- API 활성화: `gcloud services enable aiplatform.googleapis.com`
