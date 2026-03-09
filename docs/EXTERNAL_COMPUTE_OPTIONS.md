# 외부 컴퓨팅 엔진 / SHA 기반 재현성

**목적:** 로컬 GPU 없이 또는 SHA로 재현 가능하게 평가를 돌리기 위한 옵션 정리.

---

## 1. SHA로 재현 가능하게 하기

- **평가 결과에 SHA 포함:**  
  `save_gradient_and_error_summary()`가 호출될 때마다 `get_run_revision()`으로  
  `sha`, `short_sha`, `dirty`, `ref`를 구해 **gradient_report JSON**에 `run_revision`으로 넣습니다.
- **아티팩트 이름에 SHA 사용:**  
  GitHub Actions `eval-on-release` 워크플로는 결과를 `eval-<short_sha>` 이름으로 업로드합니다.
- **같은 SHA = 같은 코드 버전:**  
  나중에 `git checkout <sha>` 후 같은 데이터·모델로 다시 돌리면 재현 비교가 가능합니다.

---

## 2. 컴퓨팅 엔진 옵션

### 2.1 GitHub Actions (SHA 기반 아티팩트)

- **워크플로:** `.github/workflows/eval-on-release.yml`
- **트리거:**  
  - 태그 푸시 `eval/*` (예: `eval/v1.0`)  
  - 또는 수동 실행 `workflow_dispatch` (옵션: `max_problems`, `model`)
- **동작:**  
  - checkout → 현재 커밋 SHA 계산 → (데이터 있으면) `quick_eval.py` 실행  
  - `results/` + gradient report를 모아 **아티팩트 `eval-<short_sha>`** 로 업로드 (30일 보관)
- **제한:**  
  - 기본 `ubuntu-latest` 러너는 **GPU 없음**.  
  - 실제 모델 추론은 느리거나 OOM 날 수 있음.  
  - **GPU 러너**를 쓰려면: GitHub에서 self-hosted runner (GPU 장비) 연결 후 `runs-on: self-hosted` 등으로 이 워크플로만 GPU 러너에서 돌리면 됨.

→ **정리:** “SHA 가지고 computing engine” = **같은 SHA로 돌린 평가 결과를 아티팩트로 남기고, 나중에 그 SHA로 다시 돌려서 비교**하는 용도로 쓰면 됨.

### 2.2 원격 추론 API (로컬 GPU 없이)

- **의도:**  
  모델 추론만 외부 서비스에 맡기고, OMI 파이프라인(라우팅·검증·평가)은 로컬/CI에서 실행.
- **구현:**  
  - `OMI_REMOTE_INFERENCE_URL` 이 설정되면, Solver는 로컬 HuggingFace 대신 해당 URL로 `generate(prompt)` 요청을 보냄.  
  - 응답 텍스트를 그대로 파이프라인에 넘기므로, **어떤 백엔드(Replicate, Together, HF Inference, 자체 서버)든 동일 인터페이스로 붙일 수 있음.**
- **추천 후보:**  
  - **HuggingFace Inference API** (모델 페이지에서 “Deploy” → Inference API)  
  - **Replicate** (모델별 API, 결제 시 사용)  
  - **Together** (호스팅 추론 API)  
  - **자체 서버:** FastAPI 등으로 `POST /generate` 같은 엔드포인트 하나 만들고, 위 URL을 가리키게 하면 됨.

→ **정리:** “computing engine”을 **원격 API**로 쓰고 싶으면, 지금은 **`OMI_REMOTE_INFERENCE_URL` 하나로 통일**해서 쓰는 방식이 좋음 (아래 3절).

### 2.3 Docker + 클라우드 (이미지에 SHA 태그)

- **이미지 태그에 SHA 넣기:**  
  `docker build -t aimo:$SHORT_SHA .`  
  → 같은 SHA로 빌드한 이미지로 클라우드(GCP Cloud Run, AWS ECS, Lambda 등)에서 실행하면 재현 가능.
- **실행:**  
  클라우드에서 해당 이미지로 컨테이너 띄우고, `quick_eval.py` 또는 AIME/Numina 스크립트 실행.  
  결과·gradient report는 볼륨/스토리지에 저장하고, 필요하면 아티팩트처럼 **이름에 SHA 포함** (예: `results_<short_sha>.json`).

---

## 3. 원격 추론 URL 사용 (OMI_REMOTE_INFERENCE_URL)

- **환경 변수:**  
  `OMI_REMOTE_INFERENCE_URL` = `https://your-inference-endpoint/generate` 형태
- **동작:**  
  이 변수가 설정되어 있으면, Solver는 로컬 모델 대신 이 URL로 HTTP POST 요청을 보내고, 응답 본문을 생성 텍스트로 사용합니다.  
  (요청/응답 형식은 `src/pipeline/remote_inference.py` 또는 Solver 내부 주석 참고)
- **장점:**  
  로컬/CI에는 GPU가 없어도 되고, “computing engine”을 Replicate·HF·Together·자체 서버 등 **어디로든 바꿀 수 있음**.  
  평가 스크립트와 gradient report·SHA 로깅은 그대로 둔 채, **추론만 외부로** 빼는 형태.

---

## 4. 어떤 걸 쓰면 좋을지

| 목적 | 추천 |
|------|------|
| **같은 코드로 재현·비교** | SHA를 gradient report와 아티팩트 이름에 넣어 두기 (이미 반영됨). 필요 시 `eval-on-release` 워크플로로 태그/수동 실행. |
| **로컬에 GPU 없음** | `OMI_REMOTE_INFERENCE_URL` 로 추론만 외부 API에 맡기기. |
| **CI에서 주기적 평가** | `eval-on-release` 를 schedule 또는 태그로 돌리고, GPU self-hosted runner 또는 원격 추론 URL 사용. |
| **완전한 재현 (코드+환경)** | Docker 이미지를 `aimo:<short_sha>` 로 빌드해 클라우드에서 실행. |

필요하면 Replicate/Together/HF Inference 중 하나를 골라, 해당 서비스의 엔드포인트를 `OMI_REMOTE_INFERENCE_URL` 로 두면 “SHA + computing engine” 구성을 그대로 유지할 수 있습니다.
