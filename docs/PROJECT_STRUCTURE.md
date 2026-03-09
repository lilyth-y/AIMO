# MathCodeOrchestrator 프로젝트 구조

## 디렉토리 구조

```
MathCodeOrchestrator/
├── src/                          # 소스 코드
│   ├── pipeline/                # 메인 파이프라인
│   │   ├── orchestrator.py      # 오케스트레이터 (메인)
│   │   ├── solver.py            # LLM 솔버
│   │   ├── stage1_labeling.py  # Stage 1: 라벨링
│   │   ├── stage2_retrieval.py # Stage 2: 검색
│   │   ├── stage3_router.py    # Stage 3: 라우팅
│   │   ├── stage4_execution.py # Stage 4: 실행
│   │   ├── stage5_verification.py # Stage 5: 검증
│   │   └── ...
│   ├── evaluation/              # 평가 유틸리티
│   │   ├── evaluation_utils.py # 평가 메트릭 및 유틸리티
│   │   ├── config.py            # 평가 설정
│   │   └── run_evaluation.py   # 평가 실행
│   ├── data/                    # 데이터 로더
│   │   └── numina_loader.py    # NuminaMath 데이터 로더
│   └── data_generation/         # 데이터 생성
│
├── examples/                     # 예제 스크립트
│   ├── quick_eval.py           # 빠른 평가 (5개 문제)
│   ├── run_aime_evaluation.py  # AIME 평가
│   ├── run_numina_evaluation.py # NuminaMath 평가
│   └── ...
│
├── tests/                        # 테스트 파일
│   ├── test_evaluation_utils.py
│   ├── test_evaluation_scripts.py
│   ├── test_real_imo_puzzle.py
│   └── ...
│
├── scripts/                      # 유틸리티 스크립트
│   ├── setup_numina_dataset.py # 데이터셋 설정
│   ├── estimate_eval_time.py   # 시간 추정
│   └── ...
│
├── docs/                         # 문서
│   ├── NUMINA_15_UPGRADE.md
│   ├── HYBRID_REASONING_ARCHITECTURE.md
│   └── ...
│
├── data/                         # 데이터 파일
│   ├── aime_validation_90.json
│   └── numina_eval_balanced.json
│
├── logs/                         # 로그 파일 (gitignore)
├── results/                      # 결과 파일 (gitignore)
│
├── requirements.txt              # Python 의존성
├── Dockerfile                    # Docker 설정
└── README.md                     # 메인 README
```

## 주요 파일 설명

### 소스 코드 (src/)

#### pipeline/
- **orchestrator.py**: 전체 파이프라인을 조율하는 메인 오케스트레이터
- **solver.py**: LLM을 사용한 코드 생성 및 문제 해결
- **stage1_labeling.py**: 문제 분류 및 라벨링
- **stage2_retrieval.py**: 관련 문제/해법 검색
- **stage3_router.py**: 전략 선택 (Simulator/Theoretician/Hybrid)
- **stage4_execution.py**: 생성된 코드 실행
- **stage5_verification.py**: 답변 검증

#### evaluation/
- **evaluation_utils.py**: 평가 메트릭, 결과 저장, 답변 검증
- **config.py**: 평가 설정 및 경로 관리

### 예제 스크립트 (examples/)

- **quick_eval.py**: 빠른 평가 (5개 문제, 메모리 효율적)
- **run_aime_evaluation.py**: AIME 데이터셋 평가
- **run_numina_evaluation.py**: NuminaMath 데이터셋 평가
- **run_simple_eval.py**: 간단한 평가 (mock fallback 포함)

### 테스트 (tests/)

- **test_evaluation_utils.py**: 평가 유틸리티 테스트
- **test_evaluation_scripts.py**: 평가 스크립트 import 테스트
- **test_real_imo_puzzle.py**: IMO/퍼즐 문제 테스트

### 스크립트 (scripts/)

- **setup_numina_dataset.py**: NuminaMath 데이터셋 다운로드 및 설정
- **estimate_eval_time.py**: 평가 시간 추정
- **analyze_logs.py**: 로그 분석

## 사용 방법

### 빠른 평가 실행
```bash
python examples/quick_eval.py
```

### AIME 평가 실행
```bash
python examples/run_aime_evaluation.py
```

### NuminaMath 평가 실행
```bash
python examples/run_numina_evaluation.py
```

### 테스트 실행
```bash
python -m pytest tests/
# 또는
python tests/test_evaluation_utils.py
```

## 데이터 파일

- **data/aime_validation_90.json**: AIME 검증 세트 (90개 문제)
- **data/numina_eval_balanced.json**: NuminaMath 평가 세트 (60개 문제)

데이터 파일은 `scripts/setup_numina_dataset.py`를 실행하여 생성할 수 있습니다.

## 환경 변수

- `MathCodeOrchestrator_MODEL`: 사용할 모델 (예: `Qwen/Qwen2-1.5B-Instruct`)
- `MathCodeOrchestrator_QUANTIZATION`: 양자화 설정 (예: `4bit`)
- `HF_HOME`: HuggingFace 캐시 디렉토리
- `TRANSFORMERS_CACHE`: Transformers 캐시 디렉토리

## 주의사항

- `logs/`와 `results/` 디렉토리는 `.gitignore`에 포함되어 있습니다.
- 데이터 파일은 Git에 포함되지 않을 수 있습니다 (용량 문제).
- 모델 파일은 `.cache/`에 저장되며 Git에 포함되지 않습니다.
