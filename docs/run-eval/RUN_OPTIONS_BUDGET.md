# 한정된 비용으로 평가 돌리기 (Kaggle vs GPU/TPU 빌리기)

비용을 최소로 쓰면서 GPU/TPU로 Numina 평가를 돌리는 방법입니다.

---

## Kaggle에서 잘 돌아간다는 보장이 있나?

**없습니다.** Kaggle 환경·정책·패키지 버전은 우리가 통제할 수 없고, 실제로 0% 정확도가 나오는 경우도 있습니다. 다만 아래를 지키면 **동작 여부를 빠르게 확인**할 수 있습니다.

- **60문항 바로 돌리지 말고, 먼저 5문항만 실행**  
  노트북에서 `os.environ["MAX_PROBLEMS"] = "5"` 설정 후 평가 셀 실행. 5문항이 끝나고 정확도/DIAGNOSTIC 출력을 보면, 모델 로드·답 추출·정답 판정이 되는지 알 수 있음.
- **0%가 나오면**  
  스크립트가 출력하는 **DIAGNOSTIC** 블록과 [ZERO_ACCURACY_DEBUG.md](ZERO_ACCURACY_DEBUG.md)를 보고 원인(참조 답 형식, 모델 미로드, 타임아웃 등)을 좁히면 됨.
- **예상 리스크**  
  패키지 버전 차이, GPU 미할당, Internet 꺼짐, `numina_eval_balanced.json` 경로/형식 오류, 세션 타임아웃 등. [KAGGLE_ENV_CHECK.md](KAGGLE_ENV_CHECK.md) 체크리스트를 한 번 확인하는 것을 권장.

정리: **보장은 없고, 5문항 선행 검증 + 진단/문서로 리스크를 줄이는 방식**입니다.

---

## 1. Kaggle (무료 GPU, SSH 없음) — 가장 저비용

**장점**: 무료, 주당 GPU 시간 제한만 있음.  
**단점**: SSH 없음 → 노트북/UI에서만 실행. 터미널 접속은 안 됨.

### 어떻게 돌리나 (3단계)

1. **Kaggle.com** 로그인 → **Code** → **New Notebook** (또는 기존 노트북).
2. **오른쪽 Settings**  
   - **Accelerator: GPU** (T4/P100 등)  
   - **Internet: On** (모델 다운로드용)
3. **노트북 업로드**  
   - 리포의 `notebooks/run_numina_on_kaggle.ipynb` 를 업로드하거나,  
   - 새 노트북에 아래만 넣고 순서대로 실행해도 됨.

### 최소 실행 순서 (노트북 셀)

```python
# 1) 리포 클론
REPO_URL = "https://github.com/lilyth-y/AIMO.git"
WORK_DIR = "/kaggle/working/AIMO"
BRANCH = "changes"
import os
from pathlib import Path
if Path(WORK_DIR).exists():
    !git -C {WORK_DIR} checkout {BRANCH} && git -C {WORK_DIR} pull origin {BRANCH}
else:
    !git clone --depth 1 -b {BRANCH} {REPO_URL} {WORK_DIR}
os.chdir(WORK_DIR)
```

```python
# 2) 패키지 설치
!pip install -q -r /kaggle/working/AIMO/requirements-kaggle.txt
```

```python
# 3) 먼저 5문항만 돌려서 동작 확인 권장 (보장은 없음)
import os
os.environ["MAX_PROBLEMS"] = "5"
os.environ.setdefault("AIMO_RESULTS_DIR", "/kaggle/working")
# 4) 평가 실행
!python /kaggle/working/AIMO/examples/run_numina_evaluation.py
```

끝나면 **Output** → `results` 폴더 다운로드. 5문항이 정상적으로 끝나고 (0%가 아니거나, 0%여도 DIAGNOSTIC으로 원인 파악 가능하면) 60문항으로 늘려서 돌리면 됨.

자세한 환경 점검은 [KAGGLE_ENV_CHECK.md](KAGGLE_ENV_CHECK.md), 실행 요약은 [KAGGLE_RUN.md](KAGGLE_RUN.md) 참고.

---

## 2. SSH + GPU/TPU 쓰고 싶을 때 (저비용 옵션)

Kaggle은 SSH를 주지 않으므로, **터미널 접속이 꼭 필요하면** 아래처럼 GPU/TPU 머신을 빌리는 쪽이 맞습니다.

| 옵션 | 대략 비용 | GPU/TPU | SSH | 비고 |
|------|-----------|---------|-----|------|
| **Google Colab** | 무료 / Pro 월 $10 | T4 등 | 노트북만 (SSH는 ngrok 등 별도) | Kaggle과 비슷한 워크플로 |
| **Colab Pro+** | 월 약 $50 | A100 등 | 제한적 | 더 큰 모델용 |
| **Lambda Labs** | 시간당 $0.5~1.1 | A10, A100 | ✅ | `ssh ubuntu@...` |
| **RunPod** | 시간당 $0.2~1+ | T4, A100 등 | ✅ | 저렴한 GPU 파드 |
| **Vast.ai** | 시간당 $0.2~0.5~ | 다양한 GPU | ✅ | 개인 호스트, 가격 변동 |
| **GCP** | 시간당 $0.3~1+ | T4, V100 등 | ✅ | Preemptible로 저렴 |
| **AWS SageMaker** | 사용량 과금 | 다양한 | ✅ | 스크립트/노트북 둘 다 가능 |

### SSH 있는 서버에서 똑같이 돌리기

어디서든 **GPU 머신 + SSH**만 있으면, 같은 평가 스크립트를 그대로 쓸 수 있습니다.

```bash
# 서버 접속 후
git clone -b changes https://github.com/lilyth-y/AIMO.git
cd AIMO
pip install -r requirements-kaggle.txt   # 또는 requirements.txt (torch는 환경에 맞게)
export OMI_MODEL=Qwen/Qwen2.5-Math-1.5B-Instruct
export AIMO_RESULTS_DIR=./results
export EVAL_PROBLEM_TIMEOUT=900
python examples/run_numina_evaluation.py
```

- **TPU**를 쓰려면 보통 JAX/Flax 또는 PyTorch+XLA 설정이 필요하고, 현재 AIMO 파이프라인은 **GPU + PyTorch(transformers)** 기준이라 TPU는 추가 작업이 필요합니다.  
- **GPU만** 쓸 때는 위 명령만으로 Kaggle과 동일한 평가가 돌아갑니다.

---

## 3. 정리

- **비용 최소 + SSH 불필요** → **Kaggle**에서 노트북으로 3단계만 실행 (위 1절).
- **SSH 필요 + GPU 직접 빌리기** → Lambda / RunPod / Vast.ai / GCP 등에서 인스턴스 띄운 뒤, 2절처럼 `git clone` → `pip install` → `run_numina_evaluation.py` 실행.

둘 다 **동일한 `examples/run_numina_evaluation.py`** 를 쓰므로, Kaggle에서 검증해 두고 나중에 SSH 서버로 옮겨서 돌려도 됩니다.
