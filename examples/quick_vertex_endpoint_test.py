"""
Vertex Endpoint 연동 빠른 테스트.

사전:
  - python -m pip install -r requirements-vertex-sdk.txt
  - gcloud auth application-default login
  - 환경 변수 설정:
      $env:AIMO_VERTEX_ENDPOINT="projects/.../locations/.../endpoints/123"
    또는
      $env:AIMO_VERTEX_ENDPOINT_ID="123"
      $env:GOOGLE_CLOUD_PROJECT="gen-lang-client-0300734101"
      $env:GOOGLE_CLOUD_LOCATION="asia-northeast3"  # 엔드포인트 리전과 일치 (고정값: docs/vertex/AIMO_GCP_PROFILE.md)
"""

import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "src"))


def _looks_like_execution_error(text: str) -> bool:
    """Sandbox/executor failure line (kept local so this example runs without newer orchestrator_helpers)."""
    if not isinstance(text, str) or not text.strip():
        return False
    return text.strip().lower().startswith("error:")


def main() -> int:
    from pipeline.vertex_endpoint_inference import is_vertex_endpoint_configured, predict_vertex_endpoint

    if not is_vertex_endpoint_configured():
        print("Vertex Endpoint가 설정되지 않았습니다.")
        print("  set AIMO_VERTEX_ENDPOINT=projects/.../locations/.../endpoints/123")
        print("  또는 AIMO_VERTEX_ENDPOINT_ID + GOOGLE_CLOUD_PROJECT + GOOGLE_CLOUD_LOCATION")
        return 1

    prompt = "What is 2+2? Reply with one number only."
    out = predict_vertex_endpoint(prompt, max_new_tokens=32, temperature=0.0)
    print("Prompt:", prompt)
    print("Response:", (out[:200] if out else "(empty)"))
    if out and not _looks_like_execution_error(out):
        print("OK - Vertex Endpoint 연동 정상 동작")
        return 0
    print("실패 - 응답 확인")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

