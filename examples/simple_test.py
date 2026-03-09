#!/usr/bin/env python3
"""
가장 간단한 테스트
"""

import sys
import os

# Add project root and src to path
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

# 직접 임포트 테스트
print("=== 직접 임포트 테스트 ===")
try:
    from pipeline.orchestrator import PipelineOrchestrator
    print("[OK] PipelineOrchestrator 직접 임포트 성공")
    
    # 오케스트레이터 생성 테스트
    try:
        orchestrator = PipelineOrchestrator()
        print("[OK] PipelineOrchestrator 인스턴스 생성 성공")
        
        # 간단한 테스트
        simple_problem = "What is 2 + 3?"
        print(f"문제: {simple_problem}")
        
        result = orchestrator.solve_problem(
            domain="arithmetic",
            variables={},
            problem_text=simple_problem,
            time_budget=5.0  # 짧은 시간
        )
        
        print(f"결과: {result}")
        
    except Exception as e:
        print(f"[ERROR] 문제 해결 실패: {e}")
        import traceback
        traceback.print_exc()
        
except Exception as e:
    print(f"[ERROR] 직접 임포트 실패: {e}")
    import traceback
    traceback.print_exc()
