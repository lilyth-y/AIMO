# 연구 실험 설계: 구조 안전성·정확성·추론 (귀무가설 검정)

**목적**: 이 파이프라인이 **구조 안전성**, **정확성**, **추론(유용한 행동)** 측면에서 **효과가 있는가·얼마나**인지 검증한다.  
**귀무가설 (H0)**: 파이프라인(또는 그 구성 요소)을 켠 것과 끈 것 사이에 **체계적인 차이가 없다** (지표·설정에서 정의한 의미로).  
**대립가설 (H1)**: 정의한 최소 효과 크기(MES) 이상의 차이가 있다.

이 문서는 **실험 설계**만 담는다. 결과 해석은 별도.

---

## 1. 요인 정리 (무엇을 바꿀 것인가)

| 층 | 내용 | 실험에서의 위치 |
|----|------|-----------------|
| **L1 추론 백엔드** | 동일/다른 머지 가중치, 동일 `serve` 이미지 | **Vertex Endpoint** (재현 가능한 추론) |
| **L2 클라이언트 경로** | 풀 오케스트레이터 vs LLM 직접 호출 vs 부분 ablation | **실험 하네스** (로컬·게이트웨이·스크립트) |
| **L3 평가** | 동일 문제집·동일 채점기 | `eval_*`, `AnswerExtractor`, `check_answer_correctness`, `ans_format_guard` |

**핵심**: Vertex는 **L1을 공정하게 고정/분기**하기 좋다. **L2(중간 파이프 on/off)**는 보통 **Vertex 밖**에서 분기한다.

---

## 2. 실험 팔(arms) — 최소 설계

동일 **평가 문제집** $\mathcal{D}$ (고정 시드, 난이도·출처 스트라티파이 권장).

| Arm | L1 (Vertex) | L2 (클라이언트) | 해석 |
|-----|-------------|-----------------|------|
| **A — Baseline-LLM** | 엔드포인트 `E0` (동일 머지 $M$) | **프롬프트만** 문제→텍스트, 오케스트레이터 **미사용** | “모델 단독” |
| **B — Full-Pipeline** | 동일 `E0` ($M$ 동일) | **풀 파이프라인** (`solve_problem` 등) | “시스템 전체” |
| **C — Ablation (선택)** | 동일 `E0` | 풀 파이프에서 **한 모듈만 off** (예: 라우터 고정, 분해 off) | 원인 국소화 |

**통제**: $M$·`E0`·요청 타임아웃·`max_tokens`·온도(쓰는 경우)·$\mathcal{D}$·채점 버전은 **Arm 간 동일**하게 맞춘다.

**H0 (팔별)**: A vs B (및 C)에서 **사전 정의한 1차 지표**에 **유의미한 차이가 없다**.

---

## 3. 지표 (사전 등록 권장)

### 3.1 1차 (필수로 하나 이상 명시)

| 구분 | 예시 지표 | 비고 |
|------|-----------|------|
| **정확성** | $\mathcal{D}$에서 정답 일치율 (macro / by-difficulty) | `check_answer_correctness` |
| **형식·구조 안전** | `strict_format_compliance` 또는 검증 통과율 | 생성이 규칙을 지키는지 |
| **비용** | 문제당 평균 지연, 실패율 | 운영 관점 |

### 3.2 2차

- `ans_tag_compliance` (느슨), `predicted_nonnull`
- 난이도·출처별 분해 표
- (가능하면) 추론 품질 프록시: 구조화 블록 사용 여부, 코드 실행 성공 여부 등 **로그에서 자동 집계 가능한 것만**

### 3.3 최소 효과·표본

- **MES**: 예) 정확도 **+5%p** 이상, 또는 형식 준수율 **+10%p** 이상 — **연구 시작 전에 숫자 고정**
- **$|\mathcal{D}|$**: MES를 잡을 수 있게 **사전**에 표본 수 결정 (간단히는 파일럿으로 분산 추정)

---

## 4. Vertex 실험 배치

### 4.1 모델 A vs 모델 B (가중치 비교)

- **엔드포인트 2개**: `E_A`, `E_B` (다른 `artifact_uri`, 동일 머신·이미지·리전)
- 클라이언트는 **동일 L2**로 두 엔드포인트만 바꿔 호출

### 4.2 “같은 모델 2번” (재현성 체크)

- 동일 `E0`, 동일 요청, **시드·결정성** 가능한 부분 고정 → 노이즈 상한 추정

### 4.3 파이프 on/off (핵심)

- **Vertex는 동일** (`E0` 고정)
- **스위치는 L2**:
  - **Off**: HTTP로 `prompt`만 보내 생성문만 받아 채점 (Baseline-LLM)
  - **On**: 기존 `solve_problem` 경로로 최종 답·로그 수집 (Full-Pipeline)

→ “Vertex 2개”가 아니라 **호출 경로 2개**가 대조의 본체다.

---

## 5. 절차 (체크리스트)

1. **$\mathcal{D}$** 고정: JSONL + 버전 해시 기록  
2. **채점기·스크립트** 커밋 SHA 기록  
3. **Vertex**: `E0` 배포, 엔드포인트 ID·리전·머신 타입 문서화  
4. **Arm A**: L2=직접 호출 배치 실행 → 결과 JSONL  
5. **Arm B**: L2=풀 파이프 배치 실행 → 결과 JSONL  
6. **동일 순서·동일 재시도 정책** (형식 게이트 켜짐/끔도 Arm 간 동일하게)  
7. **집계 스크립트**로 1차 지표 계산 (수작업 최소화)  
8. **민감도**: 난이도 한 단계 바꿔 재실행 (선택)

