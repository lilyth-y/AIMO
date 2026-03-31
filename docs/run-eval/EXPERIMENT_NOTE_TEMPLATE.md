# 실험 노트 템플릿 (Phase 0 — 측정 계약)

모든 정확도·형식 실험은 아래 **5줄**을 결과 JSON/PR/노트 상단에 복사해 채운다.  
한 실험에서 **변경하는 변수는 하나** ([FORMAT_AND_ACCURACY_PLAN.md](../vertex/FORMAT_AND_ACCURACY_PLAN.md)).

## 필수 필드 (복사용)

```
Path: A | B   # 권장: 클라우드만 — A = run_numina(Vertex) 또는 동일 축 Baseline Job | B_only = eval_vertex_endpoint_quality. 로컬 HF(arm_a/arm_b)는 선택.
Data: <파일명>  n=<N>  seed=<S>
Commit: <git short_sha>  (또는 결과 JSON 의 run_revision.short_sha)
Primary_metric: <예: summary.accuracy % | accuracy fraction + strict_format_rate>
Gate: <없음 | ralph_accuracy_gate | ralph_vertex_accuracy_gate | STEP2 --enforce-gates>
Strat_target: <overall | easy-only | medium-cap | 문서화된 정책>
```

## 예시 (채워짐)

```
Path: A
Data: numina_eval_balanced.json  n=10  seed=42
Commit: a1b2c3d
Primary_metric: summary.accuracy (%) + by_difficulty
Gate: ralph_accuracy_gate (AIMO_RALPH_TARGET_ACCURACY_PCT=80)
Strat_target: by_difficulty primary; overall 80% secondary
```

## 관련

- 상세 계획: [ACCURACY_ANALYSIS_AND_PLAN.md](ACCURACY_ANALYSIS_AND_PLAN.md)
- Arm A/B: [../experiments/ARM_AB_PROTOCOL.md](../experiments/ARM_AB_PROTOCOL.md)
