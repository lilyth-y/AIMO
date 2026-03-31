"""
Minimal Vertex AI custom container prediction server for HF causal LM.

Protocol:
  POST /predict
  Body: {"instances":[{"prompt":"...","max_new_tokens":8192}]}
  Returns: {"predictions":[{"text":"..."}]}  # 생성 토큰만 (프롬프트 제외)

환경변수 AIMO_MAX_NEW_TOKENS (기본 8192):
  - 0 / 빈 값 / none → 프롬프트 제외 후 **모델 컨텍스트에 들어갈 만큼** (상한은 AIMO_MAX_NEW_TOKENS_HARD_CAP, 기본 32768)
  - 그 외 → 요청한 상한과 (컨텍스트−입력 길이) 중 작은 값

Model loading:
  - If AIP_STORAGE_URI is set to gs://... (artifact_uri), downloads into /model
  - Else uses /model as-is
  - Loads HF model from /model (expected: merged model dir)

시작 시 프리로드 (권장):
  - AIMO_PRELOAD_MODEL=1 (기본): 앱 기동 시 _load_model() 실행 → 첫 predict가 60초 게이트웨이
    한도에 걸리지 않도록 함 (Vertex 온라인 추론은 첫 요청에서 지연이 크면 503이 나기 쉬움).
  - AIMO_PRELOAD_MODEL=0: 지연 로드(구동은 빠르나 첫 predict가 매우 느릴 수 있음).
"""

from __future__ import annotations

import os
import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


MODEL_DIR = Path(os.getenv("AIMO_MODEL_DIR", "/model"))
PORT = int(os.getenv("AIP_HTTP_PORT") or os.getenv("PORT") or "8080")


def _parse_default_max_new_tokens() -> int:
    raw = (os.getenv("AIMO_MAX_NEW_TOKENS") or "8192").strip().lower()
    if raw in ("", "0", "none", "unlimited", "max"):
        return 0
    return int(raw)


DEFAULT_MAX_NEW_TOKENS = _parse_default_max_new_tokens()
DEFAULT_TEMPERATURE = float(os.getenv("AIMO_TEMPERATURE", "0.0"))

_tokenizer = None
_model = None


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """HTTP 수신 전에 모델을 올려 두면 첫 predict가 로드 시간을 겹쳐 쓰지 않음."""
    preload = os.getenv("AIMO_PRELOAD_MODEL", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )
    if preload:
        try:
            _load_model()
        except Exception as e:
            # 기동 실패는 로그로 남기고, 첫 predict에서 재시도 가능하도록 계속 기동할지
            # 운영에서는 실패 시 프로세스 종료가 나을 수 있음.
            import sys

            print(f"[serve] AIMO_PRELOAD_MODEL: load failed: {e}", file=sys.stderr)
            raise
    yield


app = FastAPI(lifespan=_lifespan)


def _download_gcs_prefix(gcs_uri: str, dst_dir: Path) -> None:
    from google.cloud import storage

    if not gcs_uri.startswith("gs://"):
        raise ValueError(f"Not a GCS URI: {gcs_uri}")
    _, _, rest = gcs_uri.partition("gs://")
    bucket, _, prefix = rest.partition("/")
    client = storage.Client()
    b = client.bucket(bucket)
    blobs = list(client.list_blobs(bucket, prefix=prefix))
    if not blobs:
        raise RuntimeError(f"No blobs found under {gcs_uri}")
    dst_dir.mkdir(parents=True, exist_ok=True)
    for blob in blobs:
        if blob.name.endswith("/"):
            continue
        rel = blob.name[len(prefix) :].lstrip("/")
        out_path = dst_dir / rel
        out_path.parent.mkdir(parents=True, exist_ok=True)
        blob.download_to_filename(str(out_path))


def _ensure_model_present() -> None:
    # Vertex passes the model artifact location as AIP_STORAGE_URI (gs://...).
    gcs_uri = os.getenv("AIP_STORAGE_URI")
    if gcs_uri and gcs_uri.startswith("gs://"):
        # If model dir already looks populated, skip download.
        if MODEL_DIR.exists() and any(MODEL_DIR.iterdir()):
            return
        _download_gcs_prefix(gcs_uri, MODEL_DIR)


