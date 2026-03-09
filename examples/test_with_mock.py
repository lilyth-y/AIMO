#!/usr/bin/env python3
"""
Mock 모델을 사용한 파이프라인 테스트
"""

import sys
import os
import json

# Add project root and src to path
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

def test_with_mock_model():
    """Mock 모델로 파이프라인 기능 테스트"""
    print("=== Mock 모델 파이프라인 테스트 ===")
    
    try:
        from pipeline.orchestrator import PipelineOrchestrator
        print("[OK] PipelineOrchestrator 임포트 성공")
        
        # Mock 모델로 오케스트레이터 생성
        # Mock 모델은 실제 LLM 없이도 작동하도록 설정
        orchestrator = PipelineOrchestrator()
        
        # 간단한 테스트 케이스들
        test_cases = [
            {
                "problem": "What is 2 + 3?",
                "expected": "5",
                "domain": "arithmetic",
                "description": "기본 덧셈"
            },
            {
                "problem": "What is 10 * 5?",
                "expected": "50", 
                "domain": "arithmetic",
                "description": "기본 곱셈"
            },
            {
                "problem": "Find the remainder when 17 is divided by 5.",
                "expected": "2",
                "domain": "arithmetic", 
                "description": "나머지 계산"
            },
            {
                "problem": "What is the square root of 16?",
                "expected": "4",
                "domain": "arithmetic",
                "description": "제곱근 계산"
            }
        ]
        
        print(f"총 {len(test_cases)}개 테스트 케이스 준비")
        
        # 각 테스트 케이스 실행
        passed = 0
        failed = 0
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n--- 테스트 {i}/{len(test_cases)} ---")
            print(f"문제: {test_case['problem']}")
            print(f"예상 답: {test_case['expected']}")
            print(f"도메인: {test_case['domain']}")
            print(f"설명: {test_case['description']}")
            
            try:
                result = orchestrator.solve_problem(
                    domain=test_case['domain'],
                    variables={},
                    problem_text=test_case['problem'],
                    time_budget=5.0  # 짧은 시간
                )
                
                predicted = result.get('answer', 'NO_ANSWER')
                print(f"예측 답: {predicted}")
                
                # 답안 비교 (단순화된 비교)
                if predicted == test_case['expected']:
                    print("✅ 통과")
                    passed += 1
                else:
                    print("❌ 실패")
                    failed += 1
                    
            except Exception as e:
                print(f"❌ 오류 발생: {e}")
                failed += 1
        
        print(f"\n=== 테스트 결과 ===")
        print(f"통과: {passed}/{len(test_cases)}")
        print(f"실패: {failed}/{len(test_cases)}")
        print(f"성공률: {passed/len(test_cases)*100:.1f}%")
        
        return {
            "total_tests": len(test_cases),
            "passed": passed,
            "failed": failed,
            "success_rate": passed/len(test_cases)*100
        }

def test_data_loading():
    """데이터 로딩 테스트"""
    print("\n=== 데이터 로딩 테스트 ===")
    
    try:
        # 기존 데이터 파일 사용
        data_path = os.path.join(project_root, 'data', 'eval_data.jsonl')
        with open(data_path, 'r', encoding='utf-8') as f:
            data = [json.loads(line) for line in f if line.strip()]
        
        print(f"[OK] 데이터 로딩 성공: {len(data)}개 문제")
        
        # 첫 번째 문제 확인
        if data:
            first_problem = data[0]
            print(f"첫 번째 문제: {first_problem['query'][:100]}...")
            return first_problem
        else:
            print("[ERROR] 데이터가 비어있음")
            return None
            
    except Exception as e:
        print(f"[ERROR] 데이터 로딩 실패: {e}")
        return None
  +++++++ REPLACE

if __name__ == "__main__":
    # 데이터 로딩 테스트
    test_data_loading()
    
    # Mock 모델 파이프라인 테스트
    test_results = test_with_mock_model()
    
    print(f"\n=== 최종 요약 ===")
    print(f"Mock 모델 테스트 성공률: {test_results['success_rate']:.1f}%")
    
    if test_results['success_rate'] >= 75.0:
        print("✅ 파이프라인 기본 기능이 정상 작동합니다.")
    else:
        print("⚠️ 파이프라인 개선이 필요합니다.")
