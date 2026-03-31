# Kaggle 실행 환경 점검

Kaggle 노트북/스크립트에서 Numina 평가를 돌리기 전에 확인할 항목입니다.

## 1. 필수 환경

| 항목 | 확인 방법 | 비고 |
|------|-----------|------|
| **GPU** | 노트북 설정 → Accelerator: GPU (T4/P100 등) | CPU만 있으면 매우 느림 |
| **Python** | 3.9+ | Kaggle 기본 3.10 등 |
| **디스크** | `/kaggle/working` 쓰기 가능 | 결과 저장용 |

## 2. 패키지

- **torch**: Kaggle 환경에는 보통 **CUDA 포함 PyTorch**가 이미 설치되어 있음. `requirements.txt`의 `torch --extra-index-url .../cpu`는 **로컬 CPU용**이므로 Kaggle에서는 **설치하지 말고** 기본 환경 사용 권장.
- 나머지: `pip install -r requirements.txt` 시 **torch 줄은 제외**하거나, Kaggle에서 먼저 `pip install torch` (기본이면 생략) 후 `pip install pandas polars sympy scipy numpy protobuf grpcio pyarrow transformers accelerate safetensors sentencepiece psutil tqdm` 등만 설치.

**권장 (Kaggle 노트북 상단):**
```python
!pip install -q -r requirements-kaggle.txt
```
- **Dependency Manager에 넣을 때:** `requirements-kaggle-deps.txt` 또는 `requirements-kaggle-paste.txt` 내용을 그대로 복사해 패키지 목록란에 붙여넣거나, `pip install -r requirements-kaggle-deps.txt` 로 설치.
- `requirements-kaggle.txt`에는 **kaggle** 패키지(공식 API) 포함. 데이터셋 다운로드/제출을 노트북에서 할 때 사용. 로컬에서 `tests/kaggle_cred_test.py` 등으로 API 확인 시에도 동일.

## 3. 데이터 경로

- **Numina 평가 데이터** `numina_eval_balanced.json` 이 다음 중 한 곳에 있어야 함:
  - `/kaggle/working/data/numina_eval_balanced.json` (노트에서 복사/업로드한 경우)
  - 또는 Dataset 추가 후 `/kaggle/input/<dataset-name>/numina_eval_balanced.json`
- 환경 변수로 데이터 디렉터리 지정 가능:
  - `AIMO_DATA_DIR=/kaggle/input/my-aimo-data` 또는 `KAGGLE_DATA_DIR=...`
- 프로젝트를 `/kaggle/working`에 올렸다면 `data/` 폴더를 만들고 그 안에 `numina_eval_balanced.json`을 두면 됨.

## 4. 결과 저장

- 기본 결과 경로: 프로젝트 루트의 `results/` (코드에서 `PROJECT_ROOT` 기준).
- Kaggle에서 결과를 working에 남기려면:
  - `AIMO_RESULTS_DIR=/kaggle/working` 설정 시 → `results/` 가 `/kaggle/working/results/` 로 생성됨.
- 제출 후 Output에서 `results/` 폴더를 다운로드하면 됨.

## 5. 선택 환경 변수 (Kaggle)

| 변수 | 의미 | 예시 |
|------|------|------|
| `OMI_MODEL` | 사용 모델 | 기본 1.5B, `MathLLMs/MathCoder-L-13B` 등 |
| `MAX_PROBLEMS` | 문항 수 제한 | `5`, `10`, `60` |
| `EVAL_PROBLEM_TIMEOUT` | 문항당 최대 시간(초) | `900` (15분) → 한 문항에서 멈추지 않고 다음으로 진행 |
| `AIMO_DATA_DIR` | 데이터 디렉터리 | `/kaggle/input/aimo-data` |
| `AIMO_RESULTS_DIR` | 결과 부모 경로 | `/kaggle/working` |

## 6. Internet을 켤 수 없을 때 (오프라인 / 대회)

일부 대회나 환경에서는 노트북에서 **Internet을 켤 수 없습니다**. 그런 경우:

1. **모델을 미리 받아서 Kaggle Dataset으로 올리기**
   - 로컬 또는 Internet 가능한 노트북에서 `Qwen/Qwen2.5-Math-1.5B-Instruct` (또는 사용할 모델)를 다운로드합니다.
   - 해당 폴더 전체를 Kaggle Dataset으로 업로드합니다.
2. **노트북에서 Dataset 추가 후 경로 지정**
   - 노트북 Settings → Add Data → 방금 만든 모델 Dataset 추가.
   - 실행 전에 `OMI_MODEL` 을 **로컬 경로**로 설정합니다. 예: `OMI_MODEL=/kaggle/input/qwen-math-1-5b`
   - 코드는 해당 경로가 실제로 존재할 때만 `local_files_only=True` 로 로드하므로, Dataset 경로를 그대로 쓰면 됩니다.

정리: Internet Off 환경에서는 HuggingFace repo_id로는 다운로드가 불가하므로, **모델을 Dataset으로 올리고 `OMI_MODEL` 에 그 경로**를 넣어 사용하세요.

## 7. 점검 체크리스트

- [ ] Accelerator: GPU
- [ ] `numina_eval_balanced.json` 경로 확인 (또는 `AIMO_DATA_DIR` 설정)
- [ ] `pip install` 시 **CPU 전용 torch 인덱스 사용 안 함** (Kaggle 기본 GPU torch 사용)
- [ ] (선택) `EVAL_PROBLEM_TIMEOUT=900` 으로 한 문항 과부하 시 다음 문항으로 진행
- [ ] (선택) `AIMO_RESULTS_DIR=/kaggle/working` 으로 결과를 working에 저장

이 항목들을 맞춘 뒤 실행하면 됩니다. **단계별 작동 과정**은 [KAGGLE_SETUP_PROCESS.md](KAGGLE_SETUP_PROCESS.md), **환경 정합성 검토**는 [KAGGLE_ENVIRONMENT_REVIEW.md](KAGGLE_ENVIRONMENT_REVIEW.md) 참고. 실행 요약은 [KAGGLE_RUN.md](KAGGLE_RUN.md).  
Internet을 켤 수 없으면 위 **6. Internet을 켤 수 없을 때** 를 참고해 모델을 Dataset으로 올리고 `OMI_MODEL` 에 로컬 경로를 지정하세요.
