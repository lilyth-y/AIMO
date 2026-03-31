"""
Vertex Custom Training entrypoint: QLoRA SFT for Qwen (numeric-only answers).

Expected inputs (GCS or local paths):
  --train_jsonl, --dev_jsonl : JSONL with {"prompt": "...", "completion": "<ANS>..</ANS>", ...}
Output:
  --output_dir : saves adapter + merged (optional) to local FS; caller should upload to GCS.

This script is intentionally minimal and reproducible for PD research.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Dict, List


def _read_jsonl(path: str) -> List[Dict]:
    rows: List[Dict] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _ensure_local(path: str, workdir: Path) -> str:
    """
    If path is gs://, download to workdir using google-cloud-storage.
    Otherwise return path as-is.
    """
    if not path.startswith("gs://"):
        return path

    from google.cloud import storage

    # Parse gs://bucket/key
    _, _, rest = path.partition("gs://")
    bucket, _, blob = rest.partition("/")
    if not bucket or not blob:
        raise ValueError(f"Invalid GCS path: {path}")

    out = workdir / Path(blob).name
    out.parent.mkdir(parents=True, exist_ok=True)
    client = storage.Client()
    client.bucket(bucket).blob(blob).download_to_filename(str(out))
    return str(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base_model", type=str, default=os.getenv("AIMO_BASE_MODEL", "Qwen/Qwen2.5-Math-7B-Instruct"))
    ap.add_argument("--train_jsonl", type=str, required=True)
    ap.add_argument("--dev_jsonl", type=str, required=True)
    ap.add_argument("--output_dir", type=str, required=True)
    ap.add_argument("--max_seq_len", type=int, default=2048)
    ap.add_argument("--epochs", type=float, default=1.0)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--batch_size", type=int, default=1)
    ap.add_argument("--grad_accum", type=int, default=16)
    ap.add_argument("--lora_r", type=int, default=16)
    ap.add_argument("--lora_alpha", type=int, default=32)
    ap.add_argument("--lora_dropout", type=float, default=0.05)
    ap.add_argument("--save_merged", action="store_true")
    ap.add_argument("--gcs_output", type=str, default=os.getenv("AIMO_GCS_OUTPUT", ""), help="Optional gs://... upload target")
    args = ap.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    workdir = out_dir / "_work"
    workdir.mkdir(parents=True, exist_ok=True)

    train_path = _ensure_local(args.train_jsonl, workdir)
    dev_path = _ensure_local(args.dev_jsonl, workdir)

    from datasets import Dataset

    train_rows = _read_jsonl(train_path)
    dev_rows = _read_jsonl(dev_path)

    # Concatenate prompt+completion as a single "text" field for SFT
    def to_text(r: Dict) -> Dict:
        return {"text": f"{r['prompt']}\n{r['completion']}"}

    train_ds = Dataset.from_list([to_text(r) for r in train_rows])
    dev_ds = Dataset.from_list([to_text(r) for r in dev_rows])

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TrainingArguments
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from trl import SFTTrainer

    bnb = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    tokenizer = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        quantization_config=bnb,
        device_map="auto",
        trust_remote_code=True,
    )
    model = prepare_model_for_kbit_training(model)

    lora = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    )
    model = get_peft_model(model, lora)

    training_args = TrainingArguments(
        output_dir=str(out_dir / "trainer_out"),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        logging_steps=10,
        save_steps=200,
        evaluation_strategy="steps",
        eval_steps=200,
        bf16=False,
        fp16=True,
        report_to=[],
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_ds,
        eval_dataset=dev_ds,
        dataset_text_field="text",
        max_seq_length=args.max_seq_len,
        args=training_args,
    )

    trainer.train()

    adapter_dir = out_dir / "adapter"
    adapter_dir.mkdir(parents=True, exist_ok=True)
    trainer.model.save_pretrained(str(adapter_dir))
    tokenizer.save_pretrained(str(adapter_dir))

    if args.save_merged:
        merged_dir = out_dir / "merged"
        merged_dir.mkdir(parents=True, exist_ok=True)
        merged = trainer.model.merge_and_unload()
        merged.save_pretrained(str(merged_dir), safe_serialization=True)
        tokenizer.save_pretrained(str(merged_dir))

    # Optional upload to GCS
    if args.gcs_output and args.gcs_output.startswith("gs://"):
        from google.cloud import storage

        _, _, rest = args.gcs_output.partition("gs://")
        bucket, _, prefix = rest.partition("/")
        client = storage.Client()
        b = client.bucket(bucket)

        def upload_dir(local_dir: Path, gcs_prefix: str):
            for p in local_dir.rglob("*"):
                if p.is_dir():
                    continue
                rel = p.relative_to(local_dir).as_posix()
                blob_name = f"{gcs_prefix.rstrip('/')}/{local_dir.name}/{rel}"
                b.blob(blob_name).upload_from_filename(str(p))

        upload_dir(adapter_dir, prefix or "aimo-qwen")
        if args.save_merged:
            upload_dir(out_dir / "merged", prefix or "aimo-qwen")

    print("OK: training finished")
    print(f"adapter_dir={adapter_dir}")
    if args.save_merged:
        print(f"merged_dir={out_dir / 'merged'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

