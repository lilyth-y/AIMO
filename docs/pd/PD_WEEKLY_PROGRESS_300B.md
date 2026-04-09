# PD 학기제 주차별 진행 요약 (각 절 약 300 byte, UTF-8)

> 각 `**진행:**` 블록(기간 줄 제외)은 UTF-8 기준 약 300바이트로 맞춤. 경로·용어는 저장소 실제 산출물과 대응.

---

## 1주차

**기간:** 3.2 – 3.8  

**진행:** 회의에서 수학 퍼즐을 풀어보자는 방향을 논의했다. `docs/AIMO3/Report.md`에 뉴로-심볼릭·AIMO3 전략을 정리하고 Plan & Code·5-Stage·역공학 데이터 개념을 확정했다. `docs/guides/HYBRID_REASONING_ARCHITECTURE.md`와 `docs/structure/PROJECT_STRUCTURE_AND_ORDER.md`로 하이브리드 추론과 모듈 순서를 문서화했다.

---

## 2주차

**기간:** 3.9 – 3.15  

**진행:** `requirements.txt`에 transformers·accelerate·torch·sympy·pytest 등을 두고 `requirements-kaggle.txt`·`requirements-vertex.txt`로 환경을 나눴다. `README.md`에 `OMI_MODEL`·양자화·설치·빠른 실행과 pip 설치 한 줄을 적어 로컬·Kaggle·Colab 재현 기반을 마련했다.

---

## 3주차

**기간:** 3.16 – 3.22  

**진행:** Qwen 로딩·토크나이저: `solver.py`의 `LocalLLMClient`가 lazy load·`BitsAndBytesConfig`를 쓴다. `model_config.py`에 프리셋·VRAM, `debug_tokenizer.py`로 점검, `pipeline/config.py`에 기본 HF 모델명을 둔다. 로컬 경로는 `local_files_only` 분기로 Windows 캐시 이슈를 줄였다.

---

## 4주차

**기간:** 3.23 – 3.29  

**진행:** 회의에서 정사각형 두 개가 겹친 구성에서 꼭짓점과 두 정사각형이 만나는 점만 node로 두고, node마다 수를 할당해 마방진을 만족시키는 퍼즐을 만들어 AI가 풀 수 있는지 시험하자는 제안이 나왔다. `stage4_execution.py`의 `CodeExecutor`: 제한 전역·`safe_import`·금지 내장·멀티프로세스 `exec`·stdout 캡처, SymPy·math 주입. `AIMO_EXECUTOR_MEMORY_MB` 등으로 메모리·CPU 한도를 조정한다. 파일 상단 주석에 완전 격리 샌드박스는 별도라고 밝힌다.

---

## 5주차

**기간:** 3.30 – 4.5  

**진행:** `reasoning_utils.py`의 `STRUCTURE_TAGS`·`assess_complexity`·`build_structured_prompt`로 구조화 프롬프트·복잡도 휴리스틱을 제공한다. Solver·Orchestrator와 연결해 코드 출력을 유도하고 `orchestrator_helpers.py` 수정 프롬프트로 실패 시 재작성 힌트를 준다.

---

## 6주차

**기간:** 4.6 – 4.12  

**진행:** `solver.py`에서 `BitsAndBytesConfig`·환경 변수 `OMI_MODEL`·`MATHCODEORCHESTRATOR_QUANTIZATION`으로 4bit 등 양자화 로딩을 지원한다. `model_config.py`에 모델별 권장 양자화를 명시했고, `notebooks/train_qlora.ipynb`·`train_qlora.py`로 선택적 QLoRA 실험 경로를 둔다.

---

## 7주차

**기간:** 4.13 – 4.19  

**진행:** `src/pipeline/orchestrator.py`의 `PipelineOrchestrator`가 Stage1–5·Router·Bandit·Multi-agent 등을 묶어 생성→실행→검증을 통합한다. `interface.py`로 외부 진입, `src/evaluate_local.py`가 `data/eval_data.jsonl` 등으로 소규모 로컬 평가 예시를 제공한다.

---

## 8주차

**기간:** 4.20 – 4.26  

