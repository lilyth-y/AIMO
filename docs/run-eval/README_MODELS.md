# AIMO 모델 선택·양자화·실행 경로

Hugging Face 기준 **모델 ID**와 **`src/pipeline/settings.py`** 의 환경 변수를 맞춘다. (구 문서의 `MathCodeOrchestrator_MODEL` 등은 사용하지 않는다.)

## 환경 변수 (코드 기준)

| 변수 | 설명 |
|------|------|
| `OMI_MODEL` | 사용할 모델: Hugging Face `repo_id` 또는 로컬 절대 경로 |
| `AIMO_MODEL` | `OMI_MODEL`이 없을 때만 사용 (폴백) |
| `OMI_QUANTIZATION` | `4bit`, `8bit`, `none` (또는 빈 문자열) |
| `AIMO_QUANTIZATION` | 양자화 폴백 |

기본값: 모델 `Qwen/Qwen2.5-Math-7B-Instruct`, 양자화 `8bit`. VRAM이 부족하면 아래처럼 1.5B·4bit를 지정한다.

## 예시 (PowerShell)

### 스모크·저VRAM (1.5B)

```powershell
$env:OMI_MODEL="Qwen/Qwen2.5-Math-1.5B-Instruct"
$env:OMI_QUANTIZATION="4bit"
$env:CUDA_VISIBLE_DEVICES="0"
python examples/run_numina_evaluation.py
```

### 기본 7B (8bit)

```powershell
$env:OMI_MODEL="Qwen/Qwen2.5-Math-7B-Instruct"
$env:OMI_QUANTIZATION="8bit"
$env:CUDA_VISIBLE_DEVICES="0"
python examples/run_numina_evaluation.py
```

### AIME 평가

```powershell
$env:OMI_MODEL="Qwen/Qwen2.5-Math-1.5B-Instruct"
python examples/run_aime_evaluation.py
```

### 빠른 소규모 평가

```powershell
python examples/quick_eval.py
```

## 필요한 패키지

### 4-bit/8-bit 양자화

```powershell
pip install bitsandbytes accelerate
```

### GPU (CUDA 12.1 예시)

```powershell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

## 파인튜닝·데이터 레이아웃

### 디렉터리 예시

```
data/
├── numina_eval_balanced.json   # Numina 평가셋
├── finetune/                   # 학습용 JSONL (실험별)
│   └── ...
└── ...
```

### JSONL 한 줄 형식 (예시)

```json
{"problem": "Solve x+2=5 for x.", "solution": "```python\nx = 5 - 2\nprint(x)\n```", "answer": "3"}
```

QLoRA·Vertex 학습 절차는 [`docs/finetuning-resources/FINETUNING_GUIDE.md`](../finetuning-resources/FINETUNING_GUIDE.md), 커스텀 학습 이미지는 [`docker/vertex-train/`](../../docker/vertex-train/) 를 본다.

## VRAM 사용량 (대략)

| 규모 | Precision | VRAM (대략) |
|------|-----------|-------------|
| 1.5B Math | FP16 | ~4GB |
| 7B Math | 4-bit | ~6GB |
| 7B Math | 8-bit | 그 이상 |

## 그 밖의 파이프라인 설정

Refine 루프·실행 타임아웃·로그 경로 등은 모두 `settings.py`를 따른다. 루트 [`README.md`](../../README.md) 환경 변수 표를 참고한다.

## 원격·클라우드 추론

로컬 GPU 없이 평가하려면 [`docs/finetuning-resources/EXTERNAL_COMPUTE_OPTIONS.md`](../finetuning-resources/EXTERNAL_COMPUTE_OPTIONS.md) 를 본다. Vertex에 **커스텀 엔드포인트**로 올린 모델은 `docs/vertex/` 및 `scripts/vertex/` 경로와 연동된다.
