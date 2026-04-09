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
│   ├── evaluation/        # 평가 유틸리티
│   ├── data/              # 데이터 로더
│   └── kaggle/            # Kaggle 평가 관련
│
├── examples/               # 예제·평가 실행 스크립트
├── tests/                  # 테스트
├── scripts/                # 유틸리티 (setup_numina_dataset, organize_pd_project 등)
├── docs/                   # 문서 (폴더별 정리, README가 인덱스)
├── dashboard/              # 발표용 웹 대시보드 (Vite + React)
├── notebooks/              # 파인튜닝 등 실험 노트북
├── data/                   # 데이터 파일
└── archive/                # 아카이브
    └── legacy/             # 레거시 코드
```

**문서**: [docs/README.md](docs/README.md) (인덱스) · [docs/structure/PROJECT_STRUCTURE_AND_ORDER.md](docs/structure/PROJECT_STRUCTURE_AND_ORDER.md) (구조)

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 의존성 설치 (로컬·일반 VM)
pip install -r requirements.txt

# 환경 변수 설정 (선택사항). 우선순위·기본값은 src/pipeline/settings.py 기준.
export OMI_MODEL="Qwen/Qwen2.5-Math-1.5B-Instruct"   # 또는 AIMO_MODEL (폴백)
export OMI_QUANTIZATION="4bit"                       # 또는 AIMO_QUANTIZATION (폴백)
export HF_HOME="~/hf_cache"
```

**Google Cloud Shell** 등 홈 디스크가 좁은 경우: 전체 `requirements.txt`를 그대로 깔면 용량이 부족해질 수 있다. Vertex만 먼저 쓸 때는 [docs/run-eval/CLOUD_NUMINA_RUN.md](docs/run-eval/CLOUD_NUMINA_RUN.md)와 `requirements-cloudshell-smoke.txt`를 본다.

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

### 5. (권장) 쉬운 문제만 + 저렴하게 실행 (Windows)

비용이 과하게 나오는 걸 방지하기 위해, 기본 실행 경로는 **easy-only**로 고정하는 것을 권장합니다.

```powershell
.\scripts\run_numina_easy_cheap.ps1
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

- **[문서 인덱스 (폴더별 정리)](docs/README.md)** — 여기서 모든 문서를 카테고리별로 찾을 수 있습니다.
- [프로젝트 구조·순서](docs/structure/PROJECT_STRUCTURE_AND_ORDER.md)
- [AIMO3 리포트](docs/AIMO3/Report.md)
- [NuminaMath 통합](docs/guides/NUMINA_INTEGRATION.md) · [1.5 업그레이드](docs/guides/NUMINA_15_UPGRADE.md)
- [requirements 선택 가이드](docs/run-eval/REQUIREMENTS_SELECTION_GUIDE.md) · [Vertex 문서 동기화 체크리스트](docs/vertex/VERTEX_DOC_SYNC_CHECKLIST.md) · [Capacity+Token 실행 계획](docs/vertex/CAPACITY_AND_TOKEN_EFFICIENCY_EXECUTION_PLAN.md)

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

- `README.md` - 문서 인덱스 (폴더별 정리)
- `getting-started/` - 소개 · `structure/` - 구조 · `run-eval/` - 실행·평가
- `finetuning-resources/` - 파인튜닝·재원 · `guides/` - 가이드 · `todo/` - 할 일
- `AIMO3/` - 대회 리포트 · `archive/` - 과거 문서

### 아카이브 (archive/)

- `legacy/AIMO_core/` - 초기 코어 프로젝트 (레거시)

## ⚙️ 환경 변수

단일 기준은 `[src/pipeline/settings.py](src/pipeline/settings.py)`입니다. 아래는 자주 쓰는 항목만 요약합니다.


| 변수                          | 의미                                 | 기본·비고                                                 |
| --------------------------- | ---------------------------------- | ----------------------------------------------------- |
| `OMI_MODEL`                 | Hugging Face `repo_id` 또는 로컬 모델 경로 | 없으면 `AIMO_MODEL` → 기본 `Qwen/Qwen2.5-Math-7B-Instruct` |
| `AIMO_MODEL`                | `OMI_MODEL` 폴백                     | 위와 동일 체인                                              |
| `OMI_QUANTIZATION`          | `4bit` / `8bit` / `none`           | 없으면 `AIMO_QUANTIZATION` → 기본 `8bit`                   |
| `AIMO_QUANTIZATION`         | 양자화 폴백                             |                                                       |
| `OMI_REFINE_MAX_ITERATIONS` | Refine 루프 최대 반복                    | 기본 `3`                                                |
| `OMI_REFINE_ENABLED`        | Refine 루프 on/off                   | 기본 `true`                                             |
| `OMI_EXECUTOR_TIMEOUT`      | 코드 실행 타임아웃(초)                      | 기본 `5.0`                                              |
| `AIMO_EXECUTOR_MEMORY_MB`   | 실행 메모리 상한(MB), `0`이면 미사용           | 기본 `0`                                                |
| `AIMO_FAST_TEST`            | `1`이면 빠른 테스트 모드                    | 기본 `0`                                                |
| `OMI_LOG_PATH`              | 평가 로그 JSONL 경로                     | 기본 `logs/eval_log.jsonl`                              |
| `HF_HOME`                   | Hugging Face 캐시 루트                 | 선택                                                    |
| `TRANSFORMERS_CACHE`        | Transformers 캐시                    | 선택                                                    |


## 📊 평가 데이터셋

- **AIME**: 90개 공식 AIME 문제 (2022-2024)
- **NuminaMath**: 60개 균형 잡힌 평가 세트

## 🔧 개발

문서 전체 목록과 구조는 [docs/README.md](docs/README.md)를 참조하세요.

## 📄 라이선스

[라이선스 정보 추가]