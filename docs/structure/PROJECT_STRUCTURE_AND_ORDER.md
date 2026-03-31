# AIMO 전체 프로젝트 구조 및 순서

## 1. 디렉터리 구조 (엄밀 정의)

```
AIMO/
├── .github/                    # CI/CD
│   └── workflows/              # GitHub Actions (ci.yml, eval-on-release 등)
├── .cursor/                    # Cursor IDE 규칙/에이전트 (편집 제외)
├── archive/                    # 레거시·이전 버전 (참고용)
│   └── legacy/
├── dashboard/                  # 발표/모니터링용 웹 대시보드 (Vite + React)
│   ├── public/                 # 정적 파일, results/ 복사본
│   ├── src/                    # 프론트엔드 소스
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
├── data/                       # 데이터 파일 (평가·학습)
│   ├── numina_eval_balanced.json   # Numina 평가 60문항
│   ├── numina_training_5k.jsonl    # 학습용 (선택)
│   ├── eval_data.jsonl             # 평가 입출력 (선택)
│   └── numina_cache/               # HuggingFace Numina 캐시 (자동 생성)
├── docs/                       # 문서 (본 파일 포함)
├── docker/                     # 컨테이너 이미지 (Vertex·Cloud Run 등)
│   ├── vertex-serve/           # 커스텀 추론 서빙
│   ├── vertex-train/           # QLoRA 등 학습 잡
│   └── cloud-run/              # Cloud Run 배포용 (선택)
├── examples/                   # 실행 진입점·예제 스크립트
│   ├── run_numina_evaluation.py    # Numina 평가 실행
│   ├── run_aime_evaluation.py       # AIME 평가
│   ├── quick_eval.py                # 소규모 빠른 평가
│   └── ...
├── logs/                       # 런타임 로그 (gitignore, 자동 생성)
├── notebooks/                  # 실험·파인튜닝 노트북
│   ├── train_qlora.py / .ipynb     # QLoRA 파인튜닝
│   └── ...
├── results/                    # 평가 결과 JSON (gitignore, 자동 생성)
├── scripts/                    # 유틸리티·설정 스크립트
│   ├── setup_numina_dataset.py
│   ├── estimate_eval_time.py
│   ├── vertex/                 # Vertex AI·GCS·엔드포인트·BigQuery 연동
│   │   ├── vertex_common.py
│   │   ├── deploy_vertex_endpoint.py
│   │   └── ...
│   └── ...
├── src/                        # 메인 소스 (패키지 루트)
│   ├── data/                   # 데이터 로더
│   │   └── numina_loader.py
│   ├── evaluation/             # 평가 메트릭·리포트
│   │   ├── evaluation_utils.py
│   │   ├── config.py
│   │   ├── comprehensive_reporting.py
│   │   └── ...
│   ├── kaggle/                 # Kaggle 게이트웨이·프로토콜
│   │   ├── aimo_3_gateway.py
│   │   └── core/
│   ├── pipeline/               # 핵심 파이프라인
│   │   ├── interface.py       # Kaggle → 오케스트레이터 진입
│   │   ├── orchestrator.py    # 5단계 오케스트레이터
│   │   ├── solver.py          # LLM 호출·코드 생성
│   │   ├── stage1_labeling.py
│   │   ├── stage2_retrieval.py
│   │   ├── stage3_router.py
│   │   ├── stage4_execution.py
│   │   ├── stage5_verification.py
│   │   ├── refine_loop.py
│   │   ├── reconciliation.py
│   │   ├── remote_inference.py          # 원격 추론
│   │   ├── vertex_inference.py          # Vertex(Gemini 등) 백엔드
│   │   ├── vertex_endpoint_inference.py # 커스텀 엔드포인트
│   │   └── ...
│   └── data_generation/        # 데이터 생성 (선택)
├── tests/                      # 단위·통합 테스트
├── requirements.txt            # 기본 Python 의존성
├── requirements-vertex.txt     # Vertex/GCP SDK 등 (선택)
├── requirements-kaggle.txt     # Kaggle 노트북·런타임용 분기 (선택)
├── requirements-cloudrun.txt   # Cloud Run (선택)
├── README.md
└── (기타 requirements-*.txt, compose.yml 등)
```

---

## 2. 모듈 의존 순서 (빌드/이해 순서)

아래 순서대로 읽으면 “데이터 → 평가 → 파이프라인 → 진입점” 흐름을 유지할 수 있습니다.

