"""평가 시간 추정"""
import sys

# 설정
MODEL_LOAD_TIME = 2  # 초
TIME_BUDGET_PER_PROBLEM = 30  # 초 (run_simple_eval.py)
AVG_TIME_PER_PROBLEM = 15  # 초 (평균, 성공 시 빠름)

def estimate(num_problems):
    total = MODEL_LOAD_TIME + (num_problems * AVG_TIME_PER_PROBLEM)
    max_time = MODEL_LOAD_TIME + (num_problems * TIME_BUDGET_PER_PROBLEM)
    
    print(f"\n{'='*70}")
    print(f"평가 시간 추정 ({num_problems}개 문제)")
    print(f"{'='*70}")
    print(f"모델 로딩: {MODEL_LOAD_TIME}초")
    print(f"문제당 평균: {AVG_TIME_PER_PROBLEM}초")
    print(f"문제당 최대: {TIME_BUDGET_PER_PROBLEM}초")
    print(f"\n예상 시간:")
    print(f"  최적: {total//60}분 {total%60}초 ({total}초)")
    print(f"  최악: {max_time//60}분 {max_time%60}초 ({max_time}초)")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    estimate(1)
    estimate(2)
    estimate(5)
    estimate(10)
    estimate(60)
