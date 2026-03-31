"""
Remote inference client: call an external HTTP API for generate(prompt).
Use when OMI_REMOTE_INFERENCE_URL is set (no local GPU needed; computing engine is remote).
"""

import os
import json
import time
from typing import Optional

from .logger import get_logger

logger = get_logger()

# Expected request: POST JSON {"prompt": str, "max_new_tokens": int (optional)}
# Expected response: JSON {"text": str} or {"generated_text": str} or plain text
DEFAULT_MAX_NEW_TOKENS = 16384
REQUEST_TIMEOUT = 120


def generate_remote(prompt: str, url: Optional[str] = None, **kwargs) -> str:
    """
    Call remote inference API. Returns generated text.

    url: from OMI_REMOTE_INFERENCE_URL if not passed
    kwargs: optional max_new_tokens, timeout
    """
    url = url or os.getenv("OMI_REMOTE_INFERENCE_URL")
    if not url or not url.strip():
        raise ValueError("OMI_REMOTE_INFERENCE_URL is not set")

    max_tokens = kwargs.get("max_new_tokens", DEFAULT_MAX_NEW_TOKENS)
    timeout = kwargs.get("timeout", REQUEST_TIMEOUT)

    try:
        import urllib.request
        body = json.dumps({"prompt": prompt, "max_new_tokens": max_tokens}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
    except Exception as e:
        logger.warning("Remote inference request failed: %s", e)
        return f"ERROR: Remote inference failed: {e}"

    try:
        data = json.loads(raw)
        return data.get("text") or data.get("generated_text") or data.get("output") or raw
    except json.JSONDecodeError:
        return raw.strip()


def is_remote_inference_configured() -> bool:
    """Return True if OMI_REMOTE_INFERENCE_URL is set."""
    return bool(os.getenv("OMI_REMOTE_INFERENCE_URL", "").strip())
