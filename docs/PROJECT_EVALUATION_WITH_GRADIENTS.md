# OMI 프로젝트 평가: 진행 상황, 수학 메트릭, DevOps 그라디언트

**작성일:** 2026-02-22  
**대상:** OMI (Orchestrated Math Interpreter) / AIMO

---

## 1. 프로젝트 진행 평가 (Progress Evaluation)

### 1.1 목표 대비 현황

| 영역 | 목표 | 현재 상태 | 비고 |
|------|------|-----------|------|
| **5-Stage 파이프라인** | 라벨링 → 검색 → 라우팅 → 실행 → 검증 | ✅ 구현 완료 | `src/pipeline/orchestrator.py` 중심 |
| **평가 프레임워크** | 표준 메트릭, 결과 저장, 재현성 | ✅ 구현 완료 | `src/evaluation/` 통합 |
| **수학 데이터** | AIME, NuminaMath 평가 세트 | ✅ 로더·스크립트 존재 | `data/`, `scripts/setup_numina_dataset.py` |
| **Kaggle 연동** | AIMO3 게이트웨이·제출 | ✅ 구조 존재 | `src/kaggle/` |
| **IMO/고난이도** | Plan & Code, 검증 라우터 | ✅ 설계·구현 | Refine Loop, 검증 강화 적용 |

### 1.2 완성도 요약

- **아키텍처:** 5-Stage + Simulator/Theoretician/Hybrid 전략, Refine Loop 적용.
- **평가:** 기본 정확도, 난이도/소스/메서드별 분해, 고급 메트릭(신뢰구간, McNemar, 오류 분류), 벤치마크·리포팅.
- **데이터:** NuminaMath-1.5 로더, 난이도별 샘플링, AIME 90문항 검증 세트.
- **문서:** PD 구조, AIMO3 리포트, Numina 통합, 종합 평가 요약 등 다수.

### 1.3 갭 및 다음 단계

- **CI/CD:** `.github/workflows` 없음 → 테스트/평가 자동화 권장.
- **수학 그라디언트:** 난이도 구간별 정확도·트렌드는 구현됐으나, **수학적 난이도 점수(DifficultyMetrics)** 와 평가 스크립트 연동 보강 가능.
- **DevOps:** Docker·compose·리소스 제한 있음; 헬스체크·로깅 정책 명시 시 프로덕션 그라디언트 상승.

---

## 2. 수학 평가 그라디언트 (Mathematical Gradients)

수학 평가의 “완전성”을 단계별로 나눈 그라디언트. 단순 정확도(L1) → 난이도/소스 분해(L2) → 통계적 엄밀성(L3) → 난이도 구간·효과크기(L4) → 도메인·리포트 완전성(L5) 순으로 단계가 올라갑니다.

### 2.1 수학 그라디언트 단계 정의

| 단계 | 이름 | 점수 구간 | 설명 | 포함 메트릭 예시 |
|------|------|-----------|------|------------------|
| L1 | Basic | 0.00–0.35 | 기본 정확도만 보고 | accuracy |
| L2 | Stratified | 0.35–0.55 | 난이도/소스별 분해 및 기본 통계 | by_difficulty, by_source |
| L3 | Statistical | 0.55–0.75 | 신뢰구간, 검정, 오류 분류 | accuracy_ci, mcnemar, error_categorization |
| L4 | Rigor | 0.75–0.90 | 난이도 구간별 정확도, 효과크기, 정량적 난이도 | accuracy_by_quantile, effect_size, difficulty_score |
| L5 | Full | 0.90–1.00 | 수학적 완전성: 모든 메트릭 + 도메인별 분석 | domain_accuracy, rigor_report |

### 2.2 현재 구현과의 매핑

- **EvaluationMetrics (evaluation_utils):** accuracy, by_difficulty, by_source, by_method → **L2** 대응.
- **AdvancedEvaluator (advanced_metrics):** Wilson CI, McNemar, 오류 분류, latency, quantile, effect size → **L3–L4** 대응.
- **BenchmarkRun:** easy/medium/hard 정확도 필드 → 난이도 그라디언트 트렌드 분석에 사용 가능.
- **DifficultyMetrics (data_generation):** 추론 단계, 개념 수, 분기 등 → 평가 시 “정량적 난이도”로 넣으면 **L4** 강화.
- **compute_difficulty_gradient (mathematical_devops_gradients):** 난이도별 정확도 시퀀스·트렌드(decreasing/increasing/flat) 제공 → 수학 그라디언트 리포트에 포함.

### 2.3 난이도 그라디언트 (Difficulty Gradient)

