"""
Bulk Data Generator
- Uses ProblemGenerator to create a large dataset.
- Saves to CSV for training/testing.
"""

import csv
import time
from reverse_engineering import ProblemGenerator

def bulk_generate(count=100, filename="generated_problems.csv"):
    gen = ProblemGenerator()
    problems = []
    
    print(f"Starting generation of {count} problems...")
    start_time = time.time()
    
    while len(problems) < count:
        p = gen.generate()
        if p:
            # Add a unique ID
            p['id'] = f"gen_{len(problems):06d}"
            problems.append(p)
            
            if len(problems) % 10 == 0:
                print(f"Generated {len(problems)}/{count}...", end='\r')
    
    end_time = time.time()
    print(f"\nCompleted in {end_time - start_time:.2f} seconds.")
    
    # Save to CSV
    keys = ['id', 'domain', 'type', 'problem', 'answer']
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(problems)
        
    print(f"Saved to {filename}")

if __name__ == "__main__":
    bulk_generate(50) # Generate 50 for a quick test
