# Kaggle에서 작동시키는 과정

Numina 평가를 **Kaggle 노트북에서 처음부터 작동시키기 위해 거치는 단계**를 하나의 절차로 정리한 문서입니다.  
환경 정합성 검토는 [KAGGLE_ENVIRONMENT_REVIEW.md](KAGGLE_ENVIRONMENT_REVIEW.md)를 참고하세요.

---

## 전제

- Kaggle 계정 있음.
- AIMO 리포지토리를 GitHub에 푸시해 둔 상태 (또는 Kaggle Dataset으로 올릴 수 있음).
- **보장은 없음.** 5문항으로 먼저 동작 여부를 확인한 뒤 60문항을 돌리는 것을 권장합니다.

---

## 과정 요약

| 단계 | 내용 | 검증 포인트 |
|------|------|-------------|
| 1 | Kaggle 노트북 생성·설정 (GPU, Internet) | Settings에서 확인 |
| 2 | 리포지토리 준비 (클론 또는 Dataset 복사) | `WORK_DIR`에 코드·data 존재 |
| 3 | 패키지 설치 | `pip install -r requirements-kaggle.txt` 성공 |
| 4 | (필요 시) 평가 데이터 생성 | `numina_eval_balanced.json` 존재 |
| 5 | 환경 변수 설정 후 평가 실행 | 5문항 → 정상 종료·결과 확인 → 60문항 |
| 6 | 결과 다운로드 | `/kaggle/working/results/` → Output |

---

## 1단계: 노트북 설정

1. **Kaggle.com** → **Code** → **New Notebook** (또는 기존 노트북 열기).
2. 오른쪽 **Settings**:
   - **Accelerator**: **GPU** (T4 또는 P100).
   - **Internet**: **On** (모델·데이터 다운로드용).  
     대회 등으로 Off만 가능한 경우에는 [KAGGLE_ENV_CHECK.md](KAGGLE_ENV_CHECK.md)의 "Internet을 켤 수 없을 때" 대로 모델을 Dataset으로 올려야 함.

**검증**: Settings에 GPU·Internet On이 반영되어 있는지 확인.

---

## 2단계: 리포지토리 준비

### 방법 A — GitHub 클론 (권장)

1. 노트북에 아래와 같은 코드 셀을 넣고 실행. (포크·다른 원격을 쓰면 `REPO_URL`만 바꾼다.)

```python
REPO_URL = "https://github.com/lilyth-y/AIMO.git"
WORK_DIR = "/kaggle/working/AIMO"
BRANCH = "changes"  # 사용하는 브랜치로 맞추기

import os
from pathlib import Path

if Path(WORK_DIR).exists():
    !git -C {WORK_DIR} checkout {BRANCH}
    !git -C {WORK_DIR} pull origin {BRANCH}
    print("[OK] pull 완료")
else:
    !git clone --depth 1 -b {BRANCH} {REPO_URL} {WORK_DIR}
    print(f"[OK] 클론 완료: {WORK_DIR}")
os.chdir(WORK_DIR)
print("CWD:", os.getcwd())
```

2. **검증**:  
   - `!ls /kaggle/working/AIMO` 로 프로젝트 디렉터리 확인.  
   - `!ls /kaggle/working/AIMO/data` 로 `data` 폴더 확인 (파일 없어도 됨. 4단계에서 생성 가능).

### 방법 B — Kaggle Dataset으로 올린 뒤 복사

1. AIMO 리포(또는 코드+data)를 **Kaggle Dataset**으로 업로드.
2. 노트북에서 **Add Data** → 해당 Dataset 추가.
3. 아래처럼 Dataset 경로를 넣고, **WORK_DIR**로 복사한 뒤 `os.chdir(WORK_DIR)` 실행.

```python
INPUT_AIMO = "/kaggle/input/your-dataset-name"  # Dataset 이름에 맞게
WORK_DIR = "/kaggle/working/AIMO"
import shutil
from pathlib import Path
if Path(INPUT_AIMO).exists() and not Path(WORK_DIR).exists():
    shutil.copytree(INPUT_AIMO, WORK_DIR)
os.chdir(WORK_DIR)
print("CWD:", os.getcwd())
```

