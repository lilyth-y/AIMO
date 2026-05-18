import os
import sys

# Add src to sys.path
sys.path.insert(0, os.path.abspath('src'))

from pipeline.vertex_inference import is_vertex_configured, generate_vertex

def main():
    print(f"Vertex configured: {is_vertex_configured()}")
    project = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT")
    api_key = os.getenv("GOOGLE_GENAI_API_KEY") or os.getenv("VERTEX_AI_API_KEY")
    print(f"Project: {project}")
    print(f"API Key: {'set' if api_key else 'unset'}")
    
    if not is_vertex_configured():
        print("Vertex not configured. Please set GOOGLE_CLOUD_PROJECT or GOOGLE_GENAI_API_KEY.")
        return

    print("Attempting a simple Vertex AI call...")
    try:
        result = generate_vertex("Say hello")
        print(f"Result: {result}")
    except Exception as e:
        print(f"Caught Exception: {e}")

if __name__ == "__main__":
    main()
