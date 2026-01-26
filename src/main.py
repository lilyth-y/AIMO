"""
Main Entry Point for AIMO 3 Submission
- Initializes the Inference Server
- Connects the Interface to the Gateway
"""

import sys
import os

# Add the src directory to sys.path to ensure modules can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Add the project root to sys.path to import kaggle_evaluation
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    import kaggle_evaluation.aimo_3_inference_server as inference_server
except ImportError as e:
    print(f"❌ Critical Error: 'kaggle_evaluation' module not found. {e}")
    sys.exit(1)

from pipeline.interface import predict

def main():
    print("🚀 Starting AIMO 3 Inference System...")
    
    # Initialize the Inference Server with our predict callback
    server = inference_server.AIMO3InferenceServer(predict)
    
    if os.getenv('KAGGLE_IS_COMPETITION_RERUN'):
        print("☁️ Running in Kaggle Competition Mode")
        server.serve()
    else:
        print("💻 Running in Local Gateway Mode")
        # For local testing, we point to the test.csv file
        # The Gateway expects a tuple of paths
        server.run_local_gateway(
            data_paths=('test.csv', )
        )

if __name__ == "__main__":
    main()