4. **검증**: `!ls /kaggle/working/AIMO` 로 코드·필요 시 `data` 존재 확인.

---

## 3단계: 패키지 설치

1. **한 셀**에 다음만 넣고 실행.

```python
!pip install -q -r /kaggle/working/AIMO/requirements-kaggle.txt
print("설치 완료.")
```

2. **검증**: 에러 없이 "설치 완료." 출력.  
   (이미지에 따라 일부 패키지가 이미 있어도, 버전 충돌이 없으면 진행.)

---

## 4단계: 평가 데이터 준비

- **이미** `/kaggle/working/AIMO/data/numina_eval_balanced.json` 이 있으면 이 단계 생략.
- 없으면 아래 셀을 실행해 **같은 경로에 생성**.

```python
WORK_DIR = "/kaggle/working/AIMO"
DATA_FILE = f"{WORK_DIR}/data/numina_eval_balanced.json"

if __import__("pathlib").Path(DATA_FILE).exists():
    print("[OK] numina_eval_balanced.json 이미 있음. 건너뜀.")
else:
    import os, sys
    os.makedirs(f"{WORK_DIR}/data", exist_ok=True)
    sys.path.insert(0, f"{WORK_DIR}/src")
    os.chdir(WORK_DIR)
    from data.numina_loader import NuminaMathDataLoader
    loader = NuminaMathDataLoader(version="1.5", cache_dir=f"{WORK_DIR}/data/numina_cache")
    loader.load_dataset(streaming=True)
    loader.create_evaluation_set(
        n_easy=10, n_medium=20, n_hard=30,
        output_file=DATA_FILE
    )
    print("[OK] numina_eval_balanced.json 생성 완료.")
```

**검증**: `!ls /kaggle/working/AIMO/data/numina_eval_balanced.json` 로 파일 존재 확인.

---

## 5단계: 환경 변수 설정 + 평가 실행

1. **먼저 5문항**으로 동작 검증을 권장합니다. 아래 셀에서 `MAX_PROBLEMS = "5"` 를 설정한 뒤 실행.

```python
import os
import sys
import subprocess

WORK_DIR = "/kaggle/working/AIMO"

# (선택) Kaggle Dataset에 올린 로컬 모델이 있으면 경로 지정 (Internet Off 시 필수)
KAGGLE_MODEL_PATH = ""  # 예: "/kaggle/input/qwen-math-1-5b/..."
if KAGGLE_MODEL_PATH and os.path.exists(KAGGLE_MODEL_PATH):
    os.environ["OMI_MODEL"] = KAGGLE_MODEL_PATH
    print("[Kaggle] Using local model:", KAGGLE_MODEL_PATH)
else:
    os.environ["OMI_MODEL"] = "Qwen/Qwen2.5-Math-1.5B-Instruct"
    print("[Kaggle] Using HuggingFace (Internet 필요)")

# 필수: 결과·데이터 경로 (노트북이 subprocess 전에 설정)
os.environ.setdefault("AIMO_RESULTS_DIR", "/kaggle/working")
os.environ.setdefault("EVAL_PROBLEM_TIMEOUT", "900")
if not os.environ.get("AIMO_DATA_DIR"):
    if os.path.exists(f"{WORK_DIR}/data/numina_eval_balanced.json"):
        os.environ["AIMO_DATA_DIR"] = f"{WORK_DIR}/data"

# 선행 검증: 5문항만 (정상 동작 확인 후 60문항 시 아래 줄 삭제 또는 주석)
os.environ["MAX_PROBLEMS"] = "5"

print("[Kaggle] OMI_MODEL =", os.environ.get("OMI_MODEL"))
print("[Kaggle] AIMO_RESULTS_DIR =", os.environ.get("AIMO_RESULTS_DIR"))
print("[Kaggle] AIMO_DATA_DIR =", os.environ.get("AIMO_DATA_DIR", "(auto)"))

rc = subprocess.run(
    [sys.executable, f"{WORK_DIR}/examples/run_numina_evaluation.py"],
    cwd=WORK_DIR,
    env={**os.environ},
    stdin=subprocess.DEVNULL,
)
if rc.returncode != 0:
    raise SystemExit(rc.returncode)
```

