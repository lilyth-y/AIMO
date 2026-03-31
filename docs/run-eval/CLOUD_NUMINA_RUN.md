# Numina 평가 — 클라우드 전용 실행 가이드 (AIMO)

개인 노트북 GPU로 `run_numina_evaluation.py`를 돌리지 않고, **GCP·Kaggle 등 클라우드**에서만 돌리는 절차입니다. (프로젝트 규칙: `.cursor/rules/aimo-cloud-eval-only.mdc`)

## 무엇을 쓰나

| 방식 | 추론 | 비고 |
|------|------|------|
| **Vertex AI (Gemini)** | 관리형 API | `solver.generate()`가 Vertex를 먼저 탐 (`docs/run-eval/VERTEX_AI.md`) |
| **Kaggle 노트북** | 런타임 GPU 또는 게이트웨이 | `notebooks/run_numina_on_kaggle.ipynb` |

Vertex가 잡히면 **로컬 HF 7B 로드 없이** API 호출만 한다. 로그에 `Loading checkpoint shards`가 나오면 **Vertex 설정이 안 된 것**이니 아래 환경 변수를 다시 확인한다.

## 경로 A: GCP Cloud Shell / GCE / Workbench (Vertex Gemini)

### 0) 반드시 저장소 루트에 있는지 확인

`requirements.txt` / `scripts/eval/run_numina_vertex_cloud.sh` 가 없다면 **디렉터리가 잘못됐거나 클론이 없는 것**이다.

```bash
git clone https://github.com/lilyth-y/AIMO.git
cd AIMO
git pull   # scripts/eval/·문서가 없으면 최신 브랜치를 당긴다
test -f requirements.txt && test -f scripts/eval/run_numina_vertex_cloud.sh && echo OK || echo "WRONG DIRECTORY — cd into AIMO repo root"
```

이후 모든 `pip` / `python` / `bash scripts/...` 는 **`cd AIMO` 한 뒤** 실행한다.

### 0.5) GCP 고정 프로필·연결 스모크 (권장)

프로젝트·버킷·엔드포인트 ID·리전 정리: [../vertex/AIMO_GCP_PROFILE.md](../vertex/AIMO_GCP_PROFILE.md).  
의존성을 최소로 깐 뒤 **연결만** 확인하려면 (Cloud Shell):

```bash
cd ~/AIMO
# requirements-cloudshell-smoke.txt 로 PYTHONPATH 설정했다면 그대로
bash scripts/vertex/run_aimo_gcp_smoke.sh
```

성공 시 Vertex SDK·Gemini·엔드포인트 호출이 한 번씩 통과한다. 이후 §1에서 전체 스택을 설치하고 Numina를 돌린다.

### 1) 의존성 설치

#### Cloud Shell 주의 (`/home` 약 5GB)

- `requirements.txt`에는 **torch·transformers·CUDA 휠** 등이 포함되어 **수 GB**를 쓴다. `pip install --user`는 **`~/.local`(홈 디스크)** 에 쌓여 **`No space left on device`** 가 나기 쉽다.
- **Vertex 연동만 먼저 확인**할 때는 **전체 `requirements.txt`를 홈에 설치하지 말 것.**

**A) Vertex 스모크만 (최소, 권장 첫 단계)**

패키지는 **홈이 아니라 `/tmp`** 에 두고, 캐시도 `/tmp` 로 보낸다.

```bash
cd ~/AIMO   # 저장소 루트
export PIP_CACHE_DIR=/tmp/pip-cache
mkdir -p /tmp/aimo-pypi
python3 -m pip install --target /tmp/aimo-pypi -r requirements-cloudshell-smoke.txt
export PYTHONPATH="/tmp/aimo-pypi:${PYTHONPATH}"
export GOOGLE_CLOUD_PROJECT=gen-lang-client-0300734101
export GOOGLE_CLOUD_LOCATION=us-central1
python3 examples/quick_vertex_test.py
```

**B) 전체 스택을 Cloud Shell에서 꼭 쓸 때 (orchestrator + `run_numina_evaluation.py`)**

