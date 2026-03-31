# %% [markdown]
# # AIMO — Qwen2.5-Math-1.5B QLoRA Fine-tuning
# 
# **환경**: Kaggle (T4 16GB) 또는 Google Colab
# **모델**: Qwen/Qwen2.5-Math-1.5B-Instruct
# **데이터**: NuminaMath-1.5 (~896K 수학 문제)
# **방법**: QLoRA (4-bit 양자화 + LoRA 어댑터)

# %% [markdown]
# ## 1. 패키지 설치

# %%
!pip install -q torch transformers datasets accelerate peft trl bitsandbytes wandb

# %% [markdown]
# ## 2. 설정

# %%
import os
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    TrainingArguments,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer, SFTConfig
from datasets import load_dataset

# --- CONFIG ---
MODEL_NAME = "Qwen/Qwen2.5-Math-1.5B-Instruct"
OUTPUT_DIR = "./qwen-math-lora"
MAX_SEQ_LEN = 1024
BATCH_SIZE = 4
GRAD_ACCUM = 4        # effective batch = 16
LEARNING_RATE = 2e-4
NUM_EPOCHS = 1
LORA_R = 16
LORA_ALPHA = 32
LORA_DROPOUT = 0.05
MAX_TRAIN_SAMPLES = 50000  # 전체 896K 중 5만개로 시작 (시간 절약)

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Device: {device}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

# %% [markdown]
# ## 3. 데이터 로드 및 전처리

# %%
print("Loading NuminaMath-1.5...")
dataset = load_dataset("AI-MO/NuminaMath-1.5", split="train")
print(f"Full dataset: {len(dataset)} problems")

# 풀이형 문제만 필터 (proof 제외)
dataset = dataset.filter(lambda x: x.get("question_type") != "proof")
print(f"After filtering proofs: {len(dataset)} problems")

# 샘플링 (학습 시간 제어)
if MAX_TRAIN_SAMPLES and len(dataset) > MAX_TRAIN_SAMPLES:
    dataset = dataset.shuffle(seed=42).select(range(MAX_TRAIN_SAMPLES))
    print(f"Sampled: {len(dataset)} problems")

# 학습/검증 분리
split = dataset.train_test_split(test_size=0.02, seed=42)
train_dataset = split["train"]
eval_dataset = split["test"]
print(f"Train: {len(train_dataset)}, Eval: {len(eval_dataset)}")

# %%
def format_problem(example):
    """NuminaMath 문제를 Chat 형식으로 변환"""
    problem = example.get("problem", "")
    solution = example.get("solution", "")
    answer = example.get("answer", "")
    
    # System + User + Assistant 형식
    text = (
        "<|im_start|>system\n"
        "Please reason step by step, and put your final answer within \\boxed{}.<|im_end|>\n"
        "<|im_start|>user\n"
        f"{problem}<|im_end|>\n"
        "<|im_start|>assistant\n"
        f"{solution}\n\n"
        f"The answer is $\\boxed{{{answer}}}$<|im_end|>"
    )
    return {"text": text}

train_dataset = train_dataset.map(format_problem)
eval_dataset = eval_dataset.map(format_problem)

print("Sample training text (first 500 chars):")
print(train_dataset[0]["text"][:500])

# %% [markdown]
# ## 4. 모델 로드 (4-bit 양자화)

# %%
# 4-bit 양자화 설정
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
)

print(f"Loading model: {MODEL_NAME}...")
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

if torch.cuda.is_available():
    mem = torch.cuda.memory_allocated() / 1024**3
    print(f"Model loaded — GPU memory: {mem:.2f} GB")

# %% [markdown]
# ## 5. LoRA 설정

# %%
lora_config = LoraConfig(
    r=LORA_R,
    lora_alpha=LORA_ALPHA,
    lora_dropout=LORA_DROPOUT,
    bias="none",
    task_type="CAUSAL_LM",
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# %% [markdown]
# ## 6. 학습

# %%
training_args = SFTConfig(
    output_dir=OUTPUT_DIR,
    num_train_epochs=NUM_EPOCHS,
    per_device_train_batch_size=BATCH_SIZE,
    gradient_accumulation_steps=GRAD_ACCUM,
    learning_rate=LEARNING_RATE,
    weight_decay=0.01,
    warmup_ratio=0.03,
    lr_scheduler_type="cosine",
    logging_steps=10,
    save_steps=500,
    eval_strategy="steps",
    eval_steps=500,
    save_total_limit=2,
    fp16=True,
    max_seq_length=MAX_SEQ_LEN,
    dataset_text_field="text",
    report_to="none",  # "wandb" 으로 변경하면 W&B 로깅 가능
    gradient_checkpointing=True,
)

trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    processing_class=tokenizer,
)

print("Starting training...")
trainer.train()
print("Training complete!")

# %% [markdown]
# ## 7. 저장 및 업로드

# %%
# LoRA 어댑터만 저장 (소용량)
model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)
print(f"LoRA adapter saved to {OUTPUT_DIR}")

# 파일 크기 확인
import os
total_size = sum(os.path.getsize(os.path.join(OUTPUT_DIR, f)) for f in os.listdir(OUTPUT_DIR))
print(f"Adapter size: {total_size / 1024 / 1024:.1f} MB")

# %% [markdown]
# ## 8. 테스트 추론

# %%
from peft import PeftModel

# 베이스 모델 + LoRA 어댑터 로드
test_model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True,
)
test_model = PeftModel.from_pretrained(test_model, OUTPUT_DIR)

# 테스트 문제
test_problem = "Find all integers n such that n^2 + 3n + 5 is divisible by 121."
messages = [
    {"role": "system", "content": "Please reason step by step, and put your final answer within \\boxed{}."},
    {"role": "user", "content": test_problem},
]

text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = tokenizer([text], return_tensors="pt").to(test_model.device)

with torch.no_grad():
    output = test_model.generate(**inputs, max_new_tokens=512, temperature=0.7, do_sample=True)

response = tokenizer.decode(output[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
print(f"Problem: {test_problem}")
print(f"Response:\n{response}")

# %% [markdown]
# ## 9. HuggingFace Hub 업로드 (선택)
# 
# ```python
# model.push_to_hub("your-username/qwen-math-1.5b-numina-lora")
# tokenizer.push_to_hub("your-username/qwen-math-1.5b-numina-lora")
# ```
