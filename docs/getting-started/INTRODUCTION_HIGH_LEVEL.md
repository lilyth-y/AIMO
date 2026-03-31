# AIMO 프로젝트 소개 (하이 레벨)


---

## 1. 프로젝트 정체

- **이름**: AIMO (OMI: Orchestrated Math Interpreter). MathCodeOrchestrator 계열 대회/평가용 파이프라인.
- **역할**: 수학 문제(텍스트) → **오케스트레이션** → 코드 생성·실행·검증 → **구조화된 답** (예: `\boxed{...}`).
- **핵심 차별점**: 단일 프롬프트 호출이 아니라 **5-Stage Pipeline**, **Fast Fail & Fallback**, **RefineLoop**로 전략·검증을 분리하고, 실패 시 재시도/대체 경로를 택함.

---

## 2. 아키텍처 요약

```
Input: problem_text (str)
  → Stage1: Labeling / Semantic Decomposition (domain, variables)
  → Stage2: Domain Experts Retrieval
  → Stage3: Calculation Router (Simulator / Theoretician / Hybrid)
  → Stage4: Code Execution (sandbox, resource limits)
  → Stage5: Verification (answer extraction, reconciliation)
  → Output: { answer, method, execution_result, error? }
```

- **RefineLoop**: Stage5 검증 실패 시, 오류 유형에 맞는 refine 프롬프트로 재생성 후 Stage3 이후 재실행 (상한 반복 횟수 있음).
- **Fallback**: Hybrid → Hierarchical Decomposer 등 대체 경로.

---

## 3. 기술 스택

| 계층 | 기술 |
|------|------|
| **언어/런타임** | Python 3.x |
| **LLM** | HuggingFace Transformers (Qwen2.5-Math 등), 4/8-bit 양자화(optional), PEFT(LoRA) 지원 |
| **평가/메트릭** | 자체 `EvaluationMetrics`, SymPy 기반 답 등가 검사, 난이도/소스/메서드별 집계 |
| **데이터** | NuminaMath-1.5 (HF), 로컬 `numina_eval_balanced.json`, AIME 검증셋 등 |
| **실행** | 제한된 서브프로세스에서 코드 실행 (CPU/메모리/시간 제한) |
| **배포/평가** | Kaggle Gateway (gRPC), Docker, (선택) 원격 추론 API |
| **시각화** | Vite+React 대시보드, Recharts, KaTeX (수식), Mermaid (다이어그램) |

---

## 4. 데이터·평가

- **평가셋**: Numina 60문항(균형), AIME 90문항 등. 형식: `problem`, `solution`, `answer`, `source`/`question_type` 등.
- **메트릭**: 정확도(전체/난이도/소스/메서드별), 평균 해결 시간, 에러 수. 결과는 `results/*.json` (summary + per-item results).
- **정답 검증**: `normalize_answer` + SymPy 등가(symbolic) 옵션.

---

## 5. 파인튜닝 전략

- **방식**: QLoRA (4-bit Qwen2.5-Math-1.5B + LoRA). NuminaMath-1.5 또는 자체 JSONL로 SFT.
- **입력 형식**: Chat 템플릿 (system: 단계별 추론 + `\boxed{}` 요구, user: problem, assistant: solution + boxed answer).
- **목표**: MathCodeOrchestrator 스타일(코드 생성 → 실행 → 검증) 및 출력 형식에 맞는 추론 습관을 강화.
- **실행**: `notebooks/train_qlora.ipynb` / `train_qlora.py`. Kaggle T4 16GB / Colab / 로컬 16GB GPU 권장.

---

## 6. 프로젝트 구조 (핵심만)

- **진입**: `src/pipeline/interface.py` (Kaggle) → `orchestrator.solve_problem()`.
- **파이프라인**: `src/pipeline/orchestrator.py` + `stage1_*` … `stage5_*`, `solver.py`, `refine_loop.py`, `reconciliation.py`.
- **평가**: `src/evaluation/evaluation_utils.py`, `config.py`; 실행 스크립트 `examples/run_numina_evaluation.py` 등.
- **데이터 로드**: `src/data/numina_loader.py`.
- **대시보드**: `dashboard/` (SPA), 정확도·풀이 과정·문제/수식 뷰어.

상세 디렉터리·실행 순서는 [docs/structure/PROJECT_STRUCTURE_AND_ORDER.md](../structure/PROJECT_STRUCTURE_AND_ORDER.md) 참고.

---

## 7. 확장·운영 포인트

- **모델**: 환경 변수로 모델/양자화 선택. 파인튜닝 어댑터 경로 연동 시 동일 인터페이스로 교체 가능.
- **리소스**: 실행 단계(Stage4) CPU/메모리/시간 제한 있음. GPU는 추론·파인튜닝 시 필요.
- **CI/평가**: GitHub Actions로 테스트; GPU 또는 원격 추론 URL로 평가 자동화 가능 (`EXTERNAL_COMPUTE_OPTIONS.md`).

이 문서는 기술 의사결정·온보딩·리뷰용 하이레벨 레퍼런스로 사용하면 됩니다.