홈 대신 **루트 파일시스템이 넉넉한 경로**에 한 번에 설치한다 (예: `/tmp/aimo-pypi`).

```bash
cd ~/AIMO
export PIP_CACHE_DIR=/tmp/pip-cache
mkdir -p /tmp/aimo-pypi
python3 -m pip install --target /tmp/aimo-pypi -r requirements.txt -r requirements-vertex.txt
export PYTHONPATH="/tmp/aimo-pypi:${PYTHONPATH}"
```

이후 같은 셸에서 `python3 examples/run_numina_evaluation.py ...` 실행. (**세션 끝나면 `/tmp`가 비워질 수 있어**, 장시간 작업은 **디스크 큰 GCE/Workbench** 권장.)

**C) 디스크 넉넉한 GCE / Workbench**

`pip install --user -r requirements.txt` 등 기존 방식 가능. `requirements-vertex.txt`는 **반드시 `cd ~/AIMO` 후** `pip install -r requirements-vertex.txt` 로 경로를 맞출 것.

### 2) 인증 (GCE VM이면 보통 생략)

- **GCE / GKE 노드 등 GCP VM**: 인스턴스에 붙은 **서비스 계정**이 ADC로 자동 사용된다. `gcloud auth application-default login` 은 **필요 없고**, 개인 계정으로 로그인하면 동료에게 토큰이 노출될 수 있어 비권장이다.
- **Cloud Shell / 로컬 개발 머신**: `gcloud auth application-default login` 또는 Express용 `export GOOGLE_GENAI_API_KEY=...` (`VERTEX_AI.md`).

### 3) 프로젝트·리전 (예시)

   ```bash
   export GOOGLE_CLOUD_PROJECT=gen-lang-client-0300734101
   export GOOGLE_CLOUD_LOCATION=us-central1
   export VERTEX_AI_MODEL=gemini-2.5-flash-lite   # 필요 시 변경
   ```

### 4) 인프로세스·50문제 (모델은 프로세스당 한 번만 로드)

저장소 루트에서:

```bash
export AIMO_EVAL_IN_PROCESS=1
export MAX_PROBLEMS=50
python examples/run_numina_evaluation.py --data-file numina_eval_balanced.json
```

또는 (루트에서만):

```bash
bash scripts/eval/run_numina_vertex_cloud.sh
```

스크립트가 없다면 위 `python examples/...` 한 줄만으로 동일하다.

### 5) 결과

`results/numina_eval_balanced_results.json` (데이터 파일 stem에 따라 파일명이 달라질 수 있음).

### GCE에서 본 오류 정리

| 증상 | 원인 | 조치 |
|------|------|------|
| `No such file ... requirements.txt` | 루트가 아님 | `cd` 로 AIMO 루트, `test -f requirements.txt` |
| `run_numina_vertex_cloud.sh: No such file` | 옛 클론 또는 루트 아님 | `git pull`, 루트에서 `ls scripts/eval/` |
| `Defaulting to user installation` | 시스템 site-packages 쓰기 불가 | 정상; `--user` 또는 venv 사용 |
| `No space left on device` (설치 중) | `requirements.txt` + `--user` 가 홈을 채움 | **Cloud Shell에서는 `requirements.txt`를 홈에 전부 설치하지 말 것**; 위 **§1 A/B** 참고 |
| `requirements-vertex.txt` 없음 | 루트가 아님 | `cd ~/AIMO` 후 `-r` 실행 |

## 경로 B: Kaggle

- 노트북: `notebooks/run_numina_on_kaggle.ipynb` 업로드 후 단계 실행.
- 체크리스트: `KAGGLE_실행_체크리스트.md`, `KAGGLE_RUN.md`.

## 비용·쿼터

- Gemini/Vertex 호출은 **건당 과금**이므로 문제 수·출력 토큰 상한(`AIMO_MAX_NEW_TOKENS` 등)을 문서 `RUN_OPTIONS_BUDGET.md`와 맞춰 조절한다.

## 관련 문서

- `VERTEX_AI.md` — 환경 변수·인증·동작 순서
- `README_AIMO_EVAL.md` — 평가 개요
