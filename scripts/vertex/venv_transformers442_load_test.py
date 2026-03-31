from __future__ import annotations

import sys
import traceback

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def load_one(path: str) -> int:
    print("PATH:", path)
    try:
        tok = AutoTokenizer.from_pretrained(path, trust_remote_code=True)
        print("tokenizer:", type(tok).__name__, "pad_token:", tok.pad_token)
    except Exception as e:
        print("TOKENIZER_ERROR:", repr(e))
        traceback.print_exc()
        return 1

    try:
        model = AutoModelForCausalLM.from_pretrained(
            path,
            trust_remote_code=True,
            device_map="auto",
            torch_dtype=torch.float32,
        )
        model.eval()
        print("MODEL_OK:", type(model).__name__)
        return 0
    except Exception as e:
        print("MODEL_ERROR:", repr(e))
        traceback.print_exc()
        return 1


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python ... <path>")
        return 2
    return load_one(sys.argv[1])


if __name__ == "__main__":
    raise SystemExit(main())

