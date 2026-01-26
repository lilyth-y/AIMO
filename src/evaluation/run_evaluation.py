"""
Evaluation Runner
- Runs the AIMO Agent against the generated test dataset.
- Calculates Accuracy and Difficulty-Weighted Metrics.
"""

import sys
import os
import pandas as pd
import polars as pl
import time

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.pipeline.interface import interface

def run_evaluation(input_file="generated_problems.csv", output_file="evaluation_results.csv"):
    print(f"Loading test data from {input_file}...")
    df = pd.read_csv(input_file)
    
    results = []
    correct_count = 0
    
    print(f"Starting evaluation of {len(df)} problems...")
    
    start_time = time.time()
    
    for idx, row in df.iterrows():
        if idx % 10 == 0:
            print(f"Processing {idx}/{len(df)}...", end='\r')
            
        problem_id = row['id']
        problem_text = row['problem']
        ground_truth = int(row['answer'])
        p_type = row['type']
        
        # Prepare Polars inputs for Interface
        id_series = pl.Series([problem_id])
        problem_series = pl.Series([problem_text])
        
        # Run Agent
        try:
            # Redirect stdout to suppress logs during batch run
            # sys.stdout = open(os.devnull, 'w') 
            response_df = interface.predict(id_series, problem_series)
            # sys.stdout = sys.__stdout__
            
            predicted_answer = response_df['answer'][0]
        except Exception as e:
            print(f"Error on {problem_id}: {e}")
            predicted_answer = -1
            
        # Check Correctness
        is_correct = (predicted_answer == ground_truth)
        if is_correct:
            correct_count += 1
            
        results.append({
            'id': problem_id,
            'type': p_type,
            'problem': problem_text,
            'ground_truth': ground_truth,
            'predicted': predicted_answer,
            'is_correct': is_correct
        })
        
    end_time = time.time()
    duration = end_time - start_time
    
    # Save Results
    results_df = pd.DataFrame(results)
    results_df.to_csv(output_file, index=False)
    
    # Calculate Metrics
    accuracy = correct_count / len(df)
    
    # Difficulty Mapping (Heuristic)
    difficulty_map = {
        'Linear Equation': 'Level 1',
        'Modular Arithmetic': 'Level 2',
        'Linear Recurrence': 'Level 3',
        'Polynomial Vieta': 'Level 3',
        'CRT': 'Level 4'
    }
    
    results_df['difficulty'] = results_df['type'].map(difficulty_map)
    
    print("\n" + "="*40)
    print(f"Evaluation Complete in {duration:.2f}s")
    print(f"Overall Accuracy: {accuracy:.2%} ({correct_count}/{len(df)})")
    print("="*40)
    
    # Breakdown by Difficulty
    print("\n[Accuracy by Difficulty]")
    summary = results_df.groupby('difficulty')['is_correct'].mean()
    print(summary)
    
    # Breakdown by Type
    print("\n[Accuracy by Type]")
    type_summary = results_df.groupby('type')['is_correct'].mean()
    print(type_summary)
    
    # Save Summary
    with open("evaluation_summary.md", "w") as f:
        f.write(f"# Evaluation Report\n")
        f.write(f"- **Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"- **Dataset**: {input_file}\n")
        f.write(f"- **Total Problems**: {len(df)}\n")
        f.write(f"- **Overall Accuracy**: {accuracy:.2%}\n\n")
        f.write("## Accuracy by Difficulty\n")
        f.write(summary.to_markdown())
        f.write("\n\n## Accuracy by Type\n")
        f.write(type_summary.to_markdown())

if __name__ == "__main__":
    run_evaluation()
