"""
Vertex AI (Gemini) inference backend for AIMO.
Use when GOOGLE_CLOUD_PROJECT is set and optionally VERTEX_AI_MODEL.
Falls back to remote URL or local model if Vertex is unavailable.
"""

import os
import random
import time
import concurrent.futures
from typing import Any, Optional, Tuple

from .logger import get_logger

logger = get_logger()

# Reuse google-genai Client across many generate_vertex calls (same process, same auth).
_CACHED_GENAI: Optional[Tuple[Tuple[str, str, str], Any]] = None

# Defaults for AIMO GCP project (override with env)
DEFAULT_GCP_PROJECT = "gen-lang-client-0300734101"
DEFAULT_VERTEX_LOCATION = "us-central1"
DEFAULT_VERTEX_MODEL = "gemini-2.5-flash-lite"
MAX_OUTPUT_TOKENS = int(os.getenv("AIMO_MAX_NEW_TOKENS", "16384"))
VERTEX_MAX_RETRIES = int(os.getenv("AIMO_VERTEX_MAX_RETRIES", "6"))
VERTEX_RETRY_BASE_SECONDS = float(os.getenv("AIMO_VERTEX_RETRY_BASE_SECONDS", "1.0"))
VERTEX_RETRY_MAX_SECONDS = float(os.getenv("AIMO_VERTEX_RETRY_MAX_SECONDS", "30.0"))
VERTEX_REQUEST_TIMEOUT_SEC = float(os.getenv("AIMO_VERTEX_REQUEST_TIMEOUT_SEC", "60.0"))
_LAST_RATE_LIMIT_SIGNAL = False


def is_vertex_configured() -> bool:
    """True if Vertex AI should be used (project or API key set)."""
    project = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT")
    api_key = os.getenv("GOOGLE_GENAI_API_KEY") or os.getenv("VERTEX_AI_API_KEY")
    return bool((project or api_key) and (project or api_key).strip())


def _vertex_genai_cache_key() -> Tuple[str, str, str]:
    """(project, location, api_key_or_empty) — if env changes, build a new client."""
    project = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT", DEFAULT_GCP_PROJECT)
    location = os.getenv("GOOGLE_CLOUD_LOCATION") or os.getenv("VERTEX_AI_LOCATION", DEFAULT_VERTEX_LOCATION)
    api_key = (os.getenv("GOOGLE_GENAI_API_KEY") or os.getenv("VERTEX_AI_API_KEY") or "").strip()
    return (project, location, api_key)


def reset_vertex_genai_client_cache() -> None:
    """Clear cached google-genai Client (tests or after env/credential change)."""
    global _CACHED_GENAI
    _CACHED_GENAI = None


def consume_vertex_rate_limit_signal() -> bool:
    """
    Return and clear whether a rate-limit signal occurred in recent generate_vertex call(s).
    Used by upper pipeline to enter rate-limit-safe mode even if the final retry succeeded.
    """
    global _LAST_RATE_LIMIT_SIGNAL
    v = bool(_LAST_RATE_LIMIT_SIGNAL)
    _LAST_RATE_LIMIT_SIGNAL = False
    return v


def _get_genai_client():
    """
    Return a singleton google.genai Client for this process when cache key matches.
    Does not cache failed initializations.
    """
    global _CACHED_GENAI
    from google import genai

    key = _vertex_genai_cache_key()
    if _CACHED_GENAI is not None and _CACHED_GENAI[0] == key:
        return _CACHED_GENAI[1]

    project, location, api_key = key
    if api_key:
        client = genai.Client(vertexai=True, api_key=api_key, project=project, location=location)
    else:
        os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project)
        os.environ.setdefault("GOOGLE_CLOUD_LOCATION", location)
        client = genai.Client(vertexai=True, project=project, location=location)

    _CACHED_GENAI = (key, client)
    return client


