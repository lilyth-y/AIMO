# 빠른 평가 (모델·문항 수 줄이기)

**기본 모델**은 이제 **Qwen2.5-Math-1.5B-Instruct(1.5B)** 입니다. 60문항이면 보통 20~~40분 정도 걸립니다.~~  
~~더 높은 정확도를 원하면 `OMI_MODEL=MathLLMs/MathCoder-L-13B` 로 13B를 쓸 수 있습니다 (1~~3시간 예상).

- **Kaggle에서 돌릴 때**: [KAGGLE_RUN.md](KAGGLE_RUN.md) 참고.

## 1. 더 작은/빠른 모델로 실행 (기본값이 이미 1.5B)

**1.5B**가 기본값이라 별도 설정 없이도 빠르게 돌아갑니다. 13B로 바꾸려면 아래처럼 `OMI_MODEL`만 설정하면 됩니다.

### PowerShell

```powershell
$env:OMI_MODEL = "Qwen/Qwen2.5-Math-1.5B-Instruct"
$env:MAX_PROBLEMS = "10"   # 10문항만 (테스트용)
python examples/run_numina_evaluation.py
```

### CMD

```cmd
set OMI_MODEL=Qwen/Qwen2.5-Math-1.5B-Instruct
set MAX_PROBLEMS=10
python examples/run_numina_evaluation.py
```

- `MAX_PROBLEMS` 를 빼면 **60문항 전체** 실행.
- 1.5B로 60문항이면 보통 **20~40분** 정도 예상.

## 2. 문항 수만 줄이기 (모델은 13B 유지)

모델은 그대로 두고 **문항 수만** 줄이려면:

```powershell
$env:MAX_PROBLEMS = "5"    # 5문항만
python examples/run_numina_evaluation.py
```

5문항이면 13B 기준으로도 **대략 10~20분** 안에 끝날 수 있습니다.

## 3. 요약


| 설정         | 예상 시간 (참고) |
| ---------- | ---------- |
| 13B, 60문항  | 1~3시간      |
| 13B, 5문항   | 약 10~20분   |
| 1.5B, 60문항 | 약 20~40분   |
| 1.5B, 10문항 | 약 5~10분    |


**빠르게 벤치마크만 보려면:** `OMI_MODEL=Qwen/Qwen2.5-Math-1.5B-Instruct` + `MAX_PROBLEMS=10` 또는 `60` 권장.