---

## 6. 한계 (솔직히)

- **인과**: “파이프라인”은 여러 모듈의 합 — **C arm ablation** 없이 B만으로는 **어느 모듈이 이득인지** 단정 어렵다.  
- **외적 타당도**: $\mathcal{D}$가 좁으면 일반화 주장 제한.  
- **Vertex**: 추론 환경 통제에 유리하지만, **전체 시스템 효과**는 **L2 설계**가 지배한다.

---

## 7. 관련 문서

- 평가 도구: [EVAL_REAL_MODEL.md](./EVAL_REAL_MODEL.md), [QUALITY_EXPERIMENT.md](./QUALITY_EXPERIMENT.md)  
- 구조 논의: [../MATH_SOLVING_ARCHITECTURE_EVALUATION.md](../MATH_SOLVING_ARCHITECTURE_EVALUATION.md)  
- Vertex 동기: [WHY_THIS_VERTEX_STACK.md](./WHY_THIS_VERTEX_STACK.md)  
- **적용 전 구조 점검**: [RESEARCH_STRUCTURE_CHECK.md](./RESEARCH_STRUCTURE_CHECK.md)

---

## 8. 요약 한 줄

**Vertex로 L1을 고정하고, L2에서 “직접 LLM” vs “풀 파이프”를 나누며, 사전 등록한 지표·MES로 H0를 시험한다.**

---

## 9. 선정 모델·MES·실행 (본 연구 기본값)

### 9.1 추론 모델 (선정)

| 역할 | 모델 | 이유 |
|------|------|------|
| **본 실험 (권장)** | `Qwen/Qwen2.5-Math-7B-Instruct` | 수학·지시 준수 균형, 레포 Vertex 학습 예시와 동일 패밀리, 1.5B보다 대조 실험에서 신호가 나오기 쉬움 |
| **파일럿·저VRAM** | `Qwen/Qwen2.5-Math-1.5B-Instruct` | 스크립트·파이프만 검증할 때 |
| **튜닝·배포 후** | GCS `merged/` (동일 Qwen 계열 머지) | L1 고정 시 `E0` 아티팩트로 통일 |

베이스 HF ID는 **Arm A 로컬**·**Vertex `serve`가 받는 베이스**를 맞추면 대조가 깔끔하다.

### 9.2 사전 등록 MES·표본 (예시 — 팀에서 확정)

| 항목 | 예시 값 |
|------|---------|
| **MES (정확도)** | Arm B − Arm A ≥ **5%p** (macro accuracy) |
| **MES (형식)** | `strict_format_compliance` 차이 ≥ **10%p** |
| **표본** | 파일럿 $n \geq 50$, 본 실험 $n \geq 100$ (문제당 동일 시드 풀) |

### 9.3 Arm A — Baseline-LLM (로컬, 즉시 실행 가능)

환경변수 `AIMO_RESEARCH_MODEL` 로 모델 변경 가능 (기본 7B).

```powershell
cd C:\startingup\AIMO
python scripts/research/run_arm_a_baseline_eval.py --n-problems 100 --seed 41
```

출력: `results/research/arm_a_baseline_<seed>_<n>p.jsonl` + stdout 요약.

**GPU**: 7B는 VRAM 여유 필요. 부족 시 `AIMO_RESEARCH_MODEL=Qwen/Qwen2.5-Math-1.5B-Instruct` 또는 `--device cpu` (느림).

### 9.4 Arm A — 동일 베이스라인을 Vertex에서 (L1)

엔드포인트 배포 후:

```powershell
python scripts/vertex/eval_vertex_endpoint_quality.py --endpoint-id <ID> --n-problems 100 --seed 41
```

프롬프트·채점은 로컬 `eval_hf_local_quality` 와 **동일 계열** (문서: [EVAL_REAL_MODEL.md](./EVAL_REAL_MODEL.md)).

### 9.5 Arm B — Full-Pipeline

```powershell
python scripts/research/run_arm_b_full_pipeline_eval.py --n-problems 20 --seed 41 --time-budget 120
```

- `eval_hf_local_quality` 와 **동일** `load_numina_jsonl_filtered` (동일 seed / data-file / n → `problem_id` 정합).
- 출력: `results/research/arm_b_full_<seed>_<n>p.jsonl`
- LLM·실행 환경이 필요하고 **시간이 김** — `n` 은 작게 시작.

구성이 없으면 스크립트가 실패할 수 있다(키·모델 경로 등). 그때는 로그·`error` 필드로 원인 확인.

### 9.6 비교

Arm A·B JSONL이 준비되면 (동일 `seed`·`data_file`·`n_problems` 권장):

```powershell
python scripts/research/compare_research_arms.py `
  --a results/research/arm_a_baseline_41_100p.jsonl `
  --b path/to/arm_b.jsonl `
  --label-a Baseline_LLM --label-b Full_Pipeline `
  --output-json results/research/compare_41.json
```

- `paired_contingency_is_correct`: 둘 다 틀림 / A만 맞음 / B만 맞음 / 둘 다 맞음 (McNemar 등 후속 통계용).
- `strict_format` 은 양쪽에 `strict_format_ok` 가 있을 때만 의미 있음.
