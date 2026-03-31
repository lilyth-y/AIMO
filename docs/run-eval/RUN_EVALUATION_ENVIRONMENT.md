# 평가 실행 환경 가이드

**작성일:** 2026-02-22

---

## 1. 지금까지 한 것

- **데이터 셋업**: 실행 완료
  - `data/aime_validation_90.json` (AIME 90문항)
  - `data/numina_eval_balanced.json` (NuminaMath 60문항)
  - `data/numina_training_5k.jsonl` (학습 샘플 5k)
- **Windows 인코딩**: `numina_loader.py`의 이모지(✅) 출력을 `[OK]`로 변경해 cp949 환경에서도 셋업 스크립트가 완료되도록 수정함.
- **로컬 모델 경로**: `solver.py`에서 Windows 절대 경로 형태의 `model_name`은 로컬 경로로 인식해 `local_files_only=True`로 로드하도록 수정함.

---

## 2. 전체 평가를 실행하려면

### 2.1 필요한 것

| 항목 | 내용 |
|------|------|
| **모델** | 코드 기본값은 [`src/pipeline/settings.py`](../../src/pipeline/settings.py): `Qwen/Qwen2.5-Math-7B-Instruct` + 양자화 `8bit`. 실험 예로 MathCoder-L-13B 등 다른 `repo_id`를 `OMI_MODEL`로 둘 수 있음. GPU 권장. |
| **환경 변수** | `OMI_MODEL` / `AIMO_MODEL`, `OMI_QUANTIZATION` / `AIMO_QUANTIZATION`: Hugging Face `repo_id` 또는 **로컬 디렉터리 경로**. |
| **데이터** | 이미 생성됨 (`data/aime_validation_90.json`, `data/numina_eval_balanced.json`). |

### 2.2 모델 설정

- **HuggingFace에서 받아서 쓰는 경우** (캐시 또는 다운로드):
  ```bash
  set OMI_MODEL=MathLLMs/MathCoder-L-13B
  ```
- **이미 로컬 캐시에 있는 경우**:  
  `settings.py` / `config.py`의 기본값이 로컬 경로이면, 수정한 `solver.py`가 해당 경로를 로컬로 인식해 `local_files_only=True`로 로드합니다.  
  **해당 경로가 실제로 존재해야 합니다** (다른 PC에서 복사한 경로면 현재 PC에 맞게 바꿔야 함).

### 2.3 실행 방법

**PowerShell (Windows)** – 환경 변수는 `$env:이름="값"` 사용:

```powershell
cd c:\startingup\AIMO
$env:PYTHONPATH = "c:\startingup\AIMO\src"

# 실제 모델 지정 (Hub 모델 사용 시)
$env:OMI_MODEL = "Qwen/Qwen2-1.5B-Instruct"
$env:MATHCODEORCHESTRATOR_QUANTIZATION = "4bit"

# 문항 수 (기본 5)
$env:MAX_PROBLEMS = "2"

# 코드 실행 샌드박스 메모리 상한 (MB, 기본 2048). 필요 시 3072 등으로 상향
$env:AIMO_EXECUTOR_MEMORY_MB = "2048"

python examples/quick_eval.py
```

**전체 평가:**

```powershell
# NuminaMath 60문
python examples/run_numina_evaluation.py

# AIME 90문
python examples/run_aime_evaluation.py
```

- **시간**: 1.5B 4bit 기준 문제당 수 분, 13B 8bit 기준 1~2분 예상.
- **메모리**: 1.5B 4bit는 GPU 4~6GB, 13B 8bit는 16GB 이상 권장.
- **코드 실행**: 기본 2048MB 제한. 무거운 문제는 `AIMO_EXECUTOR_MEMORY_MB=3072` 등으로 상향 가능.

### 2.4 메모리가 많이 들어가는 구간 (확인용)

