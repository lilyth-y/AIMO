# OMI - Orchestrated Math Interpreter

**PD 학기제 프로젝트**

OMI (Orchestrated Math Interpreter)는 수학 문제를 체계적으로 오케스트레이션하고 코드로 해석하여 실행하는 AI 시스템입니다.

## 핵심 개념

- **Math Orchestration**: 수학 문제를 단계별로 분석하고 최적의 해결 전략을 조율
- **Code Interpreter**: 생성된 Python 코드를 실행하여 정확한 답을 도출

## 주요 특징

- **5-Stage Pipeline**: 문제 분석 → 검색 → 라우팅 → 실행 → 검증
- **다중 전략**: Simulator, Theoretician, Hybrid 전략 지원
- **코드 생성 및 실행**: LLM이 생성한 Python 코드를 안전하게 실행
- **평가 프레임워크**: 표준화된 평가 메트릭 및 결과 저장
- **IMO/퍼즐 문제 지원**: 특화된 프롬프트 및 라우팅

## 📁 프로젝트 구조

```
OMI/
├── src/                    # 메인 소스 코드
│   ├── pipeline/          # 5-Stage 파이프라인
│   │   └── orchestrator.py # 메인 오케스트레이터
│   ├── evaluation/        # 평가 유틸리티
│   ├── data/              # 데이터 로더
│   └── kaggle/            # Kaggle 평가 관련
│
├── examples/              # 예제 스크립트
├── tests/                 # 테스트 파일
├── scripts/               # 유틸리티 스크립트
├── docs/                  # 문서
│   └── AIMO3/            # OMI3 프로젝트 리포트
├── data/                  # 데이터 파일
└── archive/               # 아카이브
    └── legacy/            # 레거시 코드
```

**상세 구조**: [docs/PD_PROJECT_STRUCTURE.md](docs/PD_PROJECT_STRUCTURE.md)

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정 (선택사항)
export OMI_MODEL="Qwen/Qwen2-1.5B-Instruct"
export OMI_QUANTIZATION="4bit"
export HF_HOME="~/hf_cache"
```

### 2. 데이터셋 설정

```bash
python scripts/setup_numina_dataset.py
```

### 3. 빠른 평가 실행

```bash
python examples/quick_eval.py
```

### 4. 전체 평가 실행

```bash
# AIME 평가
python examples/run_aime_evaluation.py

# NuminaMath 평가
python examples/run_numina_evaluation.py
```

## 📚 주요 기능

### Math Orchestration
수학 문제를 체계적으로 분석하고 최적의 해결 전략을 선택합니다:
- 문제 분류 및 특징 추출
- 전략 라우팅 (Simulator/Theoretician/Hybrid)
- 다단계 추론 파이프라인

### Code Interpreter
생성된 Python 코드를 안전하게 실행하여 정확한 답을 도출합니다:
- 코드 생성 및 검증
- 샌드박스 실행
- 결과 추출 및 정규화

## 📖 문서

- [프로젝트 구조 (PD)](docs/PD_PROJECT_STRUCTURE.md)
- [상세 프로젝트 구조](docs/PROJECT_STRUCTURE.md)
- [AIMO3 프로젝트 리포트](docs/AIMO3/Report.md)
- [NuminaMath 통합](docs/NUMINA_INTEGRATION.md)
- [NuminaMath 1.5 업그레이드](docs/NUMINA_15_UPGRADE.md)

## 🧪 테스트

```bash
# 평가 유틸리티 테스트
python tests/test_evaluation_utils.py

# 평가 스크립트 테스트
python tests/test_evaluation_scripts.py

# IMO/퍼즐 문제 테스트
python tests/test_real_imo_puzzle.py
```

## 📝 프로젝트 구성 요소

### 메인 소스 (src/)
- `pipeline/` - 5-Stage 추론 파이프라인
- `evaluation/` - 평가 유틸리티 및 메트릭
- `data/` - 데이터 로더 (NuminaMath, AIME)
- `kaggle/` - Kaggle 평가 게이트웨이

### 예제 (examples/)
- `quick_eval.py` - 빠른 평가 (5개 문제)
- `run_aime_evaluation.py` - AIME 평가
- `run_numina_evaluation.py` - NuminaMath 평가

### 문서 (docs/)
- `AIMO3/` - AIMO3 프로젝트 리포트 및 문서
- 기타 아키텍처 및 통합 문서

### 아카이브 (archive/)
- `legacy/AIMO_core/` - 초기 코어 프로젝트 (레거시)

## ⚙️ 환경 변수

- `OMI_MODEL`: 사용할 모델 (예: `Qwen/Qwen2-1.5B-Instruct`)
- `OMI_QUANTIZATION`: 양자화 설정 (예: `4bit`, `8bit`)
- `HF_HOME`: HuggingFace 캐시 디렉토리
- `TRANSFORMERS_CACHE`: Transformers 캐시 디렉토리

## 📊 평가 데이터셋

- **AIME**: 90개 공식 AIME 문제 (2022-2024)
- **NuminaMath**: 60개 균형 잡힌 평가 세트

## 🔧 개발

프로젝트 구조 정리 및 개발 가이드는 [docs/PROJECT_ORGANIZATION.md](docs/PROJECT_ORGANIZATION.md)를 참조하세요.

## 📄 라이선스

[라이선스 정보 추가]
