# 문제 다양성 확보 가이드

## 개요

이 문서는 AIMO 프로젝트에서 문제의 유형과 종류의 다양성을 확보하고 검증하는 방법을 설명합니다.

---

## 현재 문제 분류 시스템

### 1. 도메인 분류

시스템은 다음 도메인을 지원합니다:

- **Geometry (기하학)**: 삼각형, 원, 각도, 좌표 등
- **Number Theory (정수론)**: 소수, 최대공약수, 모듈러 연산 등
- **Algebra (대수학)**: 다항식, 방정식, 인수분해 등
- **Combinatorics (조합론)**: 순열, 조합, 그래프 등
- **Calculus (미적분)**: 미분, 적분, 극한, 급수 등
- **Inequalities (부등식)**: AM-GM, 코시-슈바르츠 등
- **Logic (논리)**: 퍼즐, 제약 조건, 증명 등
- **Probability (확률)**: 확률, 기댓값, 분포 등

### 2. 난이도 분류

- **Easy**: 기본적인 계산 문제
- **Medium**: 표준적인 문제 해결
- **Hard**: 복잡한 추론이 필요한 문제
- **Olympiad**: 올림피아드 수준의 고난도 문제

### 3. 형식 분류

- **word_problem**: 단어 문제 (What is, How many, Find the 등)
- **proof**: 증명 문제 (Prove, Show that 등)
- **multiple_choice**: 객관식 문제
- **construction**: 작도 문제
- **optimization**: 최적화 문제

---

## 다양성 확보 방법

### 1. 데이터셋 다양성 확보

#### NuminaMath-1.5 데이터셋 활용

```python
from src.data.numina_loader import load_numina_dataset

# NuminaMath-1.5 (896k 문제) 로드
problems = load_numina_dataset()

# 다양한 소스 포함:
# - olympiads (197,084): 올림피아드 문제
# - olympiads_ref (3,638): 수동으로 큐레이션된 올림피아드 문제
# - aops_forum (67,841): Art of Problem Solving 포럼
# - cn_contest (29,944): 중국 수학 경시 문제
# - inequalities (7,314): 부등식 문제
# - number_theory (4,043): 정수론 문제
```

#### AIME Validation Set 활용

```python
# AIME 검증 세트 (90 문제)
# - AIME 2022, 2023, 2024 공식 문제
# - 표준화된 벤치마크
```

### 2. 문제 분류 시스템 개선

#### 확장된 키워드 기반 분류

`src/pipeline/stage1_labeling.py`의 `ProblemAnalyzer` 클래스가 확장되었습니다:

- 더 많은 도메인 키워드 추가
- Calculus 도메인 추가
- 더 정확한 분류를 위한 키워드 확장

#### 다양성 분석 도구

`src/pipeline/problem_diversity.py`의 `ProblemDiversityAnalyzer` 클래스:

- 도메인 분포 분석
- 난이도 분포 분석
- 형식 분포 분석
- 커버리지 점수 계산
- 다양성 검증

### 3. 다양성 검증

#### 스크립트 실행

```bash
# 문제 다양성 분석
python scripts/analyze_problem_diversity.py --input data/eval_data.jsonl

# 결과:
# - 도메인 분포
# - 난이도 분포
# - 형식 분포
# - 커버리지 점수
# - 검증 결과
```

#### 프로그래밍 방식

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

---

## 다양성 확보 전략

### 1. 데이터셋 구성

#### 최소 요구사항

- **도메인**: 최소 5개 이상의 도메인 포함
- **난이도**: 최소 3개 이상의 난이도 포함
- **형식**: 최소 2개 이상의 형식 포함
- **커버리지 점수**: 0.6 이상 권장

#### 권장 구성

- **도메인**: 8개 도메인 모두 포함
- **난이도**: 4개 난이도 모두 포함
- **형식**: 5개 형식 모두 포함
- **소스**: 최소 5개 이상의 다양한 소스

### 2. 테스트 케이스 다양성

#### 도메인별 테스트 케이스

각 도메인에 대해 최소 3-5개의 테스트 케이스를 포함:

