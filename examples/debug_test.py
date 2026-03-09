#!/usr/bin/env python3
"""
간단한 디버깅 테스트 스크립트
"""

import sys
import os
import json

# Add project root and src to path
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

def test_imports():
    """기본 모듈 임포트 테스트"""
    print("=== 임포트 테스트 ===")
    try:
        from pipeline.orchestrator import PipelineOrchestrator
        print("[OK] PipelineOrchestrator 임포트 성공")
    except Exception as e:
        print(f"[ERROR] PipelineOrchestrator 임포트 실패: {e}")
        return False
    
    try:
        import sympy
        print("[OK] sympy 임포트 성공")
    except Exception as e:
        print(f"[ERROR] sympy 임포트 실패: {e}")
        return False
    
    return True

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

def test_simple_problem():
    """간단한 문제 해결 테스트"""
    print("\n=== 간단한 문제 해결 테스트 ===")
    
    if not test_imports():
        return
    
    try:
        orchestrator = PipelineOrchestrator()
        print("[OK] 오케스트레이터 초기화 성공")
        
        # 간단한 산술 문제
        simple_problem = "What is 2 + 3?"
        print(f"문제: {simple_problem}")
        
        result = orchestrator.solve_problem(
            domain="arithmetic",
            variables={},
            problem_text=simple_problem,
            time_budget=10.0
        )
        
        print(f"결과: {result}")
        
    except Exception as e:
        print(f"[ERROR] 문제 해결 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_data_loading()
    test_simple_problem()
