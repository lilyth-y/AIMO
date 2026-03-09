#!/usr/bin/env python3
"""
간단한 Mock 모델 테스트
"""

import sys
import os

# Add project root and src to path
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

def test_basic_functionality():
    """파이프라인 기본 기능 테스트"""
    print("=== 파이프라인 기본 기능 테스트 ===")
    
    try:
        from pipeline.orchestrator import PipelineOrchestrator
        print("[OK] PipelineOrchestrator 임포트 성공")
        
        # Mock 모델로 오케스트레이터 생성
        orchestrator = PipelineOrchestrator()
        
        # 간단한 덧셈 테스트
        test_problems = [
            "What is 2 + 3?",
            "What is 5 * 4?",
            "What is 10 - 3?"
        ]
        
        expected_answers = ["5", "20", "7"]
        
        print(f"총 {len(test_problems)}개 문제 테스트")
        
        passed = 0
        failed = 0
        
        for i, (problem, expected) in enumerate(zip(test_problems, expected_answers)):
            print(f"\n--- 테스트 {i+1}/{len(test_problems)} ---")
            print(f"문제: {problem}")
            print(f"예상 답: {expected}")
            
            try:
                result = orchestrator.solve_problem(
                    domain="arithmetic",
                    variables={},
                    problem_text=problem,
                    time_budget=3.0
                )
                
                predicted = result.get('answer', 'NO_ANSWER')
                print(f"예측 답: {predicted}")
                
                if predicted == expected:
                    print("✅ 통과")
                    passed += 1
                else:
                    print("❌ 실패")
                    failed += 1
                    
            except Exception as e:
                print(f"❌ 오류 발생: {e}")
                failed += 1
        
        print(f"\n=== 테스트 결과 ===")
        print(f"통과: {passed}/{len(test_problems)}")
        print(f"실패: {failed}/{len(test_problems)}")
        print(f"성공률: {passed/len(test_problems)*100:.1f}%")
        
        return {
            "total_tests": len(test_problems),
            "passed": passed,
            "failed": failed,
            "success_rate": passed/len(test_problems)*100
        }

if __name__ == "__main__":
    test_basic_functionality()
