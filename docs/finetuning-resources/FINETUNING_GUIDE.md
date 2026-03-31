# AIMO 모델 파인튜닝 가이드

## 개요

AIMO에서 사용하는 수학/코드 생성 모델을 **우리 데이터와 문제 스타일**에 맞게 추가 학습시키는 방법을 정리합니다.  
전체 모델을 다시 학습하는 대신 **QLoRA**(4-bit 양자화 + LoRA)로 **어댑터만** 학습해 GPU 메모리를 적게 쓰고, 학습된 어댑터만 저장·배포합니다.

---

## 1. 파인튜닝이 필요한 이유

- **베이스 모델**: 일반 수학/코드 데이터로 미리 학습됨.
- **AIMO 파이프라인**: MathCodeOrchestrator 스타일(코드 생성 → 실행 → 검증, 단계별 추론)에 맞는 출력이 필요.
- **파인튜닝**: “문제 → (추론 단계 + 코드 + `\boxed{정답}`)” 형식에 맞게 **추가 학습**해 정확도와 형식 일치를 높입니다.

---

## 2. 사용하는 방법: QLoRA

| 항목 | 설명 |
|------|------|
| **QLoRA** | 모델은 4-bit로 양자화해 로드하고, **LoRA 어댑터**만 학습. VRAM 절약. |
| **데이터** | NuminaMath-1.5 (HuggingFace `AI-MO/NuminaMath-1.5`) 또는 프로젝트 `data/` 의 JSONL. |
| **형식** | 문제 + 풀이 + 정답을 Chat 템플릿(시스템/유저/어시스턴트)으로 변환해 SFT. |
| **실행 환경** | Kaggle (T4 16GB), Google Colab, 또는 로컬 GPU 16GB 권장. |

---

## 3. 단계별 절차

### 3.1 환경 준비

```bash
pip install torch transformers datasets accelerate peft trl bitsandbytes
# 선택: wandb (학습 로깅)
```

- **GPU**: CUDA 사용 가능한 환경. 16GB VRAM 권장 (1.5B QLoRA 기준 약 10GB 내외 사용).

### 3.2 데이터 준비

**옵션 A — HuggingFace NuminaMath-1.5**

```python
from datasets import load_dataset
dataset = load_dataset("AI-MO/NuminaMath-1.5", split="train")
# 풀이형만 사용 시: proof 타입 제외
dataset = dataset.filter(lambda x: x.get("question_type") != "proof")
```

**옵션 B — 로컬 JSONL (프로젝트 형식)**

- `data/finetune/train.jsonl`, `val.jsonl`  
- 한 줄에 한 개 JSON: `{"problem": "...", "solution": "...", "answer": "..."}`

### 3.3 입력 형식으로 변환

모델이 기대하는 **채팅 형식**으로 바꿉니다. (Qwen 예시)

```python
def format_problem(example):
    problem = example.get("problem", "")
    solution = example.get("solution", "")
    answer = example.get("answer", "")
    text = (
        "<|im_start|>system\n"
        "Please reason step by step, and put your final answer within \\boxed{}.<|im_end|>\n"
        "<|im_start|>user\n" + problem + "<|im_end|>\n"
        "<|im_start|>assistant\n" + solution + "\n\nThe answer is $\\boxed{" + answer + "}$<|im_end|>"
    )
    return {"text": text}
```

- 학습/검증 데이터셋에 `.map(format_problem)` 적용.

### 3.4 모델 로드 (4-bit 양자화)

```python
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import prepare_model_for_kbit_training

MODEL_NAME = "Qwen/Qwen2.5-Math-1.5B-Instruct"
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True,
)
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
model = prepare_model_for_kbit_training(model)
```

### 3.5 LoRA 설정

```python
from peft import LoraConfig, get_peft_model

lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
)
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()  # 학습 파라미터 수 확인
```

### 3.6 학습 실행

```python
from trl import SFTTrainer, SFTConfig

training_args = SFTConfig(
    output_dir="./qwen-math-lora",
    num_train_epochs=1,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,   # effective batch 16
    learning_rate=2e-4,
    weight_decay=0.01,
    warmup_ratio=0.03,
    lr_scheduler_type="cosine",
    logging_steps=10,
    save_steps=500,
    eval_strategy="steps",
    eval_steps=500,
    save_total_limit=2,
    fp16=True,
    max_seq_length=1024,
    dataset_text_field="text",
    gradient_checkpointing=True,
)
trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    processing_class=tokenizer,
)
trainer.train()
```

### 3.7 저장 및 추론에 사용

- **저장**: `model.save_pretrained("./qwen-math-lora")`, `tokenizer.save_pretrained("./qwen-math-lora")`  
  → 어댑터만 저장되므로 용량은 수십~수백 MB 수준.
- **추론**: 베이스 모델 다시 로드 후 `PeftModel.from_pretrained(model, "./qwen-math-lora")` 로 어댑터만 붙여서 사용.

---

## 4. 프로젝트 내 실행 경로

| 목적 | 경로 |
|------|------|
| **노트북 (QLoRA 전체 플로우)** | `notebooks/train_qlora.py` 또는 `notebooks/train_qlora.ipynb` |
| **학습 데이터 형식 안내** | `docs/run-eval/README_MODELS.md` — `data/finetune/train.jsonl` 형식 |
| **데이터셋 준비** | `scripts/setup_numina_dataset.py`, `src/data/numina_loader.py` (Numina 평가/학습 데이터) |

- **실제 학습**: Kaggle/Colab에서는 `notebooks/train_qlora.ipynb` 실행, 로컬에서는 동일 내용을 `train_qlora.py`로 실행하면 됩니다.

---

## 5. 권장 하이퍼파라미터 (참고)

| 항목 | 권장값 | 비고 |
|------|--------|------|
| LoRA r | 16 | 키/밸류 등 타깃 모듈 차원 |
| LoRA alpha | 32 | 스케일 (보통 2*r) |
| learning_rate | 2e-4 | 1e-4 ~ 3e-4 범위에서 실험 |
| batch size (effective) | 16 | 메모리에 맞게 per_device × grad_accum |
| max_seq_length | 1024 | 긴 풀이는 2048까지 확장 가능 |
| epochs | 1 | 데이터 많으면 2~3 가능 |

---

## 6. 파인튜닝 후 연동

- 학습된 LoRA 어댑터 경로를 파이프라인/솔버 설정에서 **모델 경로**로 지정.
- `src/pipeline/model_config.py`, `settings.py` 등에서 `OMI_MODEL` 또는 해당 모델 로더가 **PEFT 어댑터 디렉터리**를 읽도록 설정하면, 평가·추론 시 파인튜닝된 모델이 사용됩니다.

정리하면: **데이터 수집 → 형식 변환 → QLoRA 학습 → 어댑터 저장 → 파이프라인에 경로 설정** 순서로 진행하면 됩니다.