2. **검증**  
   - 5문항이 끝나고 `returncode 0`으로 종료.  
   - 로그에 정확도·DIAGNOSTIC(0%일 때) 출력 확인.  
   - `!ls /kaggle/working/results/` 로 결과 파일 생성 여부 확인.

3. **60문항**으로 돌릴 때  
   - 위 셀에서 `os.environ["MAX_PROBLEMS"] = "5"` 줄을 **삭제하거나 주석** 처리한 뒤 다시 실행.

**대안 — 스크립트 한 번에 실행**  
리포가 이미 `/kaggle/working/AIMO`에 있고, env를 스크립트에 맡기려면:

```python
import os
os.chdir("/kaggle/working/AIMO")
# (선택) os.environ["MAX_PROBLEMS"] = "5"
!python scripts/run_numina_on_kaggle.py
```

`scripts/run_numina_on_kaggle.py`가 Kaggle 여부를 감지해 `AIMO_RESULTS_DIR`, `AIMO_DATA_DIR`, `EVAL_PROBLEM_TIMEOUT`를 설정한 뒤 `examples/run_numina_evaluation.py`를 실행합니다.

---

## 6단계: 결과 다운로드

1. 노트북 **Save Version** (또는 Run All 후 저장).
2. **Output** 탭에서 `/kaggle/working/results/` 아래 파일 확인.
3. **results** 폴더를 다운로드.

---

## 트러블슈팅

| 현상 | 참고 문서·조치 |
|------|----------------|
| 0% 정확도 | 스크립트 DIAGNOSTIC 출력 + [ZERO_ACCURACY_DEBUG.md](ZERO_ACCURACY_DEBUG.md) |
| `FileNotFoundError: numina_eval_balanced.json` | 4단계 실행 여부, `AIMO_DATA_DIR`가 데이터 디렉터리를 가리키는지 확인 |
| 모델 다운로드 실패 / "outgoing traffic disabled" | Internet On, 또는 모델 Dataset + `OMI_MODEL=/kaggle/input/...` |
| 패키지 충돌 | 5문항으로 동작 여부 확인 후, 필요 시 [KAGGLE_ENV_CHECK.md](KAGGLE_ENV_CHECK.md) 패키지 섹션 참고 |

---

## Ipynb로 실행 (CLI에서 노트북 실행)

노트북 파일(.ipynb)을 **CLI에서 한 번에 실행**하려면:

```bash
# 프로젝트 루트에서
python scripts/execute_numina_notebook.py
```

- **nbconvert/nbformat**이 설치되어 있으면 `notebooks/run_numina_on_kaggle.ipynb`를 실행하고, 결과 노트북을 `*_executed.ipynb`로 저장합니다.
- nbconvert이 없거나, 노트북이 Kaggle 전용 경로(`/kaggle/working`)를 써서 로컬에서 실패하면 **examples/run_numina_evaluation.py**를 대신 실행합니다.
- 5문항만 돌리기: `python scripts/execute_numina_notebook.py --max-problems 5`
- 노트북 실행 없이 평가 스크립트만 실행: `python scripts/execute_numina_notebook.py --script-only`

Kaggle 웹에서는 노트북을 업로드한 뒤 Run All로 실행하면 됩니다.

---

## 관련 문서

- [KAGGLE_ENVIRONMENT_REVIEW.md](KAGGLE_ENVIRONMENT_REVIEW.md) — Kaggle 환경 정합성 검토  
- [KAGGLE_ENV_CHECK.md](KAGGLE_ENV_CHECK.md) — 실행 환경 체크리스트  
- [KAGGLE_RUN.md](KAGGLE_RUN.md) — 모델/문항 수 등 권장 설정  
- [ZERO_ACCURACY_DEBUG.md](ZERO_ACCURACY_DEBUG.md) — 0% 정확도 시 원인·대응  
- [RUN_OPTIONS_BUDGET.md](RUN_OPTIONS_BUDGET.md) — 한정 비용·Kaggle vs GPU/TPU 옵션
