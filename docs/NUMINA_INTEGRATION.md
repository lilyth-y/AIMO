# NuminaMath-CoT Dataset Integration

## 개요

[NuminaMath-CoT](https://huggingface.co/datasets/AI-MO/NuminaMath-CoT)는 AIMO Prize 우승팀이 사용한 860k 수학 문제 데이터셋입니다.

## 데이터셋 특징

### 규모 및 구성

- **총 문제 수**: ~860,000개
- **형식**: Chain-of-Thought (CoT) 솔루션
- **언어**: 영어 (일부 중국어 문제 번역)
- **답변 형식**: LaTeX `\boxed{}` 포맷

### 출처별 분포

| Source | Count | Percentage | Difficulty |
|--------|-------|------------|------------|
| cn_k12 | 276,591 | 32.2% | Medium |
| synthetic_math | 167,895 | 19.5% | Medium |
| orca_math | 153,334 | 17.8% | Easy |
| olympiads | 150,581 | 17.5% | Hard |
| synthetic_amc | 62,111 | 7.2% | Medium-Hard |
| aops_forum | 30,201 | 3.5% | Hard |
| gsm8k | 7,345 | 0.9% | Easy |
| math | 7,478 | 0.9% | Hard |
| amc_aime | 4,072 | 0.5% | Hard |

### 난이도 분포 (추정)

- **Easy** (GSM8K, Orca): ~160k (18.6%)
- **Medium** (CN_K12, Synthetic): ~506k (58.9%)
- **Hard** (Olympiads, AMC, AOPS): ~193k (22.5%)

## 사용 방법

### 1. 설치

```bash
pip install datasets
```

### 2. 데이터셋 다운로드 및 평가 세트 생성

```bash
python setup_numina_dataset.py
```

이 스크립트는:
- NuminaMath-CoT 데이터셋 다운로드 (첫 실행 시만)
- 60개 균형 잡힌 평가 세트 생성 (Easy: 10, Medium: 20, Hard: 30)
- 5000개 훈련 샘플 추출

### 3. Python에서 사용

```python
from src.data.numina_loader import NuminaMathDataLoader

# 로더 생성
loader = NuminaMathDataLoader()

# 데이터셋 로드 (스트리밍 모드 권장)
dataset = loader.load_dataset(streaming=True)

# 특정 출처에서 샘플 가져오기
olympiad_problems = loader.get_sample_by_source('olympiads', n=10)

# 난이도별 샘플 가져오기
hard_problems = loader.get_difficulty_samples('hard', n=20)

# 평가 세트 생성
eval_set = loader.create_evaluation_set(
    n_easy=10,
    n_medium=20,
    n_hard=30,
    output_file="my_eval_set.json"
)

# 훈련 데이터 내보내기
loader.export_training_data(
    n_samples=10000,
    output_file="my_training_data.jsonl"
)
```

## 데이터 형식

### 원본 형식

```json
{
  "source": "olympiads",
  "problem": "Find all prime numbers p such that...",
  "solution": "To solve this problem, we first observe that...\n\nThus, the answer is $\\boxed{p = 2, 3, 5}$."
}
```

### 훈련용 변환 형식

```json
{
  "problem": "Find all prime numbers p such that...",
  "solution": "To solve this problem, we first observe that...",
  "answer": "p = 2, 3, 5",
  "source": "olympiads"
}
```

## AIMO 우승팀의 활용 방법

### NuminaMath Team 전략

1. **Fine-tuning**: DeepSeek 모델을 이 데이터로 fine-tune
2. **Tool-Integrated Reasoning (TIR)**: 
   - 문제 → 코드 생성 → 실행 → 검증
   - 3가지 fallback 전략 (Hybrid, Simulator, Theoretician)
3. **Majority Voting**: 48개 후보 솔루션 생성 후 다수결
4. **성능**: AIMO Progress Prize에서 29/50 달성

### 우리 프로젝트 통합 방안

#### 현재 시스템
```
User Problem → Orchestrator → TIR Pipeline → Code → Execute → Answer
```

#### NuminaMath 데이터 활용
```
1. Evaluation:
   - 현재 시스템을 NuminaMath 평가 세트로 벤치마크
   - 출처별/난이도별 성능 분석
   
2. Fine-tuning:
   - Qwen 2.5 Coder를 NuminaMath 데이터로 추가 학습
   - CoT 형식에 맞춰 프롬프트 개선
   
3. Hybrid Training:
   - Easy/Medium: 빠른 direct solving 학습
   - Hard: Decomposition + Hybrid Engine 적용
```

## 평가 계획

### Phase 1: Baseline 측정
```bash
python run_numina_evaluation.py --split easy
python run_numina_evaluation.py --split medium
python run_numina_evaluation.py --split hard
```

### Phase 2: 시스템별 비교
- Standard TIR Pipeline
- Hierarchical Decomposer
- Hybrid Reasoning Engine (New)

### Phase 3: 개선 및 반복
- 실패 케이스 분석
- Prompt engineering
- 모델 fine-tuning (선택사항)

## 메트릭

### 정량적
- **Accuracy**: 정답률
- **Pass@K**: K개 시도 중 성공률
- **Solve Time**: 평균 해결 시간

### 정성적
- **CoT Quality**: 추론 과정의 명확성
- **Code Quality**: 생성된 코드의 정확성
- **Decomposition**: 복잡한 문제 분해 능력

## 주요 파일

```
AIMO3_Project/
├── src/
│   └── data/
│       └── numina_loader.py          # 데이터셋 로더
├── data/
│   ├── numina_cache/                 # 캐시 디렉토리
│   ├── numina_eval_balanced.json     # 평가 세트
│   └── numina_training_5k.jsonl      # 훈련 샘플
├── setup_numina_dataset.py           # 셋업 스크립트
└── docs/
    └── NUMINA_INTEGRATION.md         # 이 문서
```

## 참고 자료

- [NuminaMath Dataset (Hugging Face)](https://huggingface.co/datasets/AI-MO/NuminaMath-CoT)
- [Project Numina GitHub](https://github.com/project-numina/aimo-progress-prize)
- [NuminaMath Technical Report (PDF)](https://github.com/project-numina/aimo-progress-prize/blob/main/report/numina_dataset.pdf)
- [AIMO Progress Prize](https://aimoprize.com/)

## 라이선스

Apache License 2.0 (NuminaMath-CoT dataset)

---

**작성일**: 2025-11-23  
**버전**: 1.0  
**상태**: 통합 준비 완료
