"""
Vertex Endpoint inference client (for your fine-tuned Qwen model).

Usage:
  - Set AIMO_VERTEX_ENDPOINT to the full endpoint resource name, e.g.
    projects/PROJECT/locations/us-central1/endpoints/123456789
  - Or set AIMO_VERTEX_ENDPOINT_ID + GOOGLE_CLOUD_PROJECT + GOOGLE_CLOUD_LOCATION

Request protocol:
  instances: [{"prompt": "...", "max_new_tokens": 256}]
Response:
  predictions: [{"text": "..."}]
"""

from __future__ import annotations

import os
import random
import time
from typing import Any, Dict, Optional, Tuple

from .logger import get_logger

logger = get_logger()

DEFAULT_MAX_NEW_TOKENS = int(os.getenv("AIMO_MAX_NEW_TOKENS", "256"))
DEFAULT_TEMPERATURE = float(os.getenv("AIMO_TEMPERATURE", "0.0"))

VERTEX_EP_MAX_RETRIES = int(os.getenv("AIMO_VERTEX_EP_MAX_RETRIES", "8"))
VERTEX_EP_RETRY_BASE_SECONDS = float(os.getenv("AIMO_VERTEX_EP_RETRY_BASE_SECONDS", "1.0"))
VERTEX_EP_RETRY_MAX_SECONDS = float(os.getenv("AIMO_VERTEX_EP_RETRY_MAX_SECONDS", "45.0"))

_CACHED_ENDPOINT: Optional[Tuple[str, Any]] = None  # (endpoint_name, aiplatform.Endpoint)

