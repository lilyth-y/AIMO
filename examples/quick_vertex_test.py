"""
Vertex AI 연동 빠른 테스트.
비용 최소화: 짧은 프롬프트 + 출력 50토큰 제한.

실행 전:
  1. pip install -r requirements-vertex.txt (또는 Cloud Shell: requirements-cloudshell-smoke.txt + --target /tmp, CLOUD_NUMINA_RUN.md 참고)
  2. 인증 중 하나:
     - gcloud auth application-default login
     - 또는 GOOGLE_GENAI_API_KEY / VERTEX_AI_API_KEY 설정
  3. (선택) GOOGLE_CLOUD_PROJECT=gen-lang-client-0300734101
"""

import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "src"))

def main():
    from pipeline.orchestrator_helpers import is_execution_error_output
    from pipeline.vertex_inference import is_vertex_configured, generate_vertex

    if not is_vertex_configured():
        print("Vertex가 설정되지 않았습니다.")
        print("  set GOOGLE_CLOUD_PROJECT=gen-lang-client-0300734101")
        print("  또는 set GCP_PROJECT=gen-lang-client-0300734101")
        print("  그리고 gcloud auth application-default login 또는 API 키 설정")
        return 1

    print("Vertex AI 테스트 (짧은 답변, 비용 최소)...")
    prompt = "What is 2+2? Reply with one number only."
    out = generate_vertex(prompt, max_output_tokens=50)
    print("Prompt:", prompt)
    print("Response:", out[:200] if out else "(empty)")
    if out and not is_execution_error_output(out):
        print("OK - Vertex 연동 정상 동작")
        return 0
    print("실패 - 위 응답 확인")
    return 1

if __name__ == "__main__":
    sys.exit(main())