- **의미:** easy → medium → hard (→ olympiad) 순으로 정확도가 어떻게 변하는지.
- **기대:** 일반적으로 “decreasing” (어려울수록 정확도 하락).
- **구현:** `evaluate_mathematical_and_devops()` 호출 시 `metrics["by_difficulty"]`가 있으면 자동으로 `difficulty_gradient` (levels, accuracy_gradient, gradient_trend)가 채워짐.

### 2.4 사용 예시 (수학 + DevOps 통합)

```python
from src.evaluation import EvaluationMetrics, evaluate_mathematical_and_devops

metrics_obj = EvaluationMetrics("numina_eval")
# ... add_result() 로 결과 추가 ...
metrics = metrics_obj.calculate_metrics()

gradient_report = evaluate_mathematical_and_devops(metrics)
# gradient_report["mathematical"]["score"], ["level"], ["difficulty_gradient"]
# gradient_report["devops"]["score"], ["level"]
```

---

## 3. DevOps 그라디언트 (DevOps Gradients)

배포·재현성·자동화 수준을 단계별로 나눈 그라디언트. 수동/문서(D1) → 재현 가능 환경(D2) → CI/테스트 자동화(D3) → 배포·리소스 준비(D4) → 프로덕션 수준(D5) 순입니다.

### 3.1 DevOps 그라디언트 단계 정의

| 단계 | 이름 | 점수 구간 | 설명 | 체크 항목 예시 |
|------|------|-----------|------|-----------------|
| D1 | AdHoc | 0.00–0.25 | 수동 실행, 문서만 존재 | readme, requirements |
| D2 | Reproducible | 0.25–0.50 | 고정 환경으로 재현 가능 | docker, compose, pinned_versions |
| D3 | Automated | 0.50–0.75 | CI/테스트 자동화 | ci_yml, tests_runner, artifacts |
| D4 | DeployReady | 0.75–0.90 | 배포·모니터링 준비 | entrypoint, resource_limits |
| D5 | Production | 0.90–1.00 | 프로덕션 수준 파이프라인 | logging, metrics_export, secrets |

### 3.2 현재 상태 (자동 채점 기준)

- **D1:** README.md, requirements.txt → 충족.
- **D2:** Dockerfile, compose.yml, requirements 버전 고정(일부) → 충족.
- **D3:** `.github/workflows` 없음 → **미충족**; tests/ 디렉터리 존재 → 일부 충족.
- **D4:** entrypoint.sh, compose 내 cpus/memory 제한 → 충족.
- **D5:** 로깅·메트릭 내보내기는 코드 내부에 존재; 전용 헬스체크·시크릿 관리는 미정리.

**현재 DevOps 점수 추정:** D2 상단 ~ D3 하단 (재현 가능 + 테스트 디렉터리, CI 없음).

### 3.3 DevOps 개선 제안

1. **CI 추가:** `.github/workflows/ci.yml` – lint, 단위/평가 테스트, (선택) Docker 빌드.
2. **테스트 실행 정식화:** `pytest tests/` 또는 README에 명시된 테스트 커맨드 고정.
3. **헬스체크:** 서비스 모드일 때 HTTP/스크립트 기반 헬스 엔드포인트 또는 `entrypoint.sh` 내 체크.
4. **로깅/메트릭 정책:** 로그 경로, 평가 결과 디렉터리, (선택) 메트릭 export 방식을 문서에 명시.

---

## 4. 통합 요약

| 축 | 현재 수준 | 다음 목표 |
|----|-----------|-----------|
| **진행(Progress)** | 파이프라인·평가·데이터·문서 구현 완료 | CI로 회귀 방지, 난이도 점수 연동 |
| **수학 그라디언트** | L2–L4 (분해·통계·quantile 등 구현) | L5: 도메인별 정확도·리포트 자동화 |
| **DevOps 그라디언트** | D2–D3 사이 (Docker/Compose 있음, CI 없음) | D3 확실화(CI), D4/D5(헬스체크·로깅 정책) |

---

## 5. 참고 파일

- **수학·DevOps 그라디언트 구현:** `src/evaluation/mathematical_devops_gradients.py`
- **그라디언트 단계 문서(코드):** `get_gradient_levels_documentation()`
- **기본·고급 평가:** `src/evaluation/evaluation_utils.py`, `advanced_metrics.py`, `benchmarking.py`, `comprehensive_reporting.py`
- **난이도 정의:** `src/data_generation/difficulty_metrics.py`, `src/pipeline/problem_diversity.py`
- **프로젝트 구조:** `docs/PD_PROJECT_STRUCTURE.md`, `docs/COMPREHENSIVE_EVALUATION_SUMMARY.md`
