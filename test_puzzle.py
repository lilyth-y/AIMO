"""수학 퍼즐 문제 처리 테스트"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from src.pipeline.orchestrator import PipelineOrchestrator
from src.pipeline.feature_extractor import rapid_intuition_phase

# 테스트할 퍼즐 문제들
PUZZLE_PROBLEMS = [
    {
        "name": "간단한 숫자 퍼즐",
        "problem": "Find a number such that when you add 5 to it, multiply by 3, and subtract 10, you get 20. What is the number?",
        "domain": "Puzzle",
        "variables": {"N": 100}
    },
    {
        "name": "제약 조건 퍼즐",
        "problem": "A puzzle: Place numbers 1, 2, 3, 4, 5 in a row such that: the first number is odd, the last number is even, and the sum of all numbers is 15. What is the product of the first and last numbers?",
        "domain": "Puzzle",
        "variables": {"N": 5}
    },
    {
        "name": "논리 퍼즐",
        "problem": "A logic puzzle: Three numbers A, B, C satisfy: A + B = 10, B + C = 15, A + C = 13. What is A * B * C?",
        "domain": "Logic",
        "variables": {"N": 20}
    }
]

def test_puzzle_detection():
    """퍼즐 문제 감지 테스트"""
    print("=" * 60)
    print("퍼즐 문제 감지 테스트")
    print("=" * 60)
    
    for prob in PUZZLE_PROBLEMS:
        problem_type, strategy = rapid_intuition_phase(prob["problem"])
        print(f"\n문제: {prob['name']}")
        print(f"  감지된 타입: {problem_type}")
        print(f"  추천 전략: {strategy}")
        print(f"  문제 텍스트: {prob['problem'][:80]}...")
    
    print("\n" + "=" * 60)

def test_puzzle_solving():
    """퍼즐 문제 해결 테스트"""
    print("\n" + "=" * 60)
    print("퍼즐 문제 해결 테스트")
    print("=" * 60)
    
    try:
        orchestrator = PipelineOrchestrator()
        print("Orchestrator 초기화 완료\n")
    except Exception as e:
        print(f"Orchestrator 초기화 실패: {e}")
        print("Mock 모드로 진행합니다...\n")
        return
    
    # 첫 번째 문제만 테스트 (빠른 테스트)
    test_problem = PUZZLE_PROBLEMS[0]
    
    print(f"테스트 문제: {test_problem['name']}")
    print(f"문제: {test_problem['problem']}")
    print(f"도메인: {test_problem['domain']}")
    print(f"변수: {test_problem['variables']}")
    print("\n해결 시작...\n")
    
    try:
        result = orchestrator.solve_problem(
            domain=test_problem['domain'],
            variables=test_problem['variables'],
            problem_text=test_problem['problem'],
            time_budget=30.0
        )
        
        print("\n" + "=" * 60)
        print("결과:")
        print("=" * 60)
        if isinstance(result, dict):
            print(f"답변: {result.get('answer', 'N/A')}")
            print(f"방법: {result.get('method', 'N/A')}")
            print(f"검증됨: {result.get('verified', 'N/A')}")
        else:
            print(f"결과: {result}")
    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 1. 퍼즐 감지 테스트
    test_puzzle_detection()
    
    # 2. 퍼즐 해결 테스트 (선택적)
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--solve":
        test_puzzle_solving()
    else:
        print("\n전체 해결 테스트를 실행하려면: python test_puzzle.py --solve")
