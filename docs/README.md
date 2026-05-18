# AIMO 문서 인덱스

문서는 **폴더별**로 나뉘어 있습니다. 이 파일에서 카테고리별로 찾을 수 있습니다.  
처음 보시면 **getting-started** → **structure** → **run-eval** 순서를 권장합니다.  
클라우드·GCS·커스텀 엔드포인트 실험을 할 계획이면 **structure** 직후 **`vertex/`** 와 **[VERTEX_SCRIPTS_EVALUATION.md](VERTEX_SCRIPTS_EVALUATION.md)** 를 함께 보면 좋습니다.

### “Vertex” 용어 두 가지

| 경로 | 역할 |
|------|------|
| [run-eval/VERTEX_AI.md](run-eval/VERTEX_AI.md) | **관리형 모델(Gemini 등)** 을 Vertex AI API로 두고 파이프라인 추론 |
| [vertex/](vertex/) · [vertex/WHY_THIS_VERTEX_STACK.md](vertex/WHY_THIS_VERTEX_STACK.md) | **GCS 아티팩트 + 커스텀 학습/서빙 이미지 + Endpoint** 연구 스택 |

---

## 폴더 구조

```
docs/
├── README.md                 ← 지금 문서 (인덱스)
├── getting-started/          # 시작하기
├── structure/                # 프로젝트 구조·순서
├── run-eval/                 # 실행·평가 (로컬·Kaggle·Vertex Gemini)
├── vertex/                   # GCS·커스텀 서빙·QLoRA·실험 프로토콜
├── eval/                     # 평가·채점 연대기
├── finetuning-resources/     # 파인튜닝·재원
├── guides/                   # 가이드 (기능별)
├── todo/                     # 할 일·다음 단계
├── pd/                       # PD 학기제 주간 등 보조 문서
├── AIMO3/                    # 대회·리포트
├── archive/                  # 과거·완료 문서 (참고용)
├── MATH_SOLVING_ARCHITECTURE_EVALUATION.md  # 수학 풀이 아키텍처 평가
└── VERTEX_SCRIPTS_EVALUATION.md            # Vertex 스크립트 점검·실행 기록
```

### 구명칭(MathCodeOrchestrator) 안내

과거 대회·프로젝트명으로 **MathCodeOrchestrator** 가 문서·아카이브에 남아 있을 수 있다. **현재 코드와 루트 README의 환경 변수는 `OMI_*` / `AIMO_*`** (`src/pipeline/settings.py`)를 기준으로 한다.

---

## 시작하기 · `getting-started/`

| 문서 | 설명 |
|------|------|
| [INTRODUCTION_LOW_LEVEL.md](getting-started/INTRODUCTION_LOW_LEVEL.md) | 수학/AI 비전공자용 한글 소개 |
| [INTRODUCTION_HIGH_LEVEL.md](getting-started/INTRODUCTION_HIGH_LEVEL.md) | 기술자용 소개 (아키텍처, 스택) |

---

## 프로젝트 구조·순서 · `structure/`

| 문서 | 설명 |
|------|------|
| [PROJECT_STRUCTURE_AND_ORDER.md](structure/PROJECT_STRUCTURE_AND_ORDER.md) | 전체 디렉터리 구조, 모듈 의존·실행 순서, 데이터 흐름 (기준 문서) |

---

## 실행·평가 · `run-eval/`

| 문서 | 설명 |
|------|------|
| [RUN_EVALUATION_ENVIRONMENT.md](run-eval/RUN_EVALUATION_ENVIRONMENT.md) | 평가 실행 환경 (모델, GPU, 메모리) |
| [README_AIMO_EVAL.md](run-eval/README_AIMO_EVAL.md) | AIMO 평가 개요 및 실행 방법 |
| [README_MODELS.md](run-eval/README_MODELS.md) | 모델 선택, VRAM, 파인튜닝 데이터 형식 |
| [QUICK_REFERENCE.md](run-eval/QUICK_REFERENCE.md) | 빠른 실행 명령어, 평가 레벨 |
| [FAST_EVAL.md](run-eval/FAST_EVAL.md) | 빠른 평가 (모델·문항 수 줄이기) |
| [KAGGLE_RUN.md](run-eval/KAGGLE_RUN.md) | Kaggle에서 평가 돌리기 가정·권장 |
| [KAGGLE_ENV_CHECK.md](run-eval/KAGGLE_ENV_CHECK.md) | Kaggle 실행 환경 점검 체크리스트 |
| [CLOUD_NUMINA_RUN.md](run-eval/CLOUD_NUMINA_RUN.md) | **Numina 평가를 클라우드(Vertex/Kaggle)에서만** 돌리는 절차 |
| [REQUIREMENTS_SELECTION_GUIDE.md](run-eval/REQUIREMENTS_SELECTION_GUIDE.md) | 실행 목적별 `requirements*.txt` 선택 매트릭스 |

루트 **요구사항 파일**: `requirements.txt`(전체 스택) · `requirements-vertex.txt`(Gemini 최소) · [`requirements-cloudshell-smoke.txt`](../requirements-cloudshell-smoke.txt)(Cloud Shell에서 Vertex 스모크만, 홈 디스크 절약).

