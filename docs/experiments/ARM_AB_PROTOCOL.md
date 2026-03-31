# Arm A vs B — 동일 $\mathcal{D}$·seed·채점기

[RESEARCH_EXPERIMENT_PROTOCOL.md](../vertex/RESEARCH_EXPERIMENT_PROTOCOL.md)의 최소 대조.  
**L1(모델·엔드포인트)은 동일**하게 두고, **L2만** Baseline vs Full-Pipeline으로 나눈다.

---

## 권장: 클라우드만 (로컬에서 모델 로드·추론 없음)

**기본 전제**: HF 모델을 로컬에 올리지 않고, **추론은 GCP/Vertex(또는 동일 클라우드 환경)에서만** 돌린다.

| Arm | 의미 | 어디서 |
|-----|------|--------|
| **A — Baseline** | 동일 모델/엔드포인트로 **단발·최소 프롬프트** 생성 후 `check_answer_correctness` 계열 채점 (오케스트레이터·풀 파이프라인 미사용) | Vertex **Custom Job**, Cloud Shell, GCE 노트북 등 — Job 제출·요약은 [RALPH_VERTEX.md](../run-eval/RALPH_VERTEX.md), [scripts/vertex/submit_vertex_eval_job.py](../../scripts/vertex/submit_vertex_eval_job.py) |
| **B — Full** | `solve_problem` 또는 **동일 엔드포인트 + 현재 파이프라인** | [examples/run_numina_evaluation.py](../../examples/run_numina_evaluation.py) (오케스트레이터 + Vertex Gemini) 또는 배포 Job에서 동일 엔트리포인트 |

**고정**: 동일 $\mathcal{D}$, 동일 seed, 동일 채점기. Path A(Numina+Gemini)와 Path B(엔드포인트 전용 eval)의 **숫자는 서로 직접 비교하지 않는다** — Arm A/B는 **같은 평가 축·같은 스크립트** 안에서만 비교한다.

**참고 문서**

- 인증: [GCP_AUTH.md](../vertex/GCP_AUTH.md)
- 대형·디스크 제약: [CLOUD_NUMINA_RUN.md](../run-eval/CLOUD_NUMINA_RUN.md)
- 엔드포인트만: [scripts/vertex/eval_vertex_endpoint_quality.py](../../scripts/vertex/eval_vertex_endpoint_quality.py)
- Job 후 게이트: [scripts/vertex/ralph_vertex_accuracy_gate.py](../../scripts/vertex/ralph_vertex_accuracy_gate.py)

Baseline(A)용 “짧은 단발” 스크립트는 레포에 **고정된 단일 엔트리**가 없을 수 있으므로, 실험마다 **Job 커맨드·환경변수**를 실험 노트에 붙여 재현 가능하게 남긴다.

---

## 로컬 HF (선택 — GPU·대용량 디스크 있을 때만)

아래는 **로컬에서 Hugging Face 모델을 로드할 수 있을 때**의 참고용이다. 클라우드만 쓰는 경우 **이 절은 건너뛴다**.

### Arm A — Baseline-LLM

- **스크립트**: [scripts/research/run_arm_a_baseline_eval.py](../../scripts/research/run_arm_a_baseline_eval.py)
- **실질**: [scripts/eval_hf_local_quality.py](../../scripts/eval_hf_local_quality.py) 고정 인자 호출

```powershell
cd C:\startingup\AIMO
python scripts/research/run_arm_a_baseline_eval.py --n-problems 50 --seed 41
```

### Arm B — Full-Pipeline (`solve_problem`)

- **스크립트**: [scripts/research/run_arm_b_full_pipeline_eval.py](../../scripts/research/run_arm_b_full_pipeline_eval.py)
- **동일 문제 풀**: `eval_hf_local_quality` 의 `load_numina_jsonl_filtered` 와 **동일 `seed`, `data-file`, `n-problems`**

```powershell
python scripts/research/run_arm_b_full_pipeline_eval.py --n-problems 50 --seed 41 --data-file numina_training_5k.jsonl --time-budget 120
```

`--data-file` 은 Arm A와 **동일**해야 한다.

---

## 성공 기준 (MES — 사전 등록)

파이프라인 튜닝·구조 변경을 본격화하기 전에, 동일 $\mathcal{D}$·seed에서 **Arm B가 Arm A 대비** 목표 지표(예: 정확도) **+5%p 이상**인지 등 **실험 전에 한 줄로 등록**한다. MES 미만이면 우선 L1(모델·엔드포인트)·데이터·채점 정의를 재검토한다.

## 실험 노트

실행마다 [EXPERIMENT_NOTE_TEMPLATE.md](../run-eval/EXPERIMENT_NOTE_TEMPLATE.md) 5줄을 채운다. 클라우드 Job이면 **실행 환경(프로젝트·리전·Job ID)** 을 노트에 추가해 둔다.
