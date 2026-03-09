import sys
import os
import pandas as pd

# Add current directory to path to find aimo.py and kaggle_math_pipeline.py
sys.path.append(os.path.dirname(__file__))

try:
    import aimo
    print("Successfully imported aimo competition module.")
except ImportError:
    print("Could not import aimo module. Ensure you are in the Kaggle environment or have the mock aimo.py.")
    sys.exit(1)

from kaggle_math_pipeline import PipelineOrchestrator

def main():
    # Initialize environment
    env = aimo.make_env()
    iter_test = env.iter_test()
    
    # Initialize orchestrator
    # Note: In Kaggle, you might need to set MATHCODEORCHESTRATOR_MODEL to a local path of the uploaded dataset
    # e.g. os.environ['MATHCODEORCHESTRATOR_MODEL'] = '/kaggle/input/qwen2-5-math-1-5b-instruct'
    orchestrator = PipelineOrchestrator()
    
    print("Starting submission loop...")
    for test, sample_submission in iter_test:
        # test is a DataFrame with columns ['id', 'problem', ...]
        # sample_submission is a DataFrame with columns ['id', 'answer']
        
        for index, row in test.iterrows():
            problem_text = row['problem']
            print(f"\nProcessing problem: {problem_text[:50]}...")
            
            # Solve
            try:
                # Use a shorter timeout for the competition to ensure we don't time out globally
                result = orchestrator.solve_problem(
                    domain="math_olympiad",
                    variables={},
                    problem_text=problem_text,
                    time_budget=60.0 
                )
                answer = result.get('answer')
                
                # Fallback if None
                if answer is None:
                    answer = 0 
                
                # Ensure answer is an integer (modulo 1000 usually required, check rules)
                # AIMO Progress Prize 2 required integer modulo 1000. 
                # Let's assume we just output the raw answer for now or handle formatting.
                # If the answer is a float/string, try to convert to int.
                try:
                    answer = int(float(str(answer).strip()))
                except:
                    answer = 0 # Fallback
                    
            except Exception as e:
                print(f"Error solving problem: {e}")
                answer = 0
            
            sample_submission.loc[index, 'answer'] = answer
            print(f"Predicted: {answer}")
            
        env.predict(sample_submission)
        
    print("Submission loop completed.")

if __name__ == "__main__":
    main()
