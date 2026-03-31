# 문제 다양성 확보 요약

## 완료된 작업

### 1. 문제 다양성 분석 시스템 구축 ✅

**생성된 파일**:
- `src/pipeline/problem_diversity.py`: 문제 다양성 분석 모듈
- `scripts/analyze_problem_diversity.py`: 다양성 분석 스크립트
- `tests/test_problem_diversity.py`: 다양성 분석 테스트
- `tests/test_problem_classification.py`: 분류 시스템 테스트
- `docs/PROBLEM_DIVERSITY_GUIDE.md`: 상세 가이드
- `docs/PROBLEM_DIVERSITY_STRATEGY.md`: 전략 문서

**주요 기능**:
- 8개 도메인 분류 (Geometry, Number Theory, Algebra, Combinatorics, Calculus, Inequalities, Logic, Probability)
- 4단계 난이도 분류 (Easy, Medium, Hard, Olympiad)
- 5가지 형식 분류 (word_problem, proof, multiple_choice, construction, optimization)
- 데이터셋 다양성 분석
- 커버리지 점수 계산
- 다양성 검증

### 2. 문제 분류 시스템 확장 ✅

**개선된 파일**:
- `src/pipeline/stage1_labeling.py`: 문제 분류 시스템 확장
  - 더 많은 도메인 키워드 추가
  - Calculus 도메인 추가
  - 더 정확한 분류를 위한 키워드 확장

---

## 문제 다양성 확보 방법

### 1. 데이터셋 활용

#### NuminaMath-1.5 (896k 문제)
- **다양한 소스**: olympiads, aops_forum, cn_contest, inequalities, number_theory 등
- **8개 도메인**: Algebra, Geometry, Number Theory, Combinatorics, Calculus, Inequalities, Logic, Other
- **다양한 난이도**: Easy, Medium, Hard, Olympiad

#### AIME Validation Set (90 문제)
- AIME 2022, 2023, 2024 공식 문제
- 표준화된 벤치마크

### 2. 다양성 분석

```bash
# 다양성 분석 실행
python scripts/analyze_problem_diversity.py --input data/eval_data.jsonl
```

**분석 항목**:
- 도메인 분포
- 난이도 분포
- 형식 분포
- 소스 분포
- 커버리지 점수
- 검증 결과

### 3. 다양성 검증

**최소 요구사항**:
- 도메인: 최소 5개 이상
- 난이도: 최소 3개 이상
- 형식: 최소 2개 이상
- 커버리지 점수: 0.6 이상 권장

---

## 사용 예시

### 다양성 분석

```python
from src.pipeline.problem_diversity import analyze_problem_diversity

problems = [
    {'problem': 'Geometry problem', 'source': 'geo'},
    {'problem': 'Number theory problem', 'source': 'nt'},
    # ...
]

result = analyze_problem_diversity(problems)
print(result['report'])
print(f"Valid: {result['is_valid']}")
```

### 테스트 실행

```bash
# 문제 분류 테스트
python -m pytest tests/test_problem_classification.py -v

# 다양성 분석 테스트
python -m pytest tests/test_problem_diversity.py -v
```

---

## 관련 문서

- `docs/PROBLEM_DIVERSITY_GUIDE.md`: 상세 가이드
- `docs/PROBLEM_DIVERSITY_STRATEGY.md`: 전략 문서
- `docs/NUMINA_15_UPGRADE.md`: NuminaMath-1.5 업그레이드 정보

---

**마지막 업데이트**: 2026-01-26
