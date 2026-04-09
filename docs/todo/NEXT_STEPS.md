# 다음 단계 (Next Steps)

**기준:** 2026-02-22 진행·평가·실행 정리 후

**이미 적용된 것 (자동화):**

- **CI:** `.github/workflows/ci.yml` – push/PR 시 lint(import 체크) + pytest + Docker 빌드 시도.
- **그라디언트·오류 요약:** `quick_eval.py`, `run_aime_evaluation.py`, `run_numina_evaluation.py` 실행 후 자동으로 `results/gradient_report_*.json` 저장 및 콘솔에 Math/DevOps 그라디언트 요약 출력. 오류가 있으면 `error_summary` 포함.
- **문서:** `docs/archive/MATH_REASONING_LEVEL_AND_IMPROVEMENTS.md`에 "표 업데이트 방법" 및 `results/gradient_report_*.json` 참고 안내 추가.
- **SHA 기반 재현성:** 평가 결과·gradient report에 `run_revision`(sha, short_sha, dirty, ref) 포함. 아티팩트/파일 이름에 SHA 사용 가능.
- **외부 컴퓨팅:** `eval-on-release` 워크플로(태그 `eval/`* 또는 수동 실행)로 평가 후 SHA-keyed 아티팩트 업로드. `OMI_REMOTE_INFERENCE_URL` 설정 시 추론만 원격 API로 전환. 자세한 옵션은 `docs/finetuning-resources/EXTERNAL_COMPUTE_OPTIONS.md`.

---

## 즉시 (이번에 할 수 있는 것)


| 순서  | 할 일                  | 방법                                                                                                                                                                                    |
| --- | -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | **벤치마크 숫자 채우기**      | `OMI_MODEL=Qwen/Qwen2-1.5B-Instruct` 등 설정 후 **AIME 90문** 또는 **Numina 60문** 한 번 끝까지 실행 → `results/`에 저장.                                                                               |
| 2   | **결과를 그라디언트에 넣기**    | 실행 후 `metrics.calculate_metrics()`로 나온 dict를 `evaluate_mathematical_and_devops(metrics)`에 넣어 수학/DevOps 그라디언트·난이도 트렌드 리포트 생성.                                                          |
| 3   | **문서 한 줄 업데이트 (P6)** | 평가 완료 후 `python scripts/update_math_level_from_results.py results/numina_balanced_results.json` 실행 → 출력 문장을 `docs/archive/MATH_REASONING_LEVEL_AND_IMPROVEMENTS.md`의 "현재 수준" 표에 붙여넣기. |


→ **목표:** "현재 수학적 추론 수준"을 숫자로 고정. 자세한 개선 순서는 `docs/archive/IMPROVEMENTS_P0_TO_P6.md` 참고.

---

## 단기 (1–2주)


| 순서  | 할 일             | 참고                                                                                          |
| --- | --------------- | ------------------------------------------------------------------------------------------- |
| 4   | **CI 추가**       | `.github/workflows/ci.yml` – lint, `pytest tests/`, (선택) Docker 빌드. DevOps 그라디언트 D3 확실히 충족. |
| 5   | **실행 메모리 조정**   | 코드 실행이 자주 터지면 `AIMO_EXECUTOR_MEMORY_MB=3072` 등으로 상향 후 재평가 (기본 2048MB).                      |
| 6   | **오류 분류 활용**    | 평가 결과의 `error`/메서드별 실패를 syntax·runtime·timeout·wrong_answer 등으로 분류 → 어떤 개선이 효과 큰지 파악.       |
| 7   | **검증 정확도 90%+** | P0 목표 유지. 간단 대수/산술 검증·거부 정확도 측정 후, SymPy·역검증 보강.                                            |


---

## 중기 (1–2달)


| 순서  | 할 일                      | 참고                                                                                           |
| --- | ------------------------ | -------------------------------------------------------------------------------------------- |
| 8   | **난이도 점수 연동**            | `DifficultyMetrics`(reasoning_steps, concept_count 등)를 평가 스크립트에 넣어 **정량적 난이도 vs 정확도** 곡선 분석. |
| 9   | **도메인별 정확도**             | 정수론/기하/대수/조합 등으로 나눠 집계 → 약한 도메인 집중 개선.                                                       |
| 10  | **Theoretician/기하 강화**   | N이 큰 문제·기하 문제에서 SymPy/기하 전용 경로 비중·성공률 올리기.                                                   |
| 11  | **Self-Consistency·앙상블** | 동일 문제에 여러 전략·시드로 풀고 일치하는 답 선택 → 단일 전략 대비 +1~3% 목표.                                           |


---

## 장기 (로드맵)

- **수학 그라디언트 L5:** 도메인별 정확도·정량적 난이도·rigor_report 자동화.
- **DevOps D4/D5:** 헬스체크·로깅/메트릭 정책 문서화 및 (선택) export.
- **증명(proof) 경로:** proof 타입 전용 프롬프트·후처리 실험.

---

## 참고 문서

- 수학 수준·개선: `docs/archive/MATH_REASONING_LEVEL_AND_IMPROVEMENTS.md`
- 평가·그라디언트: `docs/archive/PROJECT_EVALUATION_WITH_GRADIENTS.md`
- 실행 환경: `docs/run-eval/RUN_EVALUATION_ENVIRONMENT.md`

