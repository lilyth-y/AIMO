# 연구 도구 적용 시 구조 안전성 확인

“적용했을 때 문제없는 구조인지”를 **배포 전에** 다음 순서로 본다.

## 1. 자동 점검 (권장)

레포 루트에서:

```powershell
cd C:\startingup\AIMO
python scripts/research/verify_research_structure.py
```

- `eval_hf_local_quality.py` · 비교기 · Arm A/B 래퍼 **파일 존재**
- `compare_research_arms.py` **최소 JSONL로 1회 실행**
- (가능하면) `PipelineOrchestrator` **import** — 풀 파이프라인 배치(Arm B) 추가 시 같은 진입점

종료 코드 **0**이면 도구 골격은 정상.

## 2. Arm A (Baseline-LLM) 적용 시

| 점검 | 내용 |
|------|------|
| 경로 | `scripts/eval_hf_local_quality.py` 가 루트 기준으로 호출됨 (`run_arm_a_baseline_eval`의 `cwd`) |
| 짝 비교 | Arm A/B 비교 시 **동일 `--seed`**, **동일 `--data-file`**, **동일 `--n-problems`** → `problem_id` 풀 일치 |
| GPU | 7B는 VRAM 요구 — 부족 시 `AIMO_RESEARCH_MODEL` 또는 `--device cpu` |

## 3. Arm B (풀 파이프라인) 추가 시 — 스키마 정합

`compare_research_arms.py`는 각 줄에 최소:

- `problem_id` (int, Numina 줄 인덱스와 동일하게 쓰는 것이 Arm A와 맞추기 쉬움)
- `is_correct` (bool)

선택: `strict_format_ok` (Arm A와 동일하게 쓰려면 오케스트레이터 출력에서 `<ANS>` 검증 결과를 넣을 수 있음)

`orchestrator.solve_problem` 반환에는 보통 `answer`, `extracted_answer`, `verified` 등이 있다.  
**정답 비교**는 `evaluation.evaluation_utils.check_answer_correctness(reference_answer, predicted_str)` 로 Arm A와 **동일 함수**를 쓰면 구조적으로 안전하다.

## 4. 알려진 한계

- **Vertex `eval_vertex_endpoint_quality` JSONL**에는 `strict_format_ok`가 없을 수 있음 → 비교기에서 strict 블록은 생략 메시지.
- **Arm B** (`run_arm_b_full_pipeline_eval.py`): `strict_format_ok`는 **`last_reasoning` 텍스트**에 대한 `validate_ans_strict` — Arm A(생성 연속 구간)와 정의가 약간 다를 수 있음. 정확도 비교는 `is_correct`가 동일 축.

## 5. 관련 문서

- [RESEARCH_EXPERIMENT_PROTOCOL.md](./RESEARCH_EXPERIMENT_PROTOCOL.md)
- [scripts/research/README.md](../../scripts/research/README.md)