| 순서 | 영역 | 경로 | 설명 |
|------|------|------|------|
| 1 | 설정 | `src/evaluation/config.py` | 데이터/결과 경로, 상수 |
| 2 | 데이터 | `src/data/numina_loader.py` | Numina 로드·평가셋 생성 |
| 3 | 평가 유틸 | `src/evaluation/evaluation_utils.py` | 메트릭, 결과 저장, 정답 검증 |
| 4 | 파이프라인 설정 | `src/pipeline/config.py`, `settings.py`, `model_config.py` | 파이프라인·모델 설정 |
| 5 | 단계 모듈 | `stage1_labeling.py` → … → `stage5_verification.py` | 5단계 구현 |
| 6 | 솔버·보조 | `solver.py`, `refine_loop.py`, `reconciliation.py` | LLM 호출, 재시도, 검증 |
| 7 | 오케스트레이터 | `src/pipeline/orchestrator.py` | 5단계 조율, Fallback, RefineLoop |
| 8 | 진입점 | `src/pipeline/interface.py` | Kaggle Gateway → `orchestrator.solve_problem()` |
| 9 | 실행 스크립트 | `examples/run_numina_evaluation.py` 등 | 평가 실행 |
| 10 | 대시보드 | `dashboard/` | 결과 시각화 (선택) |

---

## 3. 실행 순서 (작업 흐름)

### 3.1 최초 1회

1. **환경**: `pip install -r requirements.txt`, (선택) GPU 드라이버·CUDA.
2. **데이터**: `python scripts/setup_numina_dataset.py` → `data/` 에 평가/학습 데이터 준비.
3. **모델**: HuggingFace에서 모델 자동 다운로드 (처음 실행 시). `HF_HOME` 등 캐시 경로 설정 권장.

### 3.2 평가 실행 순서

1. (선택) `OMI_MODEL` 또는 `AIMO_MODEL`, `OMI_QUANTIZATION` 또는 `AIMO_QUANTIZATION` 등으로 모델/양자화 설정 ([`src/pipeline/settings.py`](../../src/pipeline/settings.py) 기준).
2. `python examples/run_numina_evaluation.py` → `results/numina_balanced_results.json` 생성.
3. (선택) `python examples/run_aime_evaluation.py` 등 다른 평가 실행.
4. (선택) `dashboard/public/results/` 에 결과 복사 후 `dashboard` 에서 `npm run dev` → 브라우저에서 정확도/풀이 과정 확인.

### 3.3 파인튜닝 후 평가

1. `notebooks/train_qlora.ipynb` 또는 `train_qlora.py` 실행 → LoRA 어댑터 저장.
2. 파이프라인 설정에서 해당 어댑터 경로 지정.
3. 위 “평가 실행 순서” 2~4 반복.

### 3.4 CI/자동 평가

1. `.github/workflows/` 워크플로: 푸시/릴리스 시 테스트 또는 평가 실행.
2. GPU가 필요하면 self-hosted runner 또는 원격 추론 URL 사용 (`docs/finetuning-resources/EXTERNAL_COMPUTE_OPTIONS.md` 참고).

### 3.5 클라우드·Vertex 경로 (선택)

로컬 `examples/` 평가와 별도로, **GCS 아티팩트 → 커스텀 이미지 → Vertex Endpoint** 흐름은 `docker/vertex-*`, `scripts/vertex/`, `docs/vertex/`를 따른다. 관리형 **Gemini(Vertex AI)** 를 파이프라인 백엔드로 쓰는 설정은 `docs/run-eval/VERTEX_AI.md`를 본다 (용어 “Vertex”가 두 갈래로 쓰일 수 있음).

---

## 4. 데이터 흐름 (엄밀)

```
[data/numina_eval_balanced.json 등]
        ↓
examples/run_*_evaluation.py
        ↓
src/pipeline/interface.py (Kaggle 시) 또는 직접 orchestrator.solve_problem()
        ↓
src/pipeline/orchestrator.py
        ↓
Stage1 → Stage2 → Stage3 → Stage4 → Stage5 (및 RefineLoop/Fallback)
        ↓
EvaluationMetrics.add_result() / save_results()
        ↓
results/*.json
        ↓
dashboard (fetch) 또는 comprehensive_reporting / benchmarking
```

---

## 5. 명명·규칙 요약

- **소스**: `src/` 아래만 메인 패키지. `examples/`는 실행 스크립트, `scripts/`는 설정·유틸.
- **데이터**: `data/` 고정. 평가 결과는 `results/`, 로그는 `logs/`.
- **문서**: `docs/` 에 계획·가이드·리포트. 본 문서는 구조·순서의 단일 참조.
- **환경 변수 (코드 기준)**: 모델·양자화·Refine·실행 제한 등은 **`src/pipeline/settings.py`**가 단일 진실 원천이다. 요약 표는 루트 `README.md`와 동일하게 유지하고, 세부는 `docs/run-eval/RUN_EVALUATION_ENVIRONMENT.md`, `docs/run-eval/README_MODELS.md`를 참고한다.
- **과거 문서 명칭**: 일부 문서·아카이브에 **MathCodeOrchestrator**(대회·프로젝트 구명)가 남아 있을 수 있다. 현재 코드·루트 README는 **OMI / AIMO** 환경 변수 체계를 쓴다.

이 문서는 “디렉터리 구조”, “모듈 읽는 순서”, “실행/작업 순서”, “데이터 흐름”을 엄밀히 정의한 기준 문서입니다.