def _load_model() -> None:
    global _tokenizer, _model
    if _model is not None and _tokenizer is not None:
        return

    _ensure_model_present()
    if not MODEL_DIR.exists():
        raise RuntimeError(f"MODEL_DIR not found: {MODEL_DIR}")

    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM

    _tokenizer = AutoTokenizer.from_pretrained(str(MODEL_DIR), trust_remote_code=True)
    if _tokenizer.pad_token is None:
        _tokenizer.pad_token = _tokenizer.eos_token

    # CPU 스모크 테스트를 위해 CUDA 유무에 따라 dtype를 자동 선택합니다.
    # (tiny 모델은 float32 CPU로도 동작합니다.)
    dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    # Load with device_map auto (GPU preferred on Vertex if available)
    _model = AutoModelForCausalLM.from_pretrained(
        str(MODEL_DIR),
        trust_remote_code=True,
        device_map="auto",
        torch_dtype=dtype,
    )
    _model.eval()


def _resolve_max_new_tokens(requested: int, input_len: int, model) -> int:
    """
    requested <= 0 이면 프롬프트를 뺀 나머지 컨텍스트를 최대한 사용(상한 HARD_CAP).
    그 외에는 요청값과 물리적 상한 중 작은 값.
    """
    max_pos = int(getattr(model.config, "max_position_embeddings", 8192))
    hard = int(os.getenv("AIMO_MAX_NEW_TOKENS_HARD_CAP", "32768"))
    room = max(1, max_pos - input_len - 2)
    room = min(room, hard)
    if requested <= 0:
        return room
    return min(int(requested), room)


class PredictInstance(BaseModel):
    prompt: str
    max_new_tokens: Optional[int] = None
    temperature: Optional[float] = None


class PredictRequest(BaseModel):
    instances: List[PredictInstance]


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/endpoints/{endpoint_id}/deployedModels/{deployed_model_id}")
def vertex_readiness_probe(endpoint_id: str, deployed_model_id: str) -> Dict[str, str]:
    """
    Vertex online prediction health/readiness probes this path on the container.
    Returning 404 caused deploy LRO: FAILED_TO_DEPLOY (model server never became ready).
    """
    return {"status": "READY"}


def _predict_impl(req: PredictRequest) -> Dict[str, Any]:
    """Shared prediction implementation for multiple Vertex routes."""
    try:
        _load_model()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"model_load_failed: {e}")

    import torch

    preds: List[Dict[str, str]] = []
    for inst in req.instances:
        prompt = inst.prompt
        raw_max = DEFAULT_MAX_NEW_TOKENS if inst.max_new_tokens is None else int(inst.max_new_tokens)
        temperature = DEFAULT_TEMPERATURE if inst.temperature is None else float(inst.temperature)

        inputs = _tokenizer(prompt, return_tensors="pt")
        # Move tensors to model device
        inputs = {k: v.to(_model.device) for k, v in inputs.items()}
        input_len = int(inputs["input_ids"].shape[1])
        max_new_eff = _resolve_max_new_tokens(raw_max, input_len, _model)

        do_sample = temperature > 0.0
        with torch.no_grad():
            out = _model.generate(
                **inputs,
                max_new_tokens=max_new_eff,
                do_sample=do_sample,
                temperature=float(temperature) if do_sample else None,
                pad_token_id=_tokenizer.pad_token_id,
            )
        # 프롬프트+생성 전체가 아니라 **새로 생성된 토큰만** 반환 (평가·<ANS> 추출에 필요)
        gen_ids = out[0, input_len:]
        text = _tokenizer.decode(gen_ids, skip_special_tokens=True)
        preds.append({"text": text})

    return {"predictions": preds}


@app.post("/predict")
def predict(req: PredictRequest) -> Dict[str, Any]:
    # Backward-compatible route.
    return _predict_impl(req)


@app.post("/v1/endpoints/{endpoint_id}/deployedModels/{deployed_model_id}:predict")
def vertex_predict(endpoint_id: str, deployed_model_id: str, req: PredictRequest) -> Dict[str, Any]:
    # Vertex Online Prediction for custom containers calls this route.
    return _predict_impl(req)


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    main()

