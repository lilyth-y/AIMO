# 프로젝트 정리 분석 보고서

## 1. 중복/불필요한 파일들

### 1.1 임시 수정 스크립트 (삭제 권장)
이미 수정이 완료되어 더 이상 필요 없는 파일들:
- `fix_all_encoding.py` - 인코딩 문제 수정 완료
- `fix_encoding.py` - 인코딩 문제 수정 완료
- `fix_line_1106.py` - 특정 라인 수정 완료
- `fix_orchestrator_encoding.py` - 인코딩 문제 수정 완료
- `test_list_error_fix.py` - 리스트 오류 수정 테스트 (이미 수정 완료)

### 1.2 중복된 평가 스크립트
비슷한 기능을 하는 평가 스크립트들:
- `quick_eval.py` - 빠른 평가 (5개 문제)
- `run_simple_eval.py` - 간단한 평가 (mock fallback 포함)
- `run_aime_evaluation.py` - AIME 평가
- `run_numina_evaluation.py` - NuminaMath 평가
- `evaluate_outputs.py` - MCP 결과 평가
- `mock_eval.py` - Mock 평가
- `manual_evaluation.py` - 수동 평가
- `hf_eval_example.py` - HuggingFace 평가 예제
- `azure_evaluate.py` - Azure 평가

**권장사항**: 
- `quick_eval.py`를 메인 평가 스크립트로 유지
- `run_aime_evaluation.py`, `run_numina_evaluation.py`는 데이터셋별 평가로 유지
- 나머지는 통합 또는 삭제

### 1.3 중복된 테스트 파일
- `test_quick_eval.py` - quick_eval 테스트
- `test_fast_eval.py` - 빠른 평가 테스트
- `test_single_problem.py` - 단일 문제 테스트
- `test_imo_puzzle.py` - IMO 퍼즐 테스트
- `test_real_imo_puzzle.py` - 실제 IMO 퍼즐 테스트
- `test_puzzle.py` - 퍼즐 테스트
- `test_puzzle_prompt.py` - 퍼즐 프롬프트 테스트
- `test_evaluation_utils.py` - 평가 유틸리티 테스트
- `test_evaluation_scripts.py` - 평가 스크립트 테스트
- `test_evaluation_mock.py` - Mock 평가 테스트

**권장사항**: 
- `tests/` 디렉토리로 이동
- 통합 테스트 스위트로 재구성

### 1.4 중복된 시간 추정 스크립트
- `estimate_time.py` - 기본 시간 추정
- `estimate_eval_time.py` - 평가 시간 추정
- `realistic_time_estimate.py` - 현실적인 시간 추정

**권장사항**: 하나로 통합

### 1.5 중복된 솔버/예제 파일
- `geometry_solver.py` - 기하학 솔버
- `quadratic_solver.py` - 이차방정식 솔버
- `mcp_pipeline_example.py` - MCP 파이프라인 예제
- `hf_eval_example.py` - HuggingFace 평가 예제

**권장사항**: `examples/` 디렉토리로 이동 또는 삭제

### 1.6 중복된 설정/체크 파일
- `check_bnb_cuda.py` - BitsAndBytes CUDA 체크
- `kaggle_cred_test.py` - Kaggle 인증 테스트
- `verify_tool_usage.py` - 도구 사용 검증
- `system_test.py` - 시스템 테스트

**권장사항**: `scripts/` 또는 `tests/`로 이동

## 2. 디렉토리 구조 문제

### 2.1 중복된 디렉토리
- `MathCodeOrchestrator_core/` - 별도 코어 프로젝트? 통합 필요
- `src/pipeline/` - 메인 파이프라인
- `kaggle_evaluation/` - Kaggle 평가 관련

### 2.2 데이터 파일 위치 불명확
- 루트에 여러 `.jsonl`, `.json` 파일들
- `MathCodeOrchestrator_core/data/`에도 데이터 파일들
- `src/data/`에도 데이터 로더

**권장사항**: `data/` 디렉토리로 통합