def _parse_endpoint_name(endpoint_name: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse `projects/{project}/locations/{location}/endpoints/{id}`.
    Returns (project, location) if parsable else (None, None).
    """
    parts = endpoint_name.strip().split("/")
    try:
        p_idx = parts.index("projects")
        l_idx = parts.index("locations")
        project = parts[p_idx + 1]
        location = parts[l_idx + 1]
        return project, location
    except Exception:
        return None, None


def _endpoint_resource_name() -> Optional[str]:
    full = os.getenv("AIMO_VERTEX_ENDPOINT")
    if full and full.strip():
        return full.strip()

    endpoint_id = os.getenv("AIMO_VERTEX_ENDPOINT_ID")
    project = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION") or os.getenv("VERTEX_AI_LOCATION")
    if endpoint_id and project and location:
        return f"projects/{project}/locations/{location}/endpoints/{endpoint_id}"
    return None


def is_vertex_endpoint_configured() -> bool:
    return bool(_endpoint_resource_name())


def predict_vertex_endpoint(prompt: str, max_new_tokens: Optional[int] = None, temperature: Optional[float] = None) -> str:
    """
    Calls Vertex Endpoint (custom container) and returns the 'text' field.
    Uses ADC (Application Default Credentials).
    """
    endpoint_name = _endpoint_resource_name()
    if not endpoint_name:
        raise ValueError("Vertex Endpoint not configured. Set AIMO_VERTEX_ENDPOINT or AIMO_VERTEX_ENDPOINT_ID.")

    max_new = int(max_new_tokens or DEFAULT_MAX_NEW_TOKENS)
    temp = DEFAULT_TEMPERATURE if temperature is None else float(temperature)

    try:
        from google.cloud import aiplatform
        from google.protobuf import json_format
        from google.protobuf.struct_pb2 import Value
    except Exception as e:
        raise RuntimeError(
            "Vertex Endpoint inference requires google-cloud-aiplatform. "
            "Install: python -m pip install -r requirements-vertex-sdk.txt"
        ) from e

    # Cache Endpoint client so 1000-call eval doesn't re-init each time.
    global _CACHED_ENDPOINT
    if _CACHED_ENDPOINT is None or _CACHED_ENDPOINT[0] != endpoint_name:
        # Prefer parsing from endpoint resource name (most reliable).
        parsed_project, parsed_location = _parse_endpoint_name(endpoint_name)

        # Some users temporarily set GOOGLE_CLOUD_LOCATION="..." which breaks the SDK validator.
        env_location = os.getenv("GOOGLE_CLOUD_LOCATION") or os.getenv("VERTEX_AI_LOCATION")
        if env_location and ("..." in env_location or env_location.strip() in {"", "locations", "location"}):
            env_location = None

        project = (
            parsed_project
            or os.getenv("GOOGLE_CLOUD_PROJECT")
            or os.getenv("GCP_PROJECT")
            or "gen-lang-client-0300734101"
        )
        location = parsed_location or env_location or "us-central1"
        aiplatform.init(project=project, location=location)
        _CACHED_ENDPOINT = (endpoint_name, aiplatform.Endpoint(endpoint_name=endpoint_name))
    endpoint = _CACHED_ENDPOINT[1]

    instance: Dict[str, Any] = {"prompt": prompt, "max_new_tokens": max_new, "temperature": temp}
    parameters: Dict[str, Any] = {}

    # Retry on rate limits / transient errors
    last_err: Optional[Exception] = None
    for attempt in range(VERTEX_EP_MAX_RETRIES + 1):
        try:
            response = endpoint.predict(instances=[instance], parameters=parameters)
            # response.predictions can be list of dicts or protobuf Values
            preds = response.predictions or []
            if not preds:
                return ""
            p0 = preds[0]
            if isinstance(p0, dict):
                return p0.get("text") or p0.get("generated_text") or str(p0)
            # protobuf Value -> python dict
            v = Value()
            v.CopyFrom(p0)
            as_dict = json_format.MessageToDict(v)
            return as_dict.get("text") or as_dict.get("generated_text") or str(as_dict)
        except Exception as e:
            last_err = e
            msg = str(e)
            is_rate_limited = (
                "RESOURCE_EXHAUSTED" in msg
                or "429" in msg
                or "Too Many Requests" in msg
                or "rate" in msg.lower()
                or "quota" in msg.lower()
                or "unavailable" in msg.lower()
                or "deadline" in msg.lower()
            )
            if not is_rate_limited or attempt >= VERTEX_EP_MAX_RETRIES:
                break
            sleep_s = min(VERTEX_EP_RETRY_MAX_SECONDS, VERTEX_EP_RETRY_BASE_SECONDS * (2 ** attempt))
            sleep_s = sleep_s * (0.5 + random.random())
            logger.warning(
                "Vertex Endpoint rate-limited/transient (attempt %s/%s). Sleeping %.2fs. Error: %s",
                attempt + 1,
                VERTEX_EP_MAX_RETRIES,
                sleep_s,
                msg[:300],
            )
            time.sleep(sleep_s)

    logger.warning("Vertex Endpoint predict failed: %s", last_err)
    return f"ERROR: Vertex Endpoint inference failed: {last_err}"


def build_answer_only_prompt(problem_text: str) -> str:
    return (
        "You are solving a math problem. "
        "Return ONLY the final answer wrapped in <ANS>...</ANS>.\n"
        "No explanation, no code.\n\n"
        f"Problem:\n{problem_text.strip()}\n"
    )


def predict_vertex_endpoint_answer_only(problem_text: str, max_new_tokens: int = 256) -> Dict[str, Any]:
    """
    Convenience helper for research eval:
      - sends answer-only prompt
      - extracts <ANS> value using AnswerExtractor
    Returns a dict with raw_text, extracted value, predicted_answer.
    """
    from .answer_extraction import AnswerExtractor

    prompt = build_answer_only_prompt(problem_text)
    raw_text = predict_vertex_endpoint(prompt, max_new_tokens=max_new_tokens, temperature=0.0)
    extractor = AnswerExtractor()
    ext = extractor.extract_from_text(raw_text or "")
    pred = ext.value
    pred_str = str(pred) if pred is not None else None
    return {
        "raw_text": raw_text,
        "extracted": {
            "value": pred,
            "format": ext.format,
            "confidence": ext.confidence,
            "error": ext.error,
        },
        "predicted_answer": pred_str,
    }

