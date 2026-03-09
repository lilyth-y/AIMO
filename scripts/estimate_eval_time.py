"""
실제 평가 시간 추정 (업데이트된 설정 기반)
"""

import json
from pathlib import Path

# 실제 설정값
MODEL_LOAD_TIME = 30  # 초 (큰 모델의 경우 더 오래 걸림)
TIME_BUDGET_PER_PROBLEM = 60.0  # quick_eval.py, config.py의 DEFAULT_TIME_BUDGET
AVG_TIME_PER_PROBLEM = 25  # 초 (평균, 성공 시)
SLOW_TIME_PER_PROBLEM = 45  # 초 (어려운 문제)

def estimate_time(num_problems, scenario='average'):
    """
    평가 시간 추정
    
    Args:
        num_problems: 문제 수
        scenario: 'fast', 'average', 'slow', 'worst'
    """
    if scenario == 'fast':
        time_per_problem = 15
    elif scenario == 'average':
        time_per_problem = AVG_TIME_PER_PROBLEM
    elif scenario == 'slow':
        time_per_problem = SLOW_TIME_PER_PROBLEM
    else:  # worst
        time_per_problem = TIME_BUDGET_PER_PROBLEM
    
    total_seconds = MODEL_LOAD_TIME + (num_problems * time_per_problem)
    
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    return {
        'total_seconds': total_seconds,
        'hours': hours,
        'minutes': minutes,
        'seconds': seconds,
        'time_per_problem': time_per_problem
    }

def format_time(seconds):
    """초를 읽기 쉬운 형식으로 변환"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}시간")
    if minutes > 0:
        parts.append(f"{minutes}분")
    if secs > 0 or len(parts) == 0:
        parts.append(f"{secs}초")
    
    return " ".join(parts)

def print_estimate(num_problems):
    """시간 추정 출력"""
    print(f"\n{'='*70}")
    print(f"평가 시간 추정 ({num_problems}개 문제)")
    print(f"{'='*70}")
    print(f"모델 로딩: {format_time(MODEL_LOAD_TIME)}")
    print(f"문제당 시간 예산: {TIME_BUDGET_PER_PROBLEM}초")
    print(f"\n시나리오별 예상 시간:")
    
    scenarios = [
        ('fast', '빠름 (15초/문제)', 15),
        ('average', '평균 (25초/문제)', AVG_TIME_PER_PROBLEM),
        ('slow', '느림 (45초/문제)', SLOW_TIME_PER_PROBLEM),
        ('worst', '최악 (60초/문제)', TIME_BUDGET_PER_PROBLEM)
    ]
    
    for key, label, time_per_prob in scenarios:
        result = estimate_time(num_problems, key)
        print(f"  {label:20s}: {format_time(result['total_seconds'])} "
              f"({result['total_seconds']}초)")
    
    print(f"{'='*70}\n")

if __name__ == "__main__":
    # NuminaMath 평가 세트 크기 확인
    try:
        from src.evaluation.config import find_data_file, NUMINA_EVAL_BALANCED_FILE
        path = find_data_file(NUMINA_EVAL_BALANCED_FILE)
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        numina_count = len(data)
    except:
        numina_count = 662  # 기본값 (이전에 본 크기)
    
    # AIME 평가 세트 크기 확인
    try:
        from src.evaluation.config import find_data_file, AIME_VALIDATION_FILE
        path = find_data_file(AIME_VALIDATION_FILE)
        with open(path, 'r', encoding='utf-8') as f:
            aime_data = json.load(f)
        aime_count = len(aime_data)
    except:
        aime_count = 90  # 기본값
    
    print("\n" + "="*70)
    print("평가 세트 크기")
    print("="*70)
    print(f"NuminaMath 평가 세트: {numina_count}개 문제")
    print(f"AIME 평가 세트: {aime_count}개 문제")
    
    # 다양한 문제 수에 대한 추정
    test_cases = [1, 2, 5, 10, 20, 50, 100, numina_count, aime_count]
    
    for num in test_cases:
        if num <= 100 or num in [numina_count, aime_count]:
            print_estimate(num)
    
    # 권장사항
    print("\n" + "="*70)
    print("권장사항")
    print("="*70)
    print(f"1. 빠른 테스트: 5-10개 문제 ({format_time(estimate_time(10, 'average')['total_seconds'])})")
    print(f"2. 중간 평가: 50개 문제 ({format_time(estimate_time(50, 'average')['total_seconds'])})")
    print(f"3. 전체 NuminaMath: {numina_count}개 문제 ({format_time(estimate_time(numina_count, 'average')['total_seconds'])})")
    print(f"4. 전체 AIME: {aime_count}개 문제 ({format_time(estimate_time(aime_count, 'average')['total_seconds'])})")
    print("="*70)
