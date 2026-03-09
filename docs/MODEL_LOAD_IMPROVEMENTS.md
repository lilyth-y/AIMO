# 모델 로드 개선 (2026-02-23)

## 1. 적용한 변경

### 1) 8bit + CPU 오프로드 (solver.py)

- **BitsAndBytesConfig(8bit)**  
  - `llm_int8_enable_fp32_cpu_offload=True` 추가 (기본값, `AIMO_LLM_INT8_CPU_OFFLOAD=0`으로 끌 수 있음).  
  - GPU 메모리 부족 시 CPU로 일부를 32-bit로 오프로드.

- **from_pretrained 실패 시 재시도**  
  - "CPU or the disk", "device_map", "llm_int8_enable_fp32_cpu_offload" 관련 오류가 나면  
    `max_memory={0: "{gpu_gb}GiB", "cpu": "20GiB"}` 로 한 번 더 시도.

### 2) chat_template 없을 때 우회 (solver.py)

- **tokenizer.chat_template** 이 없으면 (MathCoder 등)  
  - `pipe(messages, ...)` 대신 **`pipe(formatted_prompt, ...)`** 로 호출.  
- `pipe(messages, ...)` 호출 중 chat_template 예외가 나면  
  - 자동으로 `pipe(formatted_prompt, ...)` 로 한 번 더 시도.

## 2. 결과

- **이전:** "Some modules are dispatched on the CPU or the disk" 등으로 모델 로드 실패 → 에러 메시지를 print하는 코드가 실행되어 32가 추출됨.
- **이후:**  
  - "Model loaded successfully", "Pipeline ready" 로 정상 로드.  
  - "Some parameters are on the meta device because they were offloaded to the cpu" 는 정상 동작.  
  - chat_template 오류 없이 문자열 프롬프트로 생성 진행.

## 3. 환경 변수

| 변수 | 의미 | 기본값 |
|------|------|--------|
| `AIMO_LLM_INT8_CPU_OFFLOAD` | 8bit 시 CPU 오프로드 사용 여부 | `1` (사용) |
| `AIMO_MAX_NEW_TOKENS` | 생성 최대 토큰 수 (낮추면 빠름, 품질 하락) | `512` |
| `AIMO_FAST_EVAL` | `1` 이면 Quick Eval 1문항만 실행 | `0` |
| `OMI_MODEL` | 모델 repo_id. 작은 모델로 바꾸면 훨씬 빠름 | `MathLLMs/MathCoder-L-13B` |

CPU 오프로드를 끄려면 `AIMO_LLM_INT8_CPU_OFFLOAD=0` (GPU 메모리 충분할 때만).

**느릴 때:** CPU 오프로드 사용 시 13B는 매우 느림. 빠른 평가 예:
- `AIMO_FAST_EVAL=1` → 1문항만
- `AIMO_MAX_NEW_TOKENS=256` → 생성 짧게
- `OMI_MODEL=Qwen/Qwen2.5-Coder-1.5B-Instruct` → 작은 모델 (CPU 오프로드 없이 빠름)
