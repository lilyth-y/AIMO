# Kaggle에서 평가 돌리기

Kaggle 노트북/스크립트에서 Numina 60문항 평가를 돌릴 때 가정과 권장 설정입니다.  
**단계별 작동 과정(설정 → 검증 포인트)**은 [KAGGLE_SETUP_PROCESS.md](KAGGLE_SETUP_PROCESS.md), **환경 정합성 검토**는 [KAGGLE_ENVIRONMENT_REVIEW.md](KAGGLE_ENVIRONMENT_REVIEW.md) 참고.

## Kaggle 환경 가정

- **GPU**: 보통 T4 16GB 또는 P100 (세션당 30시간 등 제한 있음)
- **세션 시간**: 노트북은 약 9~12시간 연속 실행 제한이 있을 수 있음
- **디스크**: HuggingFace 캐시용 공간 제한 있음

## 권장 설정

### 기본 (지금 코드 기본값)

- **모델**: `Qwen/Qwen2.5-Math-1.5B-Instruct` (1.5B)
- **양자화**: 8bit (필요 시)
- **60문항**: 보통 **20~40분** 내에 끝나서, 세션 제한 안에 여유 있음

별도 설정 없이 그대로 실행하면 1.5B가 쓰입니다.

**방법 1 – Kaggle 노트북 (권장)**  
- **`notebooks/run_numina_on_kaggle.ipynb`** 를 Kaggle에 업로드하거나, 새 노트북에서 내용을 복사해 실행하세요.  
- 설정에서 **Accelerator → GPU** 선택 후, 첫 셀에서 `REPO_URL`를 본인 AIMO 리포 주소로 바꾸고 순서대로 실행하면 됩니다.  
- 리포 클론 → `pip install -r requirements-kaggle.txt` → `python scripts/run_numina_on_kaggle.py` 로 Numina 평가가 돌고, 결과는 `/kaggle/working/results/`에 저장됩니다.

**방법 2 – 스크립트만 실행**  
이미 프로젝트가 `/kaggle/working` 아래에 있다면:
```python
!pip install -q -r requirements-kaggle.txt
!python scripts/run_numina_on_kaggle.py
```
- `/kaggle/working` 이 있으면 결과·데이터 경로를 자동 설정하고, 문항당 타임아웃(기본 900초)을 적용한 뒤 `examples/run_numina_evaluation.py` 를 실행합니다.

**방법 3 – 직접 실행**  
데이터 경로를 이미 맞춰 두었다면:
```python
!pip install -q -r requirements-kaggle.txt
!python examples/run_numina_evaluation.py
```
환경 점검 항목은 [KAGGLE_ENV_CHECK.md](KAGGLE_ENV_CHECK.md) 참고. **Internet을 켤 수 없는 환경**(일부 대회 등)에서는 해당 문서의 "Internet을 켤 수 없을 때" 섹션대로 모델을 Dataset으로 올리고 `OMI_MODEL`에 로컬 경로를 지정하면 됩니다.

### 13B로 정확도 우선 (시간 여유 있을 때)

세션 시간이 충분하고(예: 2~3시간 사용 가능), 정확도를 더 올리고 싶을 때만 13B 사용.

```python
import os
os.environ["OMI_MODEL"] = "MathLLMs/MathCoder-L-13B"
os.environ["OMI_QUANTIZATION"] = "8bit"
# 그 다음 run_numina_evaluation.py 실행
```

- 60문항이면 **1~3시간** 걸릴 수 있으므로, 제출/실험 한두 번 정도만 노리는 경우에 권장.

### 문항 수 줄여서 빠르게 확인

```python
import os
os.environ["MAX_PROBLEMS"] = "10"  # 10문항만
# 실행
```

- 1.5B + 10문항: **약 5~10분**
- 13B + 10문항: **약 15~30분**

## 결과·캐시

- **결과**: `results/numina_balanced_results.json`, `results/gradient_report_numina_*.json` 등이 노트북/스크립트 작업 디렉터리 기준으로 생성됩니다.
- **모델 캐시**: `HF_HOME` 또는 `TRANSFORMERS_CACHE`를 Kaggle 디스크 경로로 두면 다음 세션에서 다시 받지 않을 수 있으나, 세션이 끝나면 삭제될 수 있습니다.
- 제출용으로는 실행 끝난 뒤 `results/` 를 출력(Output)으로 저장하거나, 필요한 파일만 다운로드하면 됩니다.
- **한 문항에서 멈추지 않고 다음 문항으로 넘어가려면** `EVAL_PROBLEM_TIMEOUT=900`(초) 설정 권장. 문항당 최대 15분 후 타임아웃하고 다음 문항 진행.

## 요약

| 목적 | 모델 | MAX_PROBLEMS | 예상 시간 (참고) |
|------|------|--------------|------------------|
| Kaggle에서 기본 실행 | 1.5B (기본값) | 없음(60) | 20~40분 |
| 빠른 검증만 | 1.5B | 10 | 5~10분 |
| 정확도 우선 (시간 여유 시) | 13B (OMI_MODEL 설정) | 없음(60) | 1~3시간 |

**정리**: Kaggle에서는 **기본값(1.5B)** 그대로 60문항 돌리면 세션 제한 안에서 무난하게 끝납니다. 13B는 시간이 충분할 때만 쓰면 됩니다.