Kaggle에서 바로 실행하려면 **`notebooks/run_numina_on_kaggle.ipynb`** 를 업로드해 사용하면 됩니다. 단계별 체크리스트: [KAGGLE_실행_체크리스트.md](run-eval/KAGGLE_실행_체크리스트.md).  
관리형 Vertex(Gemini) 백엔드: [VERTEX_AI.md](run-eval/VERTEX_AI.md).

---

## Vertex·GCS·커스텀 서빙 · `vertex/`

| 문서 | 설명 |
|------|------|
| [WHY_THIS_VERTEX_STACK.md](vertex/WHY_THIS_VERTEX_STACK.md) | 왜 GCS + 커스텀 컨테이너 + Endpoint인지 |
| [MERGED_MODEL_ARTIFACT.md](vertex/MERGED_MODEL_ARTIFACT.md) | 머지 모델 아티팩트 |
| [VERTEX_TRAIN_DEPLOY_QWEN.md](vertex/VERTEX_TRAIN_DEPLOY_QWEN.md) | 학습·배포 흐름 (Qwen 계열) |
| [DEPLOY_QWEN_7B_VERTEX.md](vertex/DEPLOY_QWEN_7B_VERTEX.md) | 7B 배포 참고 |
| [VERTEX_DOC_SYNC_CHECKLIST.md](vertex/VERTEX_DOC_SYNC_CHECKLIST.md) | Vertex 코드/문서 동기화 체크리스트 |
| [CAPACITY_AND_TOKEN_EFFICIENCY_EXECUTION_PLAN.md](vertex/CAPACITY_AND_TOKEN_EFFICIENCY_EXECUTION_PLAN.md) | 429 완화를 위한 capacity 신청 + token 효율화 실행 순서 |
| 기타 | 동 폴더의 `STEP1_*`, `STEP2_*`, `QUALITY_EXPERIMENT.md` 등 |

루트 [VERTEX_SCRIPTS_EVALUATION.md](VERTEX_SCRIPTS_EVALUATION.md) 는 `scripts/vertex/` 실전 점검 요약이다.

---

## 평가·채점 기록 · `eval/`

| 문서 | 설명 |
|------|------|
| [EVALUATION_AND_GRADING_CHRONICLE.md](eval/EVALUATION_AND_GRADING_CHRONICLE.md) | 평가·채점 관련 연대기 |

---

## 파인튜닝·재원 · `finetuning-resources/`

| 문서 | 설명 |
|------|------|
| [FINETUNING_GUIDE.md](finetuning-resources/FINETUNING_GUIDE.md) | 모델 파인튜닝 (QLoRA 절차, 실행 경로) |
| [RESOURCE_AND_BUDGET.md](finetuning-resources/RESOURCE_AND_BUDGET.md) | 추가 재원 조사 (GPU/클라우드, 필요 여부) |
| [EXTERNAL_COMPUTE_OPTIONS.md](finetuning-resources/EXTERNAL_COMPUTE_OPTIONS.md) | 로컬 GPU 없이 평가 (원격 API, Docker) |
| [README_DOCKER.md](finetuning-resources/README_DOCKER.md) | Docker 빌드·실행 (CPU/GPU) |

---

## 가이드 (기능별) · `guides/`

| 문서 | 설명 |
|------|------|
| [DASHBOARD_DEPLOYMENT.md](guides/DASHBOARD_DEPLOYMENT.md) | 대시보드 GitHub Pages 배포 가이드 |
| [REFINE_LOOP_USAGE.md](guides/REFINE_LOOP_USAGE.md) | RefineLoop 사용법 |
| [PROBLEM_DIVERSITY_GUIDE.md](guides/PROBLEM_DIVERSITY_GUIDE.md) | 문제 다양성·평가셋 구성 |
| [HYBRID_REASONING_ARCHITECTURE.md](guides/HYBRID_REASONING_ARCHITECTURE.md) | 하이브리드 추론 아키텍처 |
| [NUMINA_INTEGRATION.md](guides/NUMINA_INTEGRATION.md) | NuminaMath 데이터 통합 |
| [NUMINA_15_UPGRADE.md](guides/NUMINA_15_UPGRADE.md) | NuminaMath 1.5 업그레이드 |

---

## 할 일·다음 단계 · `todo/`

| 문서 | 설명 |
|------|------|
| [TODO.md](todo/TODO.md) | Moai Roadmap / TODO (P0~P3) |
| [NEXT_STEPS.md](todo/NEXT_STEPS.md) | 다음 단계 제안 |

---

## PD 보조 문서 · `pd/`

| 문서 | 설명 |
|------|------|
| [PD_WEEKLY_PROGRESS_300B.md](pd/PD_WEEKLY_PROGRESS_300B.md) | 주간 진행 등 (제목 참고) |

---

## 대회·리포트 · `AIMO3/`

| 문서 | 설명 |
|------|------|
| [AIMO3/README.md](AIMO3/README.md) | AIMO3 대회 개요 |
| [AIMO3/Report.md](AIMO3/Report.md) | AIMO3 전략·리포트 |
| [AIMO3/TODO.md](AIMO3/TODO.md) | AIMO3 할 일 |

---

## 과거·완료 문서 · `archive/`

완료된 작업 요약, 과거 계획, 시점 종속 리포트입니다. 필요할 때만 참고하세요.

→ [archive/README.md](archive/README.md) (54개 문서 보관)

---

**프로젝트 정리 요약**: [CLEANUP_2026.md](CLEANUP_2026.md) (.gitignore, 루트 정리, 문서 구조)
