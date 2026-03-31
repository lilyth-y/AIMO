# 형식 준수·정확도 동시 개선 계획

## 1. 원인 정리 (관측과 코드의 합치)

| 현상 | 의미 |
|------|------|
| `strict_format_ok` 전부 `False`, `NO_ANS_TAG` | 생성문에 `<ANS>...</ANS>`가 없음. `validate_ans_strict`는 이 태그만 본다. |
| 첫 프롬프트는 “설명 없이 태그만” | `build_prompt_strict_first` — 모델이 긴 풀이·LaTeX 습관을 따르면 게이트는 실패한다. |
| `graded_fallback` / `graded_fallback_verify_agent` | 형식 실패 후 `\\boxed{}` 추출 또는 검수(verify) 에이전트로 재채점된 경로. |
| 전체 정확도와 형식률은 별개 | 폴백이 살리면 정확도는 나오지만 **strict 형식률은 별도 지표**로 봐야 한다. |

**정리:** 정확도가 낮은 주된 이유는 (1) 풀이·최종값 오류, (2) 잘못된 박스 추출, (3) 검수 출력이 잘못된 경우 등. 형식 게이트 실패는 **지시 미준수**이지, 반드시 “평가 코드 버그”는 아니다.

## 2. 목표 지표 (동시에 추적)

| 지표 | 설명 |
|------|------|
| `strict_format_rate` | `strict_format_ok` 비율 — 엔드포인트가 **프롬프트 형식을 따르는지**. |
| `accuracy` | 최종 채점(폴백·검수 포함) — **실제 사용자가 보는 품질**에 가깝다. |
| `accuracy_by_strict_format_ok` | strict 통과/실패 각각의 정확도 — 형식 통과 시만 채점이 안정적인지 확인. |
| `accuracy_by_scoring_status` | 경로별 정확도 — `graded_fallback` vs `graded_fallback_verify_agent` 등. |
| `verify_agent_recovery_rate` | 검수 호출 대비 복구 성공 비율. |

`eval_vertex_endpoint_quality.py` 종료 시 JSON 요약과 `diagnose_vertex_eval_jsonl.py` 출력에 위 분해가 포함된다.

**게이트:** `docs/vertex/STEP2_QUALITY_GATES.md` + `--enforce-gates` — `strict_format_rate`·`accuracy`·null 비율·API 오류율 등 **동시 조건**을 쓴다.

## 3. 단계별 평가 (규칙: 한 실험당 변수 하나)

### 1단계 — 실행·지표 확인

- 로컬: `python -m py_compile scripts/vertex/eval_vertex_endpoint_quality.py`
- 동일 JSONL·동일 `--seed`로 재현 가능한지 확인
- `diagnose_vertex_eval_jsonl.py <jsonl>` 로 `accuracy_by_*` 확인

### 2단계 — 소규모에서 가설 검증

**고정:** `seed`, `n-problems`, `data-file`, `difficulty-at-most`, `endpoint-id`, `predict-timeout`  
**한 번에 하나만 바꿈** 예시:

| 실험 | 바꾸는 것 | 기대 |
|------|-----------|------|
| A | `--max-format-retries` (예: 3→5) | 형식 재시도로 `strict_format_rate` 소폭 개선 가능 |
| B | `--retry-temperature` | 재시도 다양성 vs 안정성 트레이드오프 |
| C | `--verify-max-new-tokens` | 검수가 긴 답을 정리할 때 필요할 수 있음 |
| D | `--last-resort-extraction` (on) | null 감소 vs 노이즈 유입 — 정확도만 보지 말고 `scoring_status`도 함께 봄 |
| 비교 전용 | `--no-format-gate` | **레거시 단발** vs 형식 파이프라인 — “모델 한계 vs 파이프라인” 분리 |

### 3단계 — 보고 가능한 규모

- `n-problems` ≥ 50 (STEP2 게이트 기준), 동일 프로토콜
- 결과는 JSONL + stdout 요약 + (선택) BigQuery `--bq-table`

## 4. 정확도·형식을 **동시에** 끌어올리는 방향 (우선순위)

1. **학습 데이터 / SFT:** `<ANS>` 단일 블록만 출력하는 예시를 넣는 파인튜닝 — 형식률에 직접적이다.  
2. **생성 파라미터:** `temperature=0` 유지, `max_format_retries`·`retry_temperature`는 2단계에서만 조정.  
3. **더 큰 모델 또는 수학 특화 체크포인트:** 추론 정확도 자체를 올린다.  
4. **검수 프롬프트·토큰:** verify 실패/부정확 시에만 `--verify-max-new-tokens` 등을 조정 (한 변수씩).  
5. **폴백 의존 축소:** `strict_format_rate`가 목표에 가깝다면 `graded_fallback` 비율을 낮추는 것이 목표와 일치.

## 5. 리스크

- **폴백만 늘리면** 정확도는 오를 수 있으나 **strict 형식률은 그대로**일 수 있다 — 목표는 둘 다 명시해야 한다.  
- **`--last-resort-extraction`** 은 null을 줄이지만 **오답**을 늘릴 수 있다.  
- **A/B 비교 시** `seed`/`문제 집합`이 다르면 결론이 섞인다 — 동일 seed로 고정한다.

## 6. 참고 명령

```bash
# 평가 후 요약에 accuracy_by_scoring_status 등 포함
python scripts/vertex/eval_vertex_endpoint_quality.py --endpoint-id ... --n-problems 20 ...

# 로컬 JSONL로 경로별 정확도
python scripts/vertex/diagnose_vertex_eval_jsonl.py results/vertex_eval_....jsonl
```
