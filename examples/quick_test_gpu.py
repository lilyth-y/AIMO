"""
GPU 확인 및 빠른 테스트 (5개 문제)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("="*70)
print("GPU 확인")
print("="*70)

try:
    import torch
    has_gpu = torch.cuda.is_available()
    if has_gpu:
        print(f"✓ GPU 사용 가능: {torch.cuda.get_device_name(0)}")
        print(f"  CUDA 버전: {torch.version.cuda}")
    else:
        print("✗ GPU 사용 불가 - CPU 모드로 실행됩니다")
except:
    print("✗ PyTorch를 확인할 수 없습니다")

print("\n" + "="*70)
print("빠른 평가 테스트 (5개 문제)")
print("="*70)

# 환경 변수 설정
os.environ.setdefault('OMI_MODEL', 'Qwen/Qwen2-1.5B-Instruct')
os.environ.setdefault('OMI_QUANTIZATION', '4bit')
os.environ.setdefault('HF_HOME', 'C:\\hf_cache')
os.environ.setdefault('TRANSFORMERS_CACHE', 'C:\\hf_cache')
os.environ.setdefault('OTEL_EXPORTER_OTLP_ENDPOINT', '')
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')

try:
    from quick_eval import load_numina_eval, evaluate_quick
    from src.pipeline.orchestrator import PipelineOrchestrator
    
    print("\n[1/3] 문제 로딩 중...")
    problems = load_numina_eval()
    print(f"    로드된 문제: {len(problems)}개")
    
    print("\n[2/3] Orchestrator 초기화 중...")
    import time
    start_init = time.time()
    orchestrator = PipelineOrchestrator()
    init_time = time.time() - start_init
    print(f"    초기화 완료! ({init_time:.1f}초 소요)")
    
    print("\n[3/3] 평가 실행 중... (5개 문제)")
    print("    (시간이 걸릴 수 있습니다. 기다려주세요...)")
    start_eval = time.time()
    
    accuracy, results = evaluate_quick(orchestrator, problems, max_problems=5)
    
    eval_time = time.time() - start_eval
    total_time = time.time() - start_init
    
    print("\n" + "="*70)
    print("테스트 완료!")
    print("="*70)
    print(f"초기화 시간: {init_time:.1f}초")
    print(f"평가 시간: {eval_time:.1f}초 ({eval_time/60:.1f}분)")
    print(f"총 시간: {total_time:.1f}초 ({total_time/60:.1f}분)")
    print(f"문제당 평균: {eval_time/5:.1f}초")
    print(f"정확도: {accuracy:.1f}%")
    print("="*70)
    
except KeyboardInterrupt:
    print("\n\n[중단됨] 사용자가 테스트를 중단했습니다.")
except Exception as e:
    print(f"\n[오류] {e}")
    import traceback
    traceback.print_exc()
