"""
Test script for Hybrid Reasoning Engine
Tests the graph-based decomposition system
"""

import os

import pytest

from src.pipeline.orchestrator import PipelineOrchestrator

pytestmark = pytest.mark.slow

def test_complex_problem(monkeypatch):
    """
    Test with a complex multi-step problem
    """
    # Default CI/unit runs: no real HF weights (slow tests still run; mock path only).
    monkeypatch.setenv("AIMO_FAST_TEST", "1")

    print("="*60)
    print("Testing Hybrid Reasoning Engine")
    print("="*60)
    
    # Create orchestrator (includes hybrid engine)
    orch = PipelineOrchestrator()
    
    # Test problem: Multi-step geometry
    problem = """
    삼각형 ABC에서 다음이 주어졌을 때:
    - AB = 5
    - BC = 7
    - CA = 6
    
    다음을 구하시오:
    1. 삼각형의 넓이 (헤론의 공식 사용)
    2. 삼각형의 둘레
    3. 내접원의 반지름
    
    최종 답: 내접원의 반지름을 출력하시오.
    """
    
    print("\n문제:")
    print(problem)
    print("\n" + "="*60)
    
    # Solve using orchestrator (will route to hybrid engine for complex problems)
    result = orch.solve_problem(
        domain="Geometry",
        variables={"sides": [5, 7, 6]},
        problem_text=problem,
        time_budget=120.0  # 2 minutes
    )
    
    print("\n" + "="*60)
    print("최종 결과:")
    print(result)
    print("="*60)

def test_simple_comparison(monkeypatch):
    """
    Compare simple problem handling (should not use hybrid engine)
    """
    monkeypatch.setenv("AIMO_FAST_TEST", "1")

    print("\n\n" + "="*60)
    print("Testing Simple Problem (should use standard flow)")
    print("="*60)
    
    orch = PipelineOrchestrator()
    
    simple_problem = """
    100 이하의 모든 소수의 합을 구하시오.
    """
    
    print("\n문제:")
    print(simple_problem)
    print("\n" + "="*60)
    
    result = orch.solve_problem(
        domain="Number Theory",
        variables={"N": 100},
        problem_text=simple_problem,
        time_budget=30.0
    )
    
    print("\n" + "="*60)
    print("최종 결과:")
    print(result)
    print("="*60)

if __name__ == "__main__":
    os.environ.setdefault("AIMO_FAST_TEST", "1")
    from _pytest.monkeypatch import MonkeyPatch

    mp = MonkeyPatch()
    # Test 1: Complex problem (should use Hybrid Engine)
    test_complex_problem(mp)

    # Test 2: Simple problem (should use standard flow)
    test_simple_comparison(mp)
