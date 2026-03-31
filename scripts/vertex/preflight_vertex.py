"""
Vertex preflight checks (no network calls).

Goals:
  - Validate env vars for Vertex Gemini (google-genai) and/or Vertex Endpoint.
  - Validate Python deps are importable.
  - Validate Application Default Credentials (ADC) are discoverable.

This script intentionally does NOT call any Vertex API endpoint.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    detail: str


def _env(key: str) -> str:
    return (os.getenv(key) or "").strip()


def _endpoint_resource_name() -> Optional[str]:
    full = _env("AIMO_VERTEX_ENDPOINT")
    if full:
        return full
    endpoint_id = _env("AIMO_VERTEX_ENDPOINT_ID")
    project = _env("GOOGLE_CLOUD_PROJECT") or _env("GCP_PROJECT")
    location = _env("GOOGLE_CLOUD_LOCATION") or _env("VERTEX_AI_LOCATION")
    if endpoint_id and project and location:
        return f"projects/{project}/locations/{location}/endpoints/{endpoint_id}"
    return None


def _vertex_gemini_config() -> Tuple[Optional[str], Optional[str], Optional[str]]:
    project = _env("GOOGLE_CLOUD_PROJECT") or _env("GCP_PROJECT")
    location = _env("GOOGLE_CLOUD_LOCATION") or _env("VERTEX_AI_LOCATION") or "us-central1"
    api_key = _env("GOOGLE_GENAI_API_KEY") or _env("VERTEX_AI_API_KEY")
    if not project and not api_key:
        return None, None, None
    return project or "(from ADC/project default)", location, api_key or ""


def check_env() -> list[CheckResult]:
    results: list[CheckResult] = []

    endpoint = _endpoint_resource_name()
    results.append(
        CheckResult(
            name="vertex_endpoint_config",
            ok=bool(endpoint),
            detail=endpoint or "Not configured (set AIMO_VERTEX_ENDPOINT or AIMO_VERTEX_ENDPOINT_ID + project/location).",
        )
    )

    project, location, api_key = _vertex_gemini_config()
    results.append(
        CheckResult(
            name="vertex_gemini_env",
            ok=bool(project or api_key),
            detail=(
                f"project={project}, location={location}, api_key={'set' if api_key else 'unset'}"
                if (project or api_key)
                else "Not configured (set GOOGLE_CLOUD_PROJECT or GOOGLE_GENAI_API_KEY)."
            ),
        )
    )

    model = _env("VERTEX_AI_MODEL")
    results.append(
        CheckResult(
            name="vertex_gemini_model",
            ok=bool(model) or True,
            detail=model or "(default used by src/pipeline/vertex_inference.py)",
        )
    )

    remote = _env("OMI_REMOTE_INFERENCE_URL")
    results.append(
        CheckResult(
            name="remote_inference_env",
            ok=bool(remote) or True,
            detail=remote or "(not set)",
        )
    )

    fast_test = _env("AIMO_FAST_TEST")
    results.append(CheckResult(name="aimo_fast_test", ok=True, detail=fast_test or "0"))
    return results


def check_imports() -> list[CheckResult]:
    results: list[CheckResult] = []

    try:
        import google.genai  # noqa: F401

        results.append(CheckResult("import_google_genai", True, "google-genai import OK"))
    except Exception as e:
        results.append(
            CheckResult(
                "import_google_genai",
                False,
                f"Import failed: {e} (install: python -m pip install google-genai)",
            )
        )

    try:
        import google.cloud.aiplatform  # noqa: F401

        results.append(
            CheckResult(
                "import_google_cloud_aiplatform",
                True,
                "google-cloud-aiplatform import OK",
            )
        )
    except Exception as e:
        results.append(
            CheckResult(
                "import_google_cloud_aiplatform",
                False,
                f"Import failed: {e} (install: python -m pip install -r requirements-vertex-sdk.txt)",
            )
        )

    try:
        import google.auth  # noqa: F401

        results.append(CheckResult("import_google_auth", True, "google-auth import OK"))
    except Exception as e:
        results.append(
            CheckResult(
                "import_google_auth",
                False,
                f"Import failed: {e} (install: python -m pip install google-auth)",
            )
        )

    return results


def check_adc() -> list[CheckResult]:
    results: list[CheckResult] = []
    try:
        import google.auth

        creds, project = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        detail = f"ADC found (type={type(creds).__name__}, project={project or '(none)'})"
        results.append(CheckResult("adc_default_credentials", True, detail))
    except Exception as e:
        results.append(
            CheckResult(
                "adc_default_credentials",
                False,
                "ADC not found. Run: gcloud auth application-default login "
                f"(details: {e})",
            )
        )
    return results


def _print_results(title: str, results: list[CheckResult]) -> bool:
    print(f"\n== {title} ==")
    ok_all = True
    for r in results:
        status = "OK " if r.ok else "FAIL"
        print(f"[{status}] {r.name}: {r.detail}")
        ok_all = ok_all and r.ok
    return ok_all


def main() -> int:
    print("Vertex preflight (no network calls)")
    print(f"python: {sys.version.split()[0]}")

    env_results = check_env()
    imp_results = check_imports()
    adc_results = check_adc()

    _print_results("Environment", env_results)
    _print_results("Imports", imp_results)
    _print_results("ADC", adc_results)

    def _ok(name: str, results: list[CheckResult]) -> bool:
        for r in results:
            if r.name == name:
                return bool(r.ok)
        return False

    # "Ready" means at least one Vertex backend is correctly configured:
    #  - Gemini (google-genai) path OR
    #  - Endpoint (aiplatform) path
    ok_adc = _ok("adc_default_credentials", adc_results)
    ok_gemini = _ok("vertex_gemini_env", env_results) and _ok("import_google_genai", imp_results) and ok_adc
    ok_endpoint = _ok("vertex_endpoint_config", env_results) and _ok("import_google_cloud_aiplatform", imp_results) and ok_adc
    ok = ok_gemini or ok_endpoint

    mode = "gemini" if ok_gemini else ("endpoint" if ok_endpoint else "none")
    print("\n== Summary ==")
    print(("READY (" + mode + ")") if ok else "NOT READY")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())

