"""
빠른 검증 스크립트
실제 데이터로 파이프라인을 검증합니다.
"""

import sys
import json
from pathlib import Path

# 프로젝트 루트를 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline.interface import AIMOInterface
import polars as pl


def validate_with_sample_data():
    """샘플 데이터로 검증"""
    interface = AIMOInterface()
    
    # 간단한 테스트 문제들
    test_problems = [
        ("test_1", "What is 15 + 27?"),
        ("test_2", "Find the number of integers N such that 1 <= N <= 100 and N is divisible by 3"),
        ("test_3", "Compute 2^10"),
    ]
    
    results = []
    
    for problem_id, problem_text in test_problems:
        print(f"\n{'='*50}")
        print(f"Testing Problem: {problem_id}")
        print(f"Problem: {problem_text}")
        print(f"{'='*50}")
        
        try:
            id_series = pl.Series([problem_id])
            problem_series = pl.Series([problem_text])
            
            result_df = interface.predict(id_series, problem_series)
            answer = result_df['answer'].item(0)
            
            results.append({
                'id': problem_id,
                'problem': problem_text,
                'answer': answer,
                'status': 'success'
            })
            
            print(f"✅ Answer: {answer}")
            
        except Exception as e:
            results.append({
                'id': problem_id,
                'problem': problem_text,
                'error': str(e),
                'status': 'error'
            })
            print(f"❌ Error: {e}")
    
    # 결과 요약
    print(f"\n{'='*50}")
    print("Validation Summary")
    print(f"{'='*50}")
    success_count = sum(1 for r in results if r['status'] == 'success')
    print(f"Success: {success_count}/{len(results)}")
    print(f"Failed: {len(results) - success_count}/{len(results)}")
    
    return results


if __name__ == "__main__":
    results = validate_with_sample_data()
    
    # 결과를 JSON 파일로 저장
    output_file = Path(__file__).parent.parent / "validation_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to: {output_file}")
