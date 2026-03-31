from __future__ import annotations

import traceback

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def main() -> int:
    # gcloud storage cp -r 로컬 내려받기 과정에서 디렉토리가 한 번 더 중첩될 수 있음.
    # config.json 등이 최상위로 있는 실제 경로를 사용합니다.
    path = "tmp_vertex_smoke_tiny_gpt2/tiny-gpt2/tiny-gpt2"
    print("loading from:", path)
    # 컨테이너에서는 torch.cuda.is_available()에 따라 dtype을 고를 수 있어,
    # 로컬에서도 float16 재현을 먼저 시도합니다.
    dtype = torch.float16
    print("cuda?", torch.cuda.is_available(), "dtype:", dtype)

    try:
        tok = AutoTokenizer.from_pretrained(path, trust_remote_code=True)
        print("tokenizer OK; pad_token:", tok.pad_token)
        if tok.pad_token is None:
            tok.pad_token = tok.eos_token

        _model = AutoModelForCausalLM.from_pretrained(
            path,
            trust_remote_code=True,
            device_map="auto",
            torch_dtype=dtype,
        )
        _model.eval()
        print("model loaded OK")
        return 0
    except Exception as e:
        print("LOAD ERROR:", repr(e))
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

