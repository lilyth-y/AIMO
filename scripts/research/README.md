# 연구 실험 실행 스크립트

- [RESEARCH_EXPERIMENT_PROTOCOL.md](../../docs/vertex/RESEARCH_EXPERIMENT_PROTOCOL.md) §9 참고.
- 적용 전 구조 점검: [RESEARCH_STRUCTURE_CHECK.md](../../docs/vertex/RESEARCH_STRUCTURE_CHECK.md) · `python scripts/research/verify_research_structure.py`

| 스크립트 | Arm | 설명 |
|----------|-----|------|
| `run_arm_a_baseline_eval.py` | **A** | Baseline-LLM — `eval_hf_local_quality.py` 래퍼, `results/research/` 에 JSONL |
| `run_arm_b_full_pipeline_eval.py` | **B** | `PipelineOrchestrator.solve_problem` 배치, 동일 문제 풀·채점 |
| `compare_research_arms.py` | — | Arm A/B JSONL을 `problem_id` 로 짝지어 정확도·strict 차이·분할표 출력 |
| `verify_research_structure.py` | — | 경로·비교기·import 스모크 |

### Arm A → Arm B → 비교 (동일 seed/n)

```powershell
python scripts/research/run_arm_a_baseline_eval.py --n-problems 20 --seed 41
python scripts/research/run_arm_b_full_pipeline_eval.py --n-problems 20 --seed 41
python scripts/research/compare_research_arms.py `
  --a results/research/arm_a_baseline_41_20p.jsonl `
  --b results/research/arm_b_full_41_20p.jsonl `
  --label-a Baseline_LLM --label-b Full_Pipeline
```

Arm B는 **LLM·시간**이 많이 든다. `--n-problems` 는 작게 시작.
