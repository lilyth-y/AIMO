"""
Simple runner to collect responses from the agent for evaluation.
"""
import json
from src.pipeline.interface import AIMOInterface
import polars as pl

def run_agent_on_queries(input_file: str, output_file: str):
    """
    Run the agent on queries and collect responses.
    """
    print(f"Loading queries from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        queries = json.load(f)
    
    interface = AIMOInterface()
    responses = []
    
    print(f"Running agent on {len(queries)} queries...")
    for i, query_obj in enumerate(queries):
        query = query_obj['query']
        print(f"\n[{i+1}/{len(queries)}] Processing: {query[:50]}...")
        
        # Create Polars Series as the interface expects
        id_series = pl.Series([f"eval_{i}"])
        problem_series = pl.Series([query])
        
        # Get prediction
        result = interface.predict(id_series, problem_series)
        answer = result['answer'][0]
        
        responses.append({
            'query': query,
            'response': str(answer)
        })
        
        print(f"   → Response: {answer}")
    
    print(f"\nSaving responses to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(responses, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Successfully collected {len(responses)} responses!")

if __name__ == "__main__":
    run_agent_on_queries(
        "generated_queries.json",
        "generated_responses.json"
    )
