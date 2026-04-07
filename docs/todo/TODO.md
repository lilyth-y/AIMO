# Moai Roadmap / TODO (Prioritized)

## 2026-04-07 실험 기반 TODO (capacity / latency / 429)

- [ ] **P0** `cap=14` 재검증: 동일 3문항/동일 설정에서 외부 네트워크 영향 분리
- [ ] **P0** 첫 429 감지 후 high-cost fallback(multi-agent) 강제 차단 회귀 테스트 추가
- [ ] **P1** `cap=10` 고정 region 비교 확장(`us-east5`, `us-central1`) 및 시간대별 재현성 측정
- [ ] **P1** quota 신청 템플릿에 `429`, `timeout`, `avg/p90 latency`, `problem당 LLM 호출수`를 필수 필드화

Legend:
- P0: Immediate impact / unblock correctness & data quality
- P1: High impact next layer (robustness & learning)
- P2: Enhancement / scaling / research features
- P3: Nice-to-have / polish

## P0 (Core Correctness & Safety)
1. Advanced Verification Module
   - Extend `VerificationRouter` to handle: rational simplification, symbolic equality (sympy.simplify), numeric tolerance for floats, list/set multiset comparison, expression normalization (factor/expand). 
   - Add context-driven reverse checks (e.g., re-substitute solution into original equation template stored in context).
   - Acceptance: >90% of simple algebra/arithmetic problems verified or rejected correctly in a held-out mini-set.
2. Reasoning-Answer Reconciliation
   - Compare `<ANS>` extracted value with execution result; if mismatch classify (format vs logic vs arithmetic). 
   - Canonicalize both via sympy before compare.
   - Acceptance: Mismatch taxonomy logged; false mismatches reduced after canonicalization.
3. Self-Refine Loop (Single Retry)
   - On verification fail or mismatch: generate a targeted refine prompt (include error category + previous reasoning). 
   - Limit to 1 retry per strategy; log both attempts.
   - Acceptance: At least 10–20% recovery on synthetic failure cases.
4. Execution Resource Limits
   - Add CPU time & memory watchdog (psutil) around subprocess; kill if over thresholds. 
   - Expand forbidden patterns (file/network/process creation). 
   - Acceptance: Infinite loops consistently terminated; memory spikes contained.

## P1 (Learning & Strategy Optimization)
5. Strategy Selection Features
   - Build feature extractor: length, complexity_score, keyword counts (geometry/number theory/probability), operator diversity, past success rate buckets.
   - Feed to simple bandit (epsilon-greedy) or logistic classifier to choose initial strategy ordering.
   - Acceptance: Offline replay shows improved first-attempt verification rate vs static order.
6. Log Analytics Pipeline
   - Convert `logs/eval_log.jsonl` -> Parquet; create `analyze_logs.py` producing metrics (success by strategy, mismatch types, avg complexity).
   - Acceptance: Script runs <5s on 10k entries, outputs summary table.
7. Decomposition vs Direct Classifier
   - Collect dataset of problems labeled success/fail for hierarchical path. 
   - Train heuristic threshold or simple model; gate decomposition call.
   - Acceptance: Reduction in unnecessary decomposition invocations with equal or better accuracy.
8. Lemma / Pattern Cache
   - Hash normalized sympy expressions; store usage counts + success outcomes. 
   - Provide retrieval for new problems (e.g., reuse factorizations, combinatorial identities).
   - Acceptance: Cache hit ratio >10% after warm-up corpus.

## P2 (Quality & Ensemble Robustness)
9. Candidate Voting Ensemble
   - Generate multiple solutions (different strategies / temperature variations). 
   - Use sympy equivalence + frequency voting to select final answer.
   - Acceptance: Ensemble accuracy > single strategy baseline.
10. Multi-Step Self-Refine (Chain Repair)
    - Extend single retry to iterative plan editing: request corrected PLAN/DERIVATION blocks only.
    - Acceptance: Further 5–10% gain on hard labeled set.
11. Expression Distance Heuristics
    - Compute complexity of `simplify(candidate - expected)` / structural similarity score. 
    - Use to prioritize which failures warrant refine attempt.
12. Hybrid Numeric-Symbolic Validation
    - Random numeric substitution tests for symbolic equality when direct simplify inconclusive.
    - Acceptance: Reduce false negatives in verification by >50%.

## P3 (Platform & Polish)
13. Kaggle Packaging
    - Create `kaggle_runner.py` (CLI) with flags: --input_csv, --batch, --model_cache.
    - Add reproducibility doc: environment.yml / pip freeze -> requirements.
14. Performance Optimization
    - Batch multiple prompts when independent (micro-batching reasoning + code). 
    - Cache complexity scores and extracted features.
15. Documentation & Examples
    - Add README sections: architecture diagram, verification taxonomy, refinement flow.
16. Unit & Integration Tests
    - Pytest suites: verification parsing, sandbox timeout, refine path, feature extraction.
17. Security Hardening
    - Expand safe AST parsing; deny dynamic attribute access (`__getattr__`, `__class__` introspection). 
    - Add audit log for blocked patterns.

## Implementation Sequencing (Recommended)
Phase 1: (P0) 1→2→3→4
Phase 2: (P1) 5→6→7→8
Phase 3: (P2) 9→10→11→12
Phase 4: (P3) 13→14→15→16→17

## Tracking Template (log extension)
Add fields:
- refine_attempts, refine_success
- mismatch_type (format|logic|arithmetic|other)
- resource_usage (cpu_ms, mem_mb)
- strategy_decision_features (serialized dict)
- decomposition_used (bool)
- cache_hits (int)
- ensemble_size (int)

## Quick Acceptance Test Ideas
- Verification: curated 50-problem micro-set (arithmetic, algebra, geometry, number theory).
- Strategy bandit: offline replay simulation using stored outcomes.
- Self-refine: inject synthetic error (e.g., wrong coefficient) ensure correction path triggers.
- Sandbox: infinite loop & memory bloat script killed within limit.

## Notes
- Avoid overfitting early classifiers; start with heuristic + logging before ML training.
- Maintain deterministic fallback path for reproducibility in benchmarking.
- All new modules should degrade gracefully if dependencies (sympy, psutil) absent.
