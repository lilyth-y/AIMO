# MathCodeOrchestrator Model Selection & Fine-tuning Guide

## 사용 가능한 모델

환경 변수 `MathCodeOrchestrator_MODEL`로 모델 선택:

### 개발/테스트용
```powershell
$env:MathCodeOrchestrator_MODEL="qwen-0.5b"  # 0.5B, 빠른 테스트용
```

### 권장 모델 (RTX 4060 8GB)
```powershell
$env:MathCodeOrchestrator_MODEL="qwen-1.5b"  # 1.5B Coder (기본값, 권장)
$env:MathCodeOrchestrator_MODEL="qwen-math-1.5b"  # 1.5B Math-specialized
```

### 큰 모델 (4-bit quantization)
```powershell
$env:MathCodeOrchestrator_MODEL="qwen-7b"  # 7B Coder + 4-bit
$env:MathCodeOrchestrator_MODEL="qwen-math-7b"  # 7B Math + 4-bit
$env:MathCodeOrchestrator_MODEL="qwen-14b"  # 14B Coder + 4-bit (실험적)
```

## 실행 예시

### 1.5B 모델로 평가
```powershell
$env:MathCodeOrchestrator_MODEL="qwen-1.5b"
$env:CUDA_VISIBLE_DEVICES="0"
python run_aimo_evaluation.py
```

### 7B 수학 특화 모델
```powershell
$env:MathCodeOrchestrator_MODEL="qwen-math-7b"
$env:CUDA_VISIBLE_DEVICES="0"
python run_aimo_evaluation.py
```

## 필요한 패키지

### 4-bit/8-bit Quantization
```powershell
pip install bitsandbytes accelerate
```

### GPU 지원
```powershell
# CUDA 12.1 기준
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

## 파인튜닝 준비

### 1. 데이터셋 구조
```
data/
├── openmath_sample.jsonl       # OpenMathReasoning 샘플
├── numina_eval_balanced.json   # Numina 평가셋
└── finetune/
    ├── train.jsonl             # 학습 데이터
    ├── val.jsonl               # 검증 데이터
    └── README.md
```

### 2. 학습 데이터 형식 (JSONL)
```json
{"problem": "Solve x+2=5 for x.", "solution": "```python\nx = 5 - 2\nprint(x)\n```", "answer": "3"}
{"problem": "...", "solution": "...", "answer": "..."}
```

### 3. 파인튜닝 스크립트 생성 예정
```python
# scripts/finetune_qwen.py
# - LoRA/QLoRA 사용
# - Supervised Fine-Tuning (SFT)
# - MathCodeOrchestrator 스타일 프롬프트 학습
```

## VRAM 사용량 예상

| 모델 | Precision | VRAM | 속도 | 성능 |
|------|-----------|------|------|------|
| 0.5B | FP16 | ~2GB | 매우 빠름 | 낮음 |
| 1.5B | FP16 | ~4GB | 빠름 | 중간 |
| 7B | 4-bit | ~6GB | 중간 | 높음 |
| 7B Math | 4-bit | ~6GB | 중간 | 매우 높음 (수학) |
| 14B | 4-bit | ~8GB | 느림 | 매우 높음 |

## 파인튜닝 로드맵

### Phase 1: 데이터 수집 ✅
- ✅ Numina 60문제 (균형 샘플)
- ⏳ OpenMathReasoning 5000문제 ingest
- ⏳ MathCodeOrchestrator reference 문제 분석

### Phase 2: 베이스라인 평가
- ⏳ 1.5B 모델 성능 측정
- ⏳ 7B Math 모델 성능 측정
- ⏳ 전략별 성공률 분석

### Phase 3: 파인튜닝 설정
- ⏳ LoRA 설정 (rank=16, alpha=32)
- ⏳ 학습 데이터 전처리
- ⏳ Prompt template 최적화

### Phase 4: 학습
- ⏳ SFT on MathCodeOrchestrator-style problems
- ⏳ Few-shot learning 실험
- ⏳ Strategy-specific fine-tuning

### Phase 5: 평가 & 반복
- ⏳ Hold-out 테스트셋 평가
- ⏳ Error 분석 및 데이터 증강
- ⏳ Iterative improvement

## 다음 단계

1. **모델 크기 실험**: 1.5B → 7B Math 성능 비교
2. **데이터 수집**: OpenMathReasoning ingest 완료
3. **파인튜닝 스크립트**: LoRA/QLoRA 구현
4. **학습 파이프라인**: Weights & Biases 연동
5. **모델 평가**: MathCodeOrchestrator reference problems로 벤치마크
