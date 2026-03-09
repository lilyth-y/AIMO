# 개선사항 P0 ~ P6 정리

**기준:** 터미널/평가 분석 기반 순차 적용 (2026-02)

---

## 완료된 개선 (P0 ~ P3)

| 구분 | 내용 | 적용 위치 |
|------|------|-----------|
| **P0** | 모델/토크나이저 기본값을 **repo_id**로 통일 (로컬 경로 제거) | `settings.py`, `config.py` |
| **P1a** | MULTI-AGENT 최종 답이 dict(role/content)일 때 **content에서 숫자 추출** 후 검증/저장 | `reasoning_utils.normalize_multi_agent_answer`, `orchestrator.py` |
| **P1b** | 실행 환경에 **math/sympy** 제공, 코드 생성 프롬프트에 sympy 사용 명시 | `stage4_execution._restricted_globals`, `solver.py` |
| **P2a** | 실행 전 **AST 문법 검사** → SyntaxError 시 조기 반환 | `stage4_execution._basic_static_check` |
| **P2b** | **NameError/AttributeError/SyntaxError** 시 수정 프롬프트 힌트 + 1회 LLM 재생성 | `orchestrator_helpers.build_fix_code_prompt`, `orchestrator.py` |
| **P3** | **OpenTelemetry** 기본 비연결(OMI_OTLP_TRACING=1 시에만), **TF oneDNN** 억제, **torch_dtype** 경고 억제 | `orchestrator.py`, `solver.py`, `examples/*.py` |

---

## P4: 한글/로그 인코딩 (MULTI-AGENT 로그 ASCII 안전) ✅

**목표:** Windows cp949 등에서 MULTI-AGENT 로그 한글 깨짐 방지.

**적용:**
- `multi_agent_reasoner.py`: Coding approach 출력 시 `approach`가 dict이면 content 일부만 사용, 비ASCII는 `encode("ascii","replace")`로 치환해 콘솔 깨짐 방지.

---

## P5: 실패 시 error 필드로 오류 분류 저장 ✅

**목표:** 모든 전략 실패·실행 오류 시 `EvaluationResult.error`에 원인 문자열을 넣어, gradient_report의 **error_summary**에서 syntax/runtime/timeout/oom 등으로 분류되도록 함.

**적용:**
- `run_numina_evaluation.py`, `quick_eval.py`, `run_aime_evaluation.py`: `solve_problem` 반환값에 `execution_result`(예: `Error: MemoryLimitExceeded`) 또는 `method == 'all_failed'`가 있으면 `EvaluationResult(error=...)`에 설정.
- `ErrorCategorizer`는 이미 "memory"/"timeout"/"syntax" 등으로 분류하므로 `error_summary`에 by_category 반영됨.

---

## P6: 평가 결과 → 문서 표 업데이트 ✅

**목표:** Numina/AIME 평가 완료 후 "현재 수준" 표를 결과로 갱신하는 방법 제공.

**적용:**
- `scripts/update_math_level_from_results.py`: `results/numina_balanced_results.json`(또는 aime_results.json)을 읽어 정확도·난이도별 수치를 출력. 출력 문장을 `docs/MATH_REASONING_LEVEL_AND_IMPROVEMENTS.md` 표에 붙여넣으면 됨.
- 사용법: `python scripts/update_math_level_from_results.py [results/numina_balanced_results.json]`
