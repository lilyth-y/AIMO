# 현재 결과 정리

**작성일:** 2026-02-23

---

## 1. 최근 Quick Eval 결과

| 항목 | 값 |
|------|-----|
| **데이터셋** | Quick_Eval (NuminaMath balanced 60문항 중 샘플) |
| **실행 시각** | 2026-02-23T12:29:23 |
| **총 문항 수** | 5 |
| **정답 수** | 0 |
| **오답 수** | 5 |
| **정확도** | **0%** |
| **평균 풀이 시간** | 약 162초 |
| **총 평가 시간** | 약 812초 |
| **에러 건수** | 0 |

### 난이도별

| 난이도 | 문항 수 | 정답 | 정확도 |
|--------|---------|------|--------|
| medium | 3 | 0 | 0% |
| hard   | 2 | 0 | 0% |

### 소스별

| 소스 | 문항 수 | 정답 | 정확도 |
|------|---------|------|--------|
| cn_k12    | 3 | 0 | 0% |
| olympiads | 2 | 0 | 0% |

### 방법별

| 방법 | 문항 수 | 정답 | 비고 |
|------|---------|------|------|
| Path A: The Simulator | 5 | 0 | 전부 동일 경로 |

### 문항별 요약

- **참조 답**: `\frac{1}{6}`, `302`, `\frac{5\sqrt{2}-2}{2}`, `proof`, `\frac{\sqrt{5}}{2}` 등
- **예측 답**: 5문항 모두 **32**로 추출됨 (답 추출은 짧은 값으로 정리됨, 단 실제 정답과는 불일치)

---

## 2. Gradient 리포트 (gradient_report_quick_eval.json)

| 영역 | 수준 | 설명 |
|------|------|------|
| **수학 (Mathematical)** | L2_Stratified | 난이도/소스별 분해 및 기본 통계 |
| **DevOps** | D5_Production | README, requirements, Docker, compose, CI, 테스트, entrypoint, 리소스 제한, 로깅 등 프로덕션 수준 |

---

## 3. 적용된 개선 사항 (P0 ~ P6)

| 구분 | 내용 | 상태 |
|------|------|------|
| **P0** | 모델/토크나이저 repo_id 통일 | ✅ |
| **P1a** | MULTI-AGENT 답 dict일 때 content에서 숫자 추출 | ✅ |
| **P1b** | 실행 환경 math/sympy, 프롬프트에 sympy 명시 | ✅ |
| **P2a** | 실행 전 AST 문법 검사 | ✅ |
| **P2b** | NameError/AttributeError/SyntaxError 시 수정 프롬프트 + 1회 재생성 | ✅ |
| **P3** | OpenTelemetry/TF oneDNN/torch_dtype 경고 억제 | ✅ |
| **P4** | MULTI-AGENT 로그 한글(cp949) 깨짐 방지 (ASCII 안전) | ✅ |
| **P5** | 실패 시 `EvaluationResult.error` 저장 → error_summary 분류 | ✅ |
| **P6** | 평가 결과로 문서 표 갱신 스크립트/가이드 | ✅ |

---

## 4. 최근 답 추출 강화 (2026-02-23)

| 항목 | 내용 |
|------|------|
| **문제** | 이전에 예측 답이 "ONLY compact canonical form." 또는 긴 대화/JSON이 그대로 저장되던 현상 |
| **조치** | `reasoning_utils.py`, `multi_agent_reasoner.py` 수정 |
| **변경 요약** | ① `<ANS>` 플레이스홀더 문구 거부 후 boxed/숫자 fallback ② 긴 문자열에서 `최종 답안:`, `결과값`, LaTeX `\frac`, 마지막 숫자만 추출 ③ Judge 응답이 대화 형태일 때 한 번 더 추출 |
| **검증** | `scripts/check_answer_extraction.py`로 placeholder 거부·정상 ANS·긴 텍스트 추출 동작 확인 |

**현재 동작:** 예측 답은 이제 **짧은 값**(예: 32)으로만 나오며, 긴 대화/JSON이 그대로 저장되지는 않음. 다만 **실제 정답과의 일치(정확도)** 는 아직 0%로, 풀이 품질/경로 선택 개선이 별도로 필요함.

---

## 5. 결과 파일 위치

| 파일 | 설명 |
|------|------|
| `results/quick_eval_results.json` | Quick Eval 상세 결과 (summary + results[]) |
| `results/gradient_report_quick_eval.json` | 수학/DevOps gradient 요약 |
| `docs/IMPROVEMENTS_P0_TO_P6.md` | P0~P6 개선 내역 |
| `docs/MATH_REASONING_LEVEL_AND_IMPROVEMENTS.md` | 수준 표 갱신 가이드 |

---

## 6. 다음에 할 수 있는 것

1. **정확도 향상**: Path A만 사용·동일 값(32) 반복 원인 분석(모델 출력, fallback 추출 위치 등).
2. **전체 평가**: `examples/run_numina_evaluation.py`로 60문항 전체 실행 후 표 갱신.
3. **표 갱신**: `python scripts/update_math_level_from_results.py results/numina_balanced_results.json` 실행 후 `docs/MATH_REASONING_LEVEL_AND_IMPROVEMENTS.md` 표 반영.
