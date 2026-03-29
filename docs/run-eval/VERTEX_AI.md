# Vertex AI 연동 가이드 (AIMO)

AIMO 파이프라인에서 GCP Vertex AI(Gemini)를 추론 백엔드로 사용하는 방법입니다.

## GCP 프로젝트 정보

| 항목 | 값 |
|------|-----|
| 프로젝트 ID | `gen-lang-client-0300734101` |
| 프로젝트 번호 | 341687483990 |
| 기본 리전 | `us-central1` |
| 기본 모델 | `gemini-2.5-flash-lite` |

## 환경 변수

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `GOOGLE_CLOUD_PROJECT` 또는 `GCP_PROJECT` | GCP 프로젝트 ID | `gen-lang-client-0300734101` |
| `GOOGLE_CLOUD_LOCATION` 또는 `VERTEX_AI_LOCATION` | Vertex AI 리전 | `us-central1` |
| `VERTEX_AI_MODEL` | 사용할 Gemini 모델 | `gemini-2.5-flash-lite` |
| `GOOGLE_GENAI_API_KEY` 또는 `VERTEX_AI_API_KEY` | (선택) Express 모드용 API 키 | - |
| `AIMO_MAX_NEW_TOKENS` | 최대 출력 토큰 수 | `16384` |

Vertex가 **사용되는 조건**: `GOOGLE_CLOUD_PROJECT` 또는 `GCP_PROJECT` 또는 API 키 중 하나가 설정되어 있어야 합니다.

## 인증

### 1) ADC (Application Default Credentials, 권장)

로컬/CI에서 gcloud로 로그인한 경우:

```bash
gcloud auth application-default login
```

프로젝트를 지정하려면:

```bash
export GOOGLE_CLOUD_PROJECT=gen-lang-client-0300734101
export GOOGLE_CLOUD_LOCATION=us-central1
```

ADC가 설정되어 있으면 별도 API 키 없이 Vertex AI 호출이 가능합니다.

### 2) API 키 (Express 모드)

Vertex AI Express 모드용 API 키가 있다면:

```bash
export GOOGLE_GENAI_API_KEY="your-api-key"
# 또는
export VERTEX_AI_API_KEY="your-api-key"
```

프로젝트/리전은 위와 같이 설정할 수 있습니다.

## 의존성

Vertex 추론을 쓰려면 `google-genai` 패키지가 필요합니다.

```bash
# 저장소 루트에서 실행 (경로 오류 나면 cd 로 루트인지 확인)
pip install -r requirements-vertex.txt
# 또는
pip install google-genai
```

**Google Cloud Shell 등 `/home` 용량이 작은 환경**: 전체 `requirements.txt`를 홈에 설치하면 디스크가 부족해질 수 있다. **Vertex 스모크만** 할 때는 루트의 `requirements-cloudshell-smoke.txt`와 절차 **`docs/run-eval/CLOUD_NUMINA_RUN.md` §1 A**를 따른다.

## 동작 순서

solver의 `generate()` 호출 시 사용 순서는 다음과 같습니다.

1. **Vertex AI** — `is_vertex_configured()`가 True이면 `generate_vertex()` 사용
2. **Remote URL** — `OMI_REMOTE_INFERENCE_URL`이 설정되어 있으면 해당 URL 사용
3. **로컬 파이프라인** — 그 외에는 로컬 HuggingFace 파이프라인 사용

Vertex를 쓰고 싶다면 `GOOGLE_CLOUD_PROJECT`(또는 `GCP_PROJECT`) 또는 API 키를 설정하면 됩니다.

## 빠른 테스트

연동이 되는지 확인하려면 (비용 최소: 짧은 질문 + 출력 50토큰):

```bash
pip install -r requirements-vertex.txt
set GOOGLE_CLOUD_PROJECT=gen-lang-client-0300734101
python examples/quick_vertex_test.py
```

성공 시 `OK - Vertex 연동 정상 동작` 이 출력됩니다.

## 예산 알림 (비용 관리)

- GCP 콘솔 → **결제** → **예산 및 알림** 에서 월 예산(예: $10, $50) 설정 후 알림을 걸어 두면 과금 방지에 유리합니다.
- Vertex AI 요금: [Vertex AI 요금](https://cloud.google.com/vertex-ai/generative-ai/pricing) 참고. Gemini 2.5 Flash-Lite 기준 소량 테스트는 수 cents 수준입니다.

## 404 NOT_FOUND / 모델을 찾을 수 없음

- **Vertex AI API 사용 설정**: GCP 콘솔 → **API 및 서비스** → **라이브러리** → "Vertex AI API" 검색 후 사용 설정.
- **모델 ID**: 기본값은 `gemini-2.5-flash-lite` 입니다.
  - 빠른/저비용(권장): `VERTEX_AI_MODEL=gemini-2.5-flash-lite`
  - 프리뷰: `VERTEX_AI_MODEL=gemini-2.5-flash-lite-preview-09-2025`
- 프로젝트/리전에 따라 사용 가능한 모델이 다를 수 있습니다. [Vertex AI 사용 가능 모델](https://cloud.google.com/vertex-ai/generative-ai/docs/learn/model-versions) 참고.

## 참고

- Vertex AI SDK: [Google Gen AI Python](https://googleapis.github.io/python-genai/)
- Vertex 문서: [Generative AI on Vertex AI](https://cloud.google.com/vertex-ai/generative-ai/docs)
- 코드: `src/pipeline/vertex_inference.py`, `src/pipeline/solver.py` (Vertex 분기)
