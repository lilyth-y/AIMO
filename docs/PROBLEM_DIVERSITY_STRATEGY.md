# 문제 다양성 확보 전략

## 개요

AIMO 프로젝트에서 문제의 유형과 종류의 다양성을 확보하고 유지하는 전략을 설명합니다.

---

## 현재 구현된 시스템

### 1. 문제 다양성 분석 모듈

**파일**: `src/pipeline/problem_diversity.py`

**주요 기능**:
- 도메인 분류 (8개 도메인)
- 난이도 분류 (4단계)
- 형식 분류 (5가지)
- 데이터셋 다양성 분석
- 커버리지 점수 계산
- 다양성 검증

### 2. 확장된 문제 분류 시스템

**파일**: `src/pipeline/stage1_labeling.py`

**개선 사항**:
- 더 많은 도메인 키워드 추가
- Calculus 도메인 추가
- 더 정확한 분류를 위한 키워드 확장

### 3. 다양성 분석 스크립트

**파일**: `scripts/analyze_problem_diversity.py`

**기능**:
- JSONL/JSON 파일에서 문제 로드
- 다양성 분석 실행
- 보고서 생성
- JSON 형식 결과 저장

---

## 다양성 확보 방법

### 1. 데이터셋 구성

#### NuminaMath-1.5 활용

**총 896,215개 문제**를 포함하며 다음 소스로 구성:

- **olympiads** (197,084): 올림피아드 문제
- **olympiads_ref** (3,638): 수동 큐레이션된 올림피아드 문제
- **aops_forum** (67,841): Art of Problem Solving 포럼
- **cn_contest** (29,944): 중국 수학 경시 문제
- **inequalities** (7,314): 부등식 문제
- **number_theory** (4,043): 정수론 문제

**문제 유형 분포**:
- Algebra
- Geometry
- Number Theory
- Combinatorics
- Calculus
- Inequalities
- Logic and Puzzles
- Other

#### AIME Validation Set

**90개 공식 AIME 문제**:
- AIME 2022, 2023, 2024
- 표준화된 벤치마크

### 2. 문제 분류 시스템

#### 다층 분류 시스템

1. **Stage 1 (stage1_labeling.py)**: 기본 도메인 분류
   - Geometry, Number Theory, Algebra, Combinatorics, Calculus, General

2. **Rapid Intuition (feature_extractor.py)**: 빠른 직관적 분류
   - geometry, number_theory, algebra, calculus, puzzle, arithmetic, general, misc

3. **Problem Type (orchestrator_helpers.py)**: 문제 유형 분류
   - computational, geometric, complex

4. **Diversity Analyzer (problem_diversity.py)**: 종합 분석
   - 8개 도메인, 4단계 난이도, 5가지 형식

### 3. 다양성 검증

#### 자동 검증

```bash
# 다양성 분석 실행
python scripts/analyze_problem_diversity.py --input data/eval_data.jsonl

# 결과:
# - 도메인 분포 및 다양성 점수
# - 난이도 분포 및 다양성 점수
# - 형식 분포 및 다양성 점수
# - 전체 커버리지 점수
# - 검증 결과 (통과/실패)
```

#### 프로그래밍 방식 검증

```python
from src.pipeline.problem_diversity import ProblemDiversityAnalyzer

analyzer = ProblemDiversityAnalyzer()
is_valid, issues = analyzer.validate_diversity(
    problems,
    min_domains=5,
    min_difficulties=3,
    min_formats=2
)

if is_valid:
    print("✅ 다양성 검증 통과")
else:
    print("❌ 다양성 검증 실패:")
    for issue in issues:
        print(f"  - {issue}")
```

---

## 다양성 확보 체크리스트

### 데이터셋 구성

- [ ] **도메인 다양성**: 최소 5개 이상의 도메인 포함
  - Geometry, Number Theory, Algebra, Combinatorics, Calculus 등
- [ ] **난이도 다양성**: 최소 3개 이상의 난이도 포함
  - Easy, Medium, Hard, Olympiad
- [ ] **형식 다양성**: 최소 2개 이상의 형식 포함
  - word_problem, proof, optimization 등
- [ ] **소스 다양성**: 최소 5개 이상의 다양한 소스
  - olympiads, aops_forum, cn_contest 등
- [ ] **커버리지 점수**: 0.6 이상 권장

### 테스트 커버리지

- [ ] **도메인별 테스트**: 각 도메인에 대해 3-5개 테스트 케이스
- [ ] **난이도별 테스트**: 각 난이도에 대해 테스트 케이스
- [ ] **형식별 테스트**: 각 형식에 대해 테스트 케이스
- [ ] **복합 문제 테스트**: 여러 도메인이 혼합된 문제

### 시스템 검증

- [ ] **분류 정확도**: 각 도메인별 분류 정확도 검증
- [ ] **전략 라우팅**: 각 도메인에 적절한 전략 선택 확인
- [ ] **처리 성공률**: 각 문제 유형별 처리 성공률 모니터링

---

## 지속적인 다양성 확보

### 1. 정기적인 분석

```bash
# 주기적으로 다양성 분석 실행
python scripts/analyze_problem_diversity.py \
    --input data/eval_data.jsonl \
    --output docs/problem_diversity_report.txt
```

### 2. 갭 분석 및 보완

- 부족한 도메인 식별
- 부족한 난이도 식별
- 부족한 형식 식별
- 새로운 문제 소스 추가

### 3. 데이터셋 확장

- 새로운 소스 추가
- 다양한 난이도 문제 수집
- 다양한 형식 문제 수집
- 균형잡힌 분포 유지

---

## 사용 예시

### 1. 데이터셋 다양성 확인

```python
from src.pipeline.problem_diversity import analyze_problem_diversity
import json

# 문제 로드
with open('data/eval_data.jsonl', 'r', encoding='utf-8') as f:
    problems = [json.loads(line) for line in f if line.strip()]

# 분석
result = analyze_problem_diversity(problems)

# 결과 확인
print(result['report'])
print(f"커버리지 점수: {result['analysis']['coverage_score']:.2f}")
print(f"검증 통과: {result['is_valid']}")
```

### 2. 문제 분류 테스트

```bash
python -m pytest tests/test_problem_classification.py -v
```

### 3. 다양성 분석 테스트

```bash
python -m pytest tests/test_problem_diversity.py -v
```

---

## 개선 권장사항

### 1. 분류 정확도 향상

- **LLM 기반 분류**: 키워드 기반에서 LLM 기반으로 전환
- **학습 기반 분류**: BERT나 다른 분류 모델 사용
- **하이브리드 접근**: 키워드 + LLM 조합

### 2. 데이터셋 확장

- **더 많은 소스**: 다양한 수학 경시 문제 소스 추가
- **난이도 균형**: 각 난이도별 균형잡힌 분포
- **형식 다양화**: 다양한 문제 형식 포함

### 3. 모니터링 및 알림

- **정기적인 분석**: 주기적으로 데이터셋 분석
- **커버리지 추적**: 커버리지 점수 모니터링
- **자동 알림**: 다양성 부족 시 알림

---

## 관련 파일

- `src/pipeline/problem_diversity.py`: 다양성 분석 모듈
- `src/pipeline/stage1_labeling.py`: 문제 분류 모듈
- `scripts/analyze_problem_diversity.py`: 다양성 분석 스크립트
- `tests/test_problem_diversity.py`: 다양성 분석 테스트
- `tests/test_problem_classification.py`: 분류 시스템 테스트
- `docs/PROBLEM_DIVERSITY_GUIDE.md`: 상세 가이드

---

**마지막 업데이트**: 2026-01-26
