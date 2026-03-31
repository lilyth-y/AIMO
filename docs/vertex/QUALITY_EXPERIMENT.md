# 품질 실험 트랙 (배포용과 분리)

**목적**: 형식(`<ANS>`)·채점 파이프·지표가 의미 있게 도는지 **빠르고 저렴하게** 검증.  
**실제 배포용** 전체 학습·머지·Vertex는 [MERGE_TRAIN_UPLOAD.md](./MERGE_TRAIN_UPLOAD.md) 등으로 **별도** 진행한다.

**귀무가설·대조군·Vertex vs 클라이언트 역할**이 정리된 전체 설계: [RESEARCH_EXPERIMENT_PROTOCOL.md](./RESEARCH_EXPERIMENT_PROTOCOL.md)

| 구분 | 품질 실험 | 실제 배포용 |
|------|-----------|-------------|
| 데이터 | `numinamath_full.jsonl` 일부 스캔 + 소량 train/dev/test | 필터 통과분 대규모 또는 전체 |
| 출력 디렉터리 | `data/finetune/qwen_numeric_quality_exp/` (예) | `data/finetune/qwen_numeric/` |
| 학습 | 로컬 짧은 실험 또는 스킵, Vertex 소형 Job | Custom Job + `--save-merged` |
| 평가 | `eval_hf_local_quality.py` 소 `n`, `strict_format_compliance` 확인 | 동일 채점기 + 엔드포인트 평가 |

## 1) 소규모 JSONL 만들기

```powershell
cd C:\startingup\AIMO

python scripts/vertex/prepare_qwen_numeric_dataset_from_local.py `
  --input data/numinamath_full.jsonl `
  --seed 42 `
  --max-raw-lines 200000 `
  --train 400 --dev 100 --test 100 `
  --out-dir data/finetune/qwen_numeric_quality_exp
```

- `--max-raw-lines`: 전체 1.3GB를 다 안 돌리고 앞부분만 스캔 (실험용).
- 배포용과 섞이지 않게 **`--out-dir`** 을 실험 전용으로 둔다.

## 2) 로컬 품질 평가 (채점·형식 지표)

`eval_hf_local_quality.py`는 기본적으로 **`data/numina_training_5k.jsonl` 등 Numina 원문**(문제·정답)에서 샘플을 뽑는다.  
§1에서 만든 `*_quality_exp/*.jsonl`은 **SFT 학습용**이며, 이 스크립트의 입력 데이터와는 역할이 다르다 (파이프라인·형식 검증용으로는 Numina 샘플이면 충분).

베이스 HF 모델로 Numina 샘플 점수 (학습과 무관하게 파이프 검증 가능):

```powershell
python scripts/eval_hf_local_quality.py `
  --model Qwen/Qwen2.5-Math-1.5B-Instruct `
  --n-problems 15 `
  --max-format-retries 2 `
  --device auto
```

- `strict_format_compliance`, `accuracy`, `results/hf_local_eval_*.jsonl` 확인.

## 3) (선택) 실험용 JSONL로 로컬 QLoRA

GPU·시간 여유 있을 때만. 출력 어댑터는 `results/` 등에 두고 배포 경로와 분리.

---

**한 줄**: 품질 실험 = **작은 데이터 + 같은 채점·형식 게이트 + 별 출력 폴더**. 배포용은 **별 브랜치/별 GCS prefix**로 가져가면 혼선이 없다.