```python
# tests/test_problem_classification.py
geometry_tests = [
    "Find the area of a triangle",
    "What is the radius of a circle?",
    "Find the distance between two points",
    # ...
]
```

#### 난이도별 테스트 케이스

각 난이도에 대해 테스트 케이스 포함:

- Easy: 기본 계산 문제
- Medium: 표준 문제
- Hard: 복잡한 추론 문제
- Olympiad: 고난도 문제

### 3. 데이터 수집 전략

#### 다양한 소스 활용

1. **공식 경시 문제**
   - IMO, AIME, USAMO 등
   - 공식 웹사이트에서 직접 추출

2. **온라인 커뮤니티**
   - Art of Problem Solving (AoPS)
   - Math Stack Exchange
   - 수학 경시 포럼

3. **학습 데이터셋**
   - NuminaMath-1.5 (896k 문제)
   - 다양한 난이도와 도메인 포함

4. **자체 생성**
   - 역공학 데이터 생성
   - 변형 문제 생성

---

## 다양성 검증 체크리스트

### 데이터셋 검증

- [ ] 최소 5개 도메인 포함
- [ ] 최소 3개 난이도 포함
- [ ] 최소 2개 형식 포함
- [ ] 커버리지 점수 0.6 이상
- [ ] 각 도메인당 최소 10개 문제
- [ ] 각 난이도당 최소 10개 문제

### 테스트 검증

- [ ] 각 도메인별 테스트 케이스 존재
- [ ] 각 난이도별 테스트 케이스 존재
- [ ] 각 형식별 테스트 케이스 존재
- [ ] 테스트 커버리지 70% 이상

### 시스템 검증

- [ ] 문제 분류 시스템이 모든 도메인 인식
- [ ] 각 도메인에 적절한 전략 라우팅
- [ ] 다양한 문제 유형에 대한 처리 전략 존재

---

## 사용 예시

### 1. 데이터셋 다양성 분석

```bash
python scripts/analyze_problem_diversity.py \
    --input data/eval_data.jsonl \
    --output docs/problem_diversity_report.txt \
    --json-output docs/problem_diversity_analysis.json
```

### 2. 프로그래밍 방식 분석

```python
from src.pipeline.problem_diversity import ProblemDiversityAnalyzer
import json

# 문제 로드
with open('data/eval_data.jsonl', 'r', encoding='utf-8') as f:
    problems = [json.loads(line) for line in f if line.strip()]

# 분석
analyzer = ProblemDiversityAnalyzer()
analysis = analyzer.analyze_dataset(problems)

# 검증
is_valid, issues = analyzer.validate_diversity(problems)

if is_valid:
    print("✅ 다양성 검증 통과")
else:
    print("❌ 다양성 검증 실패:")
    for issue in issues:
        print(f"  - {issue}")
```

### 3. 테스트 실행

```bash
# 문제 분류 테스트
python -m pytest tests/test_problem_classification.py -v

# 다양성 분석 테스트
python -m pytest tests/test_problem_diversity.py -v
```

---

## 개선 권장사항

### 1. 분류 정확도 향상

- **LLM 기반 분류**: 키워드 기반에서 LLM 기반으로 전환
- **학습 기반 분류**: BERT나 다른 분류 모델 사용
- **하이브리드 접근**: 키워드 + LLM 조합

### 2. 데이터셋 확장

- **더 많은 소스 추가**: 다양한 수학 경시 문제 소스
- **난이도 균형**: 각 난이도별 균형잡힌 분포
- **형식 다양화**: 다양한 문제 형식 포함

### 3. 지속적인 모니터링

- **정기적인 다양성 분석**: 주기적으로 데이터셋 분석
- **커버리지 추적**: 커버리지 점수 모니터링
- **갭 분석**: 부족한 영역 식별 및 보완

---

## 관련 파일

- `src/pipeline/problem_diversity.py`: 다양성 분석 모듈
- `src/pipeline/stage1_labeling.py`: 문제 분류 모듈
- `scripts/analyze_problem_diversity.py`: 다양성 분석 스크립트
- `tests/test_problem_diversity.py`: 다양성 분석 테스트
- `tests/test_problem_classification.py`: 분류 시스템 테스트

---

**마지막 업데이트**: 2026-01-26