**진행:** 중간 시연용으로 `dashboard/`에 Vite+React 대시보드를 두고 Accuracy·Overview·ProblemViewer 등 페이지를 연결했다. `README.md`·`docs/README.md`로 개요·문서 인덱스를 정리하고 `public/` 정적 자산으로 발표 시연·리포 안내를 함께 갖췄다.

---

## 9주차

**기간:** 4.27 – 5.3  

**진행:** `src/pipeline/refine_loop.py`의 `RefineLoop`·`refine_attempt`로 검증 실패 시 재생성 루프를 구현했다. `reconciliation.py`가 추론·실행 정합을 맞추고, `verification_enhancements.py`·`stage5_verification.py`의 검증 라우터와 `build_refine_prompt`가 연동된다.

---

## 10주차

**기간:** 5.4 – 5.12  

**진행:** `data/`에 eval·Numina·finetune JSONL·`eval/trusted_subset_seed.jsonl` 등을 두고 `scripts/setup_numina_dataset.py`·`src/data/numina_loader.py`로 로드한다. `scripts/vertex/prepare_qwen_numeric_dataset*.py`가 Hugging Face·로컬 원본에서 학습용 JSONL을 생성한다.

---

## 11주차

**기간:** 5.13 – 5.17  

**진행:** `examples/run_numina_evaluation.py`·`run_aime_evaluation.py`·`quick_eval.py`로 end-to-end 평가를 돌린다. `src/evaluation/`의 run_evaluation·eval_grading·comprehensive_reporting과 `scripts/analyze_logs.py`·`scripts/research/compare_research_arms.py`로 Success/Fail·arm 비교 로그를 남긴다.

---

## 12주차

**기간:** 5.18 – 5.24  

**진행:** `stage4_execution.py`에서 wall time·`psutil`·정적 금지 패턴으로 Timeout·CPU·메모리 이슈를 완화한다. `src/pipeline/exceptions.py`로 예외를 정리해 무한 루프·위험 코드에 대한 방어선을 강화하고 최종 벤치 직전 안정성을 높인다.

---

## 13주차

**기간:** 5.25 – 5.31  

**진행:** `examples/ab_eval_1000.py` 등으로 비교 실험을 돌리고 `scripts/vertex/eval_vertex_endpoint_quality.py`·`eval_hf_local_quality.py`로 엔드포인트·로컬 품질을 평가한다. `results/*.jsonl`에 기록해 프롬프트 단독 대비 오케스트레이터의 정답률 차이를 수치화한다.

---

## 14주차

**기간:** 6.1 – 6.7  

**진행:** `docs/CLEANUP_2026.md`·`docs/structure/PROJECT_STRUCTURE_AND_ORDER.md`로 정리·구조를 문서화하고 `.github/workflows`로 CI를 둔다. `scripts/organize_pd_project.py`로 리포 가독성·제3자 재현 경로를 맞추고, `docs/README.md` 인덱스와 폴더 규칙을 일치시켰다.

---

## 15주차

**기간:** 6.8 – 6.14  

**진행:** 최종 보고서 근거로 `docs/eval/EVALUATION_AND_GRADING_CHRONICLE.md`·`docs/run-eval/` 가이드, `docs/vertex/AGENTIC_AI_VERTEX_IMPLEMENTATION_PLAN.md`, 루트 `SOLVER_STRATEGY_EVIDENCE.md`를 둔다. 실험 이력·한계·Vertex 보완 방향을 한곳에서 인용할 수 있다.

---

## 검증

아래 명령으로 각 주차 `**진행:`** 단락의 UTF-8 바이트 수를 확인할 수 있다.

```bash
python -c "
import re, pathlib
text = pathlib.Path('docs/pd/PD_WEEKLY_PROGRESS_300B.md').read_text(encoding='utf-8')
for m in re.finditer(r'\*\*진행:\*\* (.*?)(?=\n\n---|\n## |\Z)', text, re.S):
    body = m.group(1).strip()
    print(len(body.encode('utf-8')), body[:60]+'...')
"
```

(경로는 저장소 루트에서 실행 기준)