| 구간 | 설명 |
|------|------|
| **모델 추론** | 메인 프로세스. GPU VRAM 사용 (1.5B 4bit 약 4~6GB, 13B 8bit 16GB+). |
| **코드 실행(실제 초과 지점)** | **별도 서브프로세스**에서 생성된 Python 코드를 실행. 이 프로세스의 RSS가 `AIMO_EXECUTOR_MEMORY_MB`를 넘으면 `MemoryLimitExceeded`로 종료됨. 즉, **모델이 생성한 코드**가 큰 리스트/행렬/재귀 등으로 메모리를 쓰는 것이 원인. |
| **대응** | (1) `AIMO_EXECUTOR_MEMORY_MB=3072` 등으로 상향 (2) 코드 생성 프롬프트에 "메모리 ~2GB 이하, 큰 리스트 지양" 가이드 반영됨 (Simulator 경로) (3) 초과 시 로그에 해당 코드 앞 400자 출력 → 어떤 코드가 폭증을 일으켰는지 확인 가능. |

### 2.5 로그/트레이싱 (선택)

- **OpenTelemetry**: 기본은 OTLP 전송 비활성화. localhost:4317 연결 시도로 인한 에러를 피하려면 `OMI_OTLP_TRACING`을 설정하지 않으면 됨. 트레이싱이 필요할 때만 `OMI_OTLP_TRACING=1` 로 설정.
- **콘솔 스팬**: `OMI_CONSOLE_TRACING=1` 이면 콘솔에 스팬 출력 (디버깅용).
- **TensorFlow oneDNN**: 평가 스크립트(`quick_eval`, `run_numina_evaluation`, `run_aime_evaluation`)에서 `TF_ENABLE_ONEDNN_OPTS=0` 을 기본 설정해 oneDNN 관련 로그를 줄임.

---

## 3. 현재 환경에서 막혔던 점

1. **모델 이름이 로컬 캐시 경로**(예: `C:/Users/.../snapshots/xxx`)인데, HuggingFace 쪽이 이를 repo_id로 검사해서 `Repo id must be in the form 'repo_name' or 'namespace/repo_name'` 에러가 났음.  
   → **해결**: `solver.py`에서 경로 형태면 로컬로 간주하고 `local_files_only=True`로 로드하도록 수정함.
2. **로컬 경로가 이 PC에 없음**: 다른 사용자/다른 PC의 캐시 경로가 설정에 있으면 `os.path.exists`가 False이고, 예전에는 repo_id로 넘어가 에러가 났음.  
   → **해결**: 경로 형태이면 repo_id 검사 없이 로컬 로드 시도. 경로가 없으면 그때는 로드 실패. 이 경우 `OMI_MODEL=MathLLMs/MathCoder-L-13B` 로 바꾸면 Hub에서 받아서 사용 가능.

---

## 4. 모델 없이 평가 파이프라인만 검증하기 (Mock)

실제 LLM 없이 데이터 로드 → 메트릭 계산 → 저장까지 확인하려면:

- **Mock 솔버 사용**: `examples/mock_eval.py` 참고.  
  오케스트레이터의 `solver`를 `MockSolver()`로 바꾼 뒤, `data/numina_eval_balanced.json` 등으로 평가 스크립트와 동일한 방식으로 실행하면 됨.
- **1문항만**: `examples/quick_eval.py`에서 `max_problems=1`로 두고, 모델만 Mock으로 바꾸면 1문항 기준으로 파이프라인만 빠르게 검증 가능.

---

## 5. 한 줄 요약

- **데이터**: 셋업 완료. AIME 90, Numina 60 사용 가능.
- **전체 평가 실행**: `OMI_MODEL`을 HuggingFace repo id(예: `MathLLMs/MathCoder-L-13B`) 또는 **실제로 존재하는** 로컬 경로로 두고, 위처럼 실행하면 됨.
- **지금 환경이 어렵다면**:  
  - 로컬에 13B 모델이 없고, GPU/메모리가 부족하면 → Mock 평가로 파이프라인만 돌리거나,  
  - 더 작은 모델(예: 1.5B)로 `OMI_MODEL`을 바꿔서 적은 문항으로 먼저 테스트하는 방법을 권장.
