"""
현실적인 평가 시간 추정
실제 파이프라인 동작을 고려한 시간 계산
"""

def realistic_estimate(num_problems):
    """
    실제 파이프라인 동작을 고려한 시간 추정
    
    각 문제당:
    - 모델 로딩 (최초 1회): 30초
    - 전략 선택: 1초
    - 코드 생성 (LLM 추론): 15-45초 (문제 난이도에 따라)
    - 코드 실행: 1-5초
    - 검증: 1-2초
    - 실패 시 재시도: 최대 3번 시도
    - IMO 급 문제는 더 오래 걸림
    """
    
    MODEL_LOAD = 30  # 초
    
    # 문제별 시간 (실제 경험치)
    EASY_PROBLEM = 20   # 초 (간단한 문제, 1번 시도로 성공)
    MEDIUM_PROBLEM = 60  # 초 (중간 난이도, 1-2번 시도)
    HARD_PROBLEM = 120  # 초 (어려운 문제, 2-3번 시도)
    IMO_PROBLEM = 300   # 초 (IMO 급, 여러 전략 시도, 재시도)
    
    print("\n" + "="*70)
    print("현실적인 평가 시간 추정")
    print("="*70)
    print("\n[참고] README_AIMO_EVAL.md 기준:")
    print("  - CPU 모드 (0.5B): ~5-10분/문제 (총 25-50분)")
    print("  - GPU 모드 (0.5B): ~1-2분/문제 (총 5-10분)")
    print("\n[참고] time_budget=60초는 '최대 예산'이지 실제 시간이 아닙니다.")
    print("  실제로는 여러 전략 시도, 재시도, 모델 추론 시간이 더해집니다.")
    
    print("\n" + "-"*70)
    print("문제당 실제 소요 시간 (경험치)")
    print("-"*70)
    print(f"  쉬운 문제: {EASY_PROBLEM}초 (1번 시도로 성공)")
    print(f"  중간 문제: {MEDIUM_PROBLEM}초 (1-2번 시도)")
    print(f"  어려운 문제: {HARD_PROBLEM}초 (2-3번 시도)")
    print(f"  IMO 급 문제: {IMO_PROBLEM}초 (5분, 여러 전략 시도)")
    
    print("\n" + "-"*70)
    print("평가 세트별 추정")
    print("-"*70)
    
    # NuminaMath 평가 세트 (60개)
    # 가정: 20% 쉬움, 50% 중간, 25% 어려움, 5% IMO
    numina_easy = int(60 * 0.20)
    numina_medium = int(60 * 0.50)
    numina_hard = int(60 * 0.25)
    numina_imo = 60 - numina_easy - numina_medium - numina_hard
    
    numina_total = (
        MODEL_LOAD +
        numina_easy * EASY_PROBLEM +
        numina_medium * MEDIUM_PROBLEM +
        numina_hard * HARD_PROBLEM +
        numina_imo * IMO_PROBLEM
    )
    
    print(f"\nNuminaMath 평가 세트 (60개):")
    print(f"  쉬움: {numina_easy}개 × {EASY_PROBLEM}초 = {numina_easy * EASY_PROBLEM}초")
    print(f"  중간: {numina_medium}개 × {MEDIUM_PROBLEM}초 = {numina_medium * MEDIUM_PROBLEM}초")
    print(f"  어려움: {numina_hard}개 × {HARD_PROBLEM}초 = {numina_hard * HARD_PROBLEM}초")
    print(f"  IMO: {numina_imo}개 × {IMO_PROBLEM}초 = {numina_imo * IMO_PROBLEM}초")
    print(f"  모델 로딩: {MODEL_LOAD}초")
    print(f"  총 예상 시간: {numina_total//60}분 {numina_total%60}초 ({numina_total}초)")
    print(f"  = 약 {numina_total/60:.1f}분 = 약 {numina_total/3600:.2f}시간")
    
    # AIME 평가 세트 (90개)
    # 가정: 10% 쉬움, 30% 중간, 40% 어려움, 20% IMO
    aime_easy = int(90 * 0.10)
    aime_medium = int(90 * 0.30)
    aime_hard = int(90 * 0.40)
    aime_imo = 90 - aime_easy - aime_medium - aime_hard
    
    aime_total = (
        MODEL_LOAD +
        aime_easy * EASY_PROBLEM +
        aime_medium * MEDIUM_PROBLEM +
        aime_hard * HARD_PROBLEM +
        aime_imo * IMO_PROBLEM
    )
    
    print(f"\nAIME 평가 세트 (90개):")
    print(f"  쉬움: {aime_easy}개 × {EASY_PROBLEM}초 = {aime_easy * EASY_PROBLEM}초")
    print(f"  중간: {aime_medium}개 × {MEDIUM_PROBLEM}초 = {aime_medium * MEDIUM_PROBLEM}초")
    print(f"  어려움: {aime_hard}개 × {HARD_PROBLEM}초 = {aime_hard * HARD_PROBLEM}초")
    print(f"  IMO: {aime_imo}개 × {IMO_PROBLEM}초 = {aime_imo * IMO_PROBLEM}초")
    print(f"  모델 로딩: {MODEL_LOAD}초")
    print(f"  총 예상 시간: {aime_total//60}분 {aime_total%60}초 ({aime_total}초)")
    print(f"  = 약 {aime_total/60:.1f}분 = 약 {aime_total/3600:.2f}시간")
    
    print("\n" + "="*70)
    print("요약")
    print("="*70)
    print(f"NuminaMath (60개): 약 {numina_total/60:.1f}분 ({numina_total/3600:.2f}시간)")
    print(f"AIME (90개): 약 {aime_total/60:.1f}분 ({aime_total/3600:.2f}시간)")
    print("\n[참고]")
    print("  - time_budget=60초는 '최대 예산'이지 실제 시간이 아닙니다")
    print("  - 실제로는 여러 전략 시도, 재시도, 모델 추론 시간이 더해집니다")
    print("  - IMO 급 문제는 5-10분이 걸릴 수 있습니다")
    print("  - GPU 사용 시 2-3배 빠를 수 있습니다")
    print("="*70)

if __name__ == "__main__":
    realistic_estimate(60)
