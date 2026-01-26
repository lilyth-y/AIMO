"""
단일 문제 빠른 테스트 (GPU 확인 포함)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# GPU 확인
print("="*70)
print("시스템 정보 확인")
print("="*70)

try:
    import torch
    print(f"PyTorch 버전: {torch.__version__}")
    print(f"CUDA 사용 가능: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA 버전: {torch.version.cuda}")
        print(f"GPU 개수: {torch.cuda.device_count()}")
        print(f"GPU 이름: {torch.cuda.get_device_name(0)}")
        print(f"현재 GPU: cuda:{torch.cuda.current_device()}")
    else:
        print("GPU를 사용할 수 없습니다. CPU 모드로 실행됩니다.")
except ImportError:
    print("PyTorch가 설치되지 않았습니다.")

print("\n" + "="*70)
print("환경 변수 확인")
print("="*70)
print(f"AIMO_MODEL: {os.environ.get('AIMO_MODEL', 'Not set')}")
print(f"AIMO_QUANTIZATION: {os.environ.get('AIMO_QUANTIZATION', 'Not set')}")
print(f"HF_HOME: {os.environ.get('HF_HOME', 'Not set')}")

# 환경 변수 설정 (없으면 기본값)
os.environ.setdefault('AIMO_MODEL', 'Qwen/Qwen2-1.5B-Instruct')
os.environ.setdefault('AIMO_QUANTIZATION', '4bit')
os.environ.setdefault('HF_HOME', 'C:\\hf_cache')
os.environ.setdefault('TRANSFORMERS_CACHE', 'C:\\hf_cache')
os.environ.setdefault('OTEL_EXPORTER_OTLP_ENDPOINT', '')
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')

print("\n" + "="*70)
print("단일 문제 테스트 시작")
print("="*70)

# 간단한 테스트 문제
TEST_PROBLEM = {
    "problem": "Find three positive integers a, b, c such that a + b + c = 12, a * b * c is maximum, and a < b < c. What is the product a * b * c?",
    "answer": "40"
}

print(f"\n문제: {TEST_PROBLEM['problem']}")
print(f"정답: {TEST_PROBLEM['answer']}")

try:
    from src.pipeline.orchestrator import PipelineOrchestrator
    from evaluation.evaluation_utils import check_answer_correctness
    
    print("\n[INFO] Orchestrator 초기화 중...")
    import time
    init_start = time.time()
    
    orchestrator = PipelineOrchestrator()
    
    init_time = time.time() - init_start
    print(f"[SUCCESS] 초기화 완료! (소요 시간: {init_time:.2f}초)")
    
    print("\n[INFO] 문제 해결 시작...")
    solve_start = time.time()
    
    result = orchestrator.solve_problem(
        domain="general_math",
        variables={},
        problem_text=TEST_PROBLEM['problem'],
        time_budget=30.0  # 빠른 테스트
    )
    
    solve_time = time.time() - solve_start
    
    predicted = result.get('answer', 'N/A')
    method = result.get('method', 'unknown')
    
    print(f"\n결과:")
    print(f"  예측 답: {predicted}")
    print(f"  방법: {method}")
    print(f"  소요 시간: {solve_time:.2f}초")
    print(f"  총 시간 (초기화 포함): {init_time + solve_time:.2f}초")
    
    is_correct = check_answer_correctness(TEST_PROBLEM['answer'], predicted)
    
    if is_correct:
        print(f"  상태: [OK] 정답!")
    else:
        print(f"  상태: [X] 오답 (예상: {TEST_PROBLEM['answer']}, 예측: {predicted})")
    
    print("\n" + "="*70)
    print("테스트 완료!")
    print("="*70)
    
except Exception as e:
    print(f"\n[ERROR] 오류 발생: {e}")
    import traceback
    traceback.print_exc()
    print("\n모델 로딩에 실패했습니다. 환경 변수를 확인하세요.")