## 3. 로그/결과 파일들 (삭제 권장)
- `full_aimo_run.log` - 실행 로그
- `run_math7b.log` - 모델 실행 로그
- `results.jsonl`, `results_orch.jsonl`, `results_vanilla.jsonl` - 결과 파일
- `generated_queries.json`, `generated_responses.json` - 생성된 데이터

**권장사항**: `.gitignore`에 추가, `logs/`, `results/` 디렉토리 사용

## 4. 문서 파일 정리
- `README_MathCodeOrchestrator_EVAL.md` - 평가 README
- `README_DOCKER.md` - Docker README
- `README_MODELS.md` - 모델 README
- `Development_Plan_and_Analysis.md` - 개발 계획
- `Plan_Review.md` - 계획 리뷰
- `Report.md` - 리포트
- `TODO.md` - TODO
- `DOCKER_STATUS.md` - Docker 상태
- `evaluation_report_baseline.md` - 평가 리포트
- `evaluation_report_llm.md` - LLM 평가 리포트
- `evaluation_summary.md` - 평가 요약

**권장사항**: `docs/` 디렉토리로 통합

## 5. 권장 디렉토리 구조

```
MathCodeOrchestrator/
├── README.md                    # 메인 README
├── requirements.txt
├── .gitignore
├── setup.py                     # 패키지 설정
│
├── src/                         # 소스 코드
│   ├── pipeline/               # 메인 파이프라인
│   ├── evaluation/             # 평가 유틸리티
│   ├── data/                   # 데이터 로더
│   └── data_generation/       # 데이터 생성
│
├── data/                        # 데이터 파일
│   ├── aime_validation_90.json
│   └── numina_eval_balanced.json
│
├── scripts/                     # 유틸리티 스크립트
│   ├── setup_numina_dataset.py
│   └── analyze_logs.py
│
├── tests/                       # 테스트 파일
│   ├── test_evaluation_utils.py
│   ├── test_pipeline.py
│   └── test_puzzle.py
│
├── examples/                    # 예제 스크립트
│   ├── quick_eval.py
│   └── run_aime_evaluation.py
│
├── docs/                        # 문서
│   ├── NUMINA_15_UPGRADE.md
│   └── HYBRID_REASONING_ARCHITECTURE.md
│
├── logs/                        # 로그 파일 (gitignore)
└── results/                     # 결과 파일 (gitignore)
```

## 6. 즉시 삭제 가능한 파일 목록

### 6.1 임시 수정 스크립트
- [ ] `fix_all_encoding.py`
- [ ] `fix_encoding.py`
- [ ] `fix_line_1106.py`
- [ ] `fix_orchestrator_encoding.py`
- [ ] `test_list_error_fix.py`

### 6.2 로그/결과 파일
- [ ] `full_aimo_run.log`
- [ ] `run_math7b.log`
- [ ] `results.jsonl`
- [ ] `results_orch.jsonl`
- [ ] `results_vanilla.jsonl`
- [ ] `generated_queries.json`
- [ ] `generated_responses.json`

### 6.3 중복 파일 (통합 후 삭제)
- [ ] `estimate_time.py` (estimate_eval_time.py로 통합)
- [ ] `test_fast_eval.py` (test_quick_eval.py로 통합)
- [ ] `test_single_problem.py` (test_quick_eval.py로 통합)
- [ ] `test_imo_puzzle.py` (test_real_imo_puzzle.py로 통합)
- [ ] `test_puzzle.py` (test_real_imo_puzzle.py로 통합)
- [ ] `test_puzzle_prompt.py` (test_real_imo_puzzle.py로 통합)

## 7. 정리 작업 순서

1. **1단계**: 임시 파일 삭제 (fix_*.py, 로그 파일)
2. **2단계**: 디렉토리 구조 생성 (tests/, examples/, docs/ 통합)
3. **3단계**: 파일 이동 및 정리
4. **4단계**: 중복 파일 통합
5. **5단계**: .gitignore 업데이트
6. **6단계**: README.md 업데이트
