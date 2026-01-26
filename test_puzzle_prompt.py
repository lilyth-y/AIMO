"""퍼즐 프롬프트 생성 테스트"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from src.pipeline.solver import Solver
from src.pipeline.feature_extractor import rapid_intuition_phase

# 퍼즐 문제 예시
PUZZLE_PROBLEM = "A puzzle: Place numbers 1, 2, 3, 4, 5 in a row such that: the first number is odd, the last number is even, and the sum of all numbers is 15. What is the product of the first and last numbers?"

# 일반 문제 (퍼즐 아님)
NORMAL_PROBLEM = "Find the sum of all integers from 1 to 100."

def test_puzzle_prompt():
    """퍼즐 프롬프트가 제대로 생성되는지 테스트"""
    print("=" * 70)
    print("퍼즐 프롬프트 생성 테스트")
    print("=" * 70)
    
    # 1. 문제 분류 확인
    print("\n1. 문제 분류 확인:")
    print("-" * 70)
    
    puzzle_type, puzzle_strategy = rapid_intuition_phase(PUZZLE_PROBLEM)
    normal_type, normal_strategy = rapid_intuition_phase(NORMAL_PROBLEM)
    
    print(f"퍼즐 문제:")
    print(f"  타입: {puzzle_type}")
    print(f"  전략: {puzzle_strategy}")
    print(f"  문제: {PUZZLE_PROBLEM[:60]}...")
    
    print(f"\n일반 문제:")
    print(f"  타입: {normal_type}")
    print(f"  전략: {normal_strategy}")
    print(f"  문제: {NORMAL_PROBLEM}")
    
    # 2. 프롬프트 생성 확인 (Solver의 _construct_prompt 메서드 직접 테스트)
    print("\n2. 프롬프트 생성 확인:")
    print("-" * 70)
    
    try:
        solver = Solver()
        
        # 퍼즐 문제 프롬프트
        puzzle_prompt = solver._construct_prompt(
            problem_text=PUZZLE_PROBLEM,
            strategy="Path A: The Simulator",
            reasoning_text=None,
            lemma_snippets=None
        )
        
        print("\n퍼즐 문제 프롬프트:")
        print("-" * 70)
        print(puzzle_prompt)
        print("-" * 70)
        
        # 퍼즐 키워드가 프롬프트에 포함되어 있는지 확인
        puzzle_keywords = ['constraint', 'satisfaction', 'backtracking', 'systematic search', 'logical deduction']
        found_keywords = [kw for kw in puzzle_keywords if kw in puzzle_prompt.lower()]
        
        print(f"\n퍼즐 관련 키워드 발견: {found_keywords if found_keywords else '없음'}")
        
        if found_keywords:
            print("✓ 퍼즐 전용 프롬프트가 제대로 생성되었습니다!")
        else:
            print("⚠ 퍼즐 키워드가 프롬프트에 없습니다. 확인이 필요합니다.")
        
        # 일반 문제 프롬프트
        normal_prompt = solver._construct_prompt(
            problem_text=NORMAL_PROBLEM,
            strategy="Path A: The Simulator",
            reasoning_text=None,
            lemma_snippets=None
        )
        
        print("\n일반 문제 프롬프트:")
        print("-" * 70)
        print(normal_prompt)
        print("-" * 70)
        
        # 차이점 확인
        if 'constraint' in puzzle_prompt.lower() and 'constraint' not in normal_prompt.lower():
            print("\n✓ 퍼즐 문제와 일반 문제의 프롬프트가 다르게 생성됩니다!")
        else:
            print("\n⚠ 프롬프트 차이가 명확하지 않습니다.")
            
    except Exception as e:
        print(f"\n오류 발생: {e}")
        print("(모델 로딩이 필요할 수 있습니다)")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_puzzle_prompt()