def generate_vertex(prompt: str, model: Optional[str] = None, **kwargs) -> str:
    """
    Generate text via Vertex AI (Gemini). Uses google-genai SDK.

    model: override from VERTEX_AI_MODEL env
    kwargs: optional max_output_tokens, etc.
    """
    model = model or os.getenv("VERTEX_AI_MODEL", DEFAULT_VERTEX_MODEL)
    max_tokens = kwargs.get("max_output_tokens", MAX_OUTPUT_TOKENS)

    global _LAST_RATE_LIMIT_SIGNAL
    _LAST_RATE_LIMIT_SIGNAL = False

    try:
        client = _get_genai_client()
    except ImportError as e:
        logger.warning("Vertex AI: google-genai not installed. pip install google-genai")
        raise RuntimeError("Vertex AI requires google-genai. pip install google-genai") from e
    except Exception as e:
        logger.warning("Vertex AI client init failed: %s", e)
        return (
            "ERROR: Vertex AI init failed. "
            "Check ADC (gcloud auth application-default login) or set GOOGLE_GENAI_API_KEY. "
            f"Details: {e}"
        )

    try:
        from google.genai import types
        if kwargs.get("config") is not None:
            config = kwargs["config"]
        else:
            cfg_kw = {"max_output_tokens": max_tokens}
            if kwargs.get("temperature") is not None:
                cfg_kw["temperature"] = float(kwargs["temperature"])
            config = types.GenerateContentConfig(**cfg_kw)
        last_err: Optional[Exception] = None
        for attempt in range(VERTEX_MAX_RETRIES + 1):
            try:
                # google-genai does not reliably expose a per-request timeout across all transports.
                # To prevent rare hangs from stalling evaluation runs, enforce a hard timeout here.
                def _call():
                    return client.models.generate_content(
                        model=model,
                        contents=prompt,
                        config=config,
                    )

                timeout_s = float(kwargs.get("request_timeout_sec", VERTEX_REQUEST_TIMEOUT_SEC))
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                    fut = ex.submit(_call)
                    response = fut.result(timeout=timeout_s)
                # Cost/debug: log token usage when SDK exposes it (google-genai).
                _usage = getattr(response, "usage_metadata", None) or getattr(response, "usage", None)
                if _usage is not None:
                    logger.info("Vertex usage_metadata: %s", _usage)
                if hasattr(response, "text"):
                    return response.text or ""
                if hasattr(response, "candidates") and response.candidates:
                    part = response.candidates[0].content.parts[0]
                    return getattr(part, "text", None) or str(part)
                return ""
            except concurrent.futures.TimeoutError as e:
                last_err = e
                # Timeout is not retryable in the same way as rate limits; bail fast so pipeline can fallback.
                logger.warning("Vertex AI request timed out after %.1fs (attempt %s/%s)", timeout_s, attempt + 1, VERTEX_MAX_RETRIES)
                break
            except Exception as e:
                last_err = e
                msg = str(e)
                is_rate_limited = (
                    "RESOURCE_EXHAUSTED" in msg
                    or "429" in msg
                    or "Too Many Requests" in msg
                    or "rate" in msg.lower()
                    or "quota" in msg.lower()
                )
                if is_rate_limited:
                    _LAST_RATE_LIMIT_SIGNAL = True
                if not is_rate_limited or attempt >= VERTEX_MAX_RETRIES:
                    break
                # Exponential backoff with jitter
                sleep_s = min(VERTEX_RETRY_MAX_SECONDS, VERTEX_RETRY_BASE_SECONDS * (2 ** attempt))
                sleep_s = sleep_s * (0.5 + random.random())  # jitter [0.5x, 1.5x]
                logger.warning(
                    "Vertex rate-limited (attempt %s/%s). Sleeping %.2fs. Error: %s",
                    attempt + 1,
                    VERTEX_MAX_RETRIES,
                    sleep_s,
                    msg[:300],
                )
                time.sleep(sleep_s)

        logger.warning("Vertex AI generate_content failed: %s", last_err)
        return f"ERROR: Vertex AI generation failed: {last_err}"
    except Exception as e:
        logger.warning("Vertex AI generate_content unexpected error: %s", e)
        return f"ERROR: Vertex AI generation failed: {e}"
