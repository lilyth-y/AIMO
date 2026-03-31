# Kaggle에서 실제 모델 돌리기 — 체크리스트

**목표:** Kaggle 노트북에서 AIMO 파이프라인을 돌려 Numina 데이터로 평가 결과를 냅니다.

---

## ✅ 가능 여부

- **가능합니다.** GPU 선택 + 리포/데이터 준비 + 실행 스크립트만 맞추면 됩니다.

---

## 1. Kaggle 노트북 설정

| 항목 | 설정 |
|------|------|
| **Accelerator** | **GPU** (T4 또는 P100 권장) |
| **Internet** | **On** (GitHub 클론 시 필요) |

---

## 2. 코드/데이터 준비 (둘 중 하나)

### 방법 A — GitHub에서 클론 (공개 리포)

1. **New Notebook** 생성 후 `notebooks/run_numina_on_kaggle.ipynb` 내용을 복사하거나, 리포를 업로드해 해당 노트북을 연다.
2. 첫 코드 셀에서 **`REPO_URL`** 를 본인 AIMO 리포 주소로 변경한다.
   ```python
   REPO_URL = "https://github.com/본인계정/AIMO.git"
   ```
3. 실행하면 `/kaggle/working/AIMO` 에 클론되고, `data/numina_eval_balanced.json` 도 함께 들어온다.

### 방법 B — Dataset으로 올린 경우

1. AIMO 리포(또는 `data/` + 코드만)를 **Kaggle Dataset**으로 업로드한다.
2. 노트북에서 **Add Data** → 해당 Dataset 추가.
3. `notebooks/run_numina_on_kaggle.ipynb` 의 "대안" 셀에서 **`INPUT_AIMO`** 를 Dataset 경로로 수정한 뒤, 그 셀을 실행해 `/kaggle/working/AIMO` 로 복사한다.
   - 예: Dataset 이름이 `aimo-repo` 이면 `/kaggle/input/aimo-repo`

---

## 3. 실행 순서 (노트북 셀 순서대로)

1. **리포 준비** — 클론 또는 Dataset 복사 (위 A 또는 B)
2. **패키지 설치** — `!pip install -q -r /kaggle/working/AIMO/requirements-kaggle.txt`
3. **(필요 시) 데이터 준비** — `numina_eval_balanced.json` 없으면 2.5 셀 실행 (HuggingFace에서 60문항 생성)
4. **모델 실행** — 환경 변수 설정 후 `subprocess.run(examples/run_numina_evaluation.py)` (노트북 3번 셀)  
   또는 `!python scripts/run_numina_on_kaggle.py` (스크립트가 env 자동 설정)
   - (권장) 5문항만 먼저: `os.environ["MAX_PROBLEMS"] = "5"` 설정 후 실행

**전체 과정 상세**: [KAGGLE_SETUP_PROCESS.md](KAGGLE_SETUP_PROCESS.md)

---

## 4. 데이터 위치

- **평가 데이터:** `numina_eval_balanced.json` 이 리포의 `data/` 안에 있으면 자동으로 사용됩니다.
- 클론 시: `AIMO/data/numina_eval_balanced.json` → 그대로 인식됨.
- Dataset에 `data/numina_eval_balanced.json` 만 넣었다면, `AIMO_DATA_DIR` 를 그 폴더로 설정 (예: `/kaggle/input/aimo-data`).

---

## 5. 결과 확인

- **저장 위치:** `/kaggle/working/results/`
- **파일:** `numina_balanced_results.json`, `gradient_report_numina_*.json` 등
- 노트북 **제출(Save Version)** 후 **Output** 탭에서 `results` 폴더를 다운로드하면 됩니다.

---

## 6. 요약

| 단계 | 할 일 |
|------|--------|
| 1 | 노트북에서 GPU + Internet On |
| 2 | AIMO 리포 클론 또는 Dataset 추가 후 working으로 복사 |
| 3 | `pip install -q -r requirements-kaggle.txt` |
| 4 | `python scripts/run_numina_on_kaggle.py` |
| 5 | Output에서 `results/` 다운로드 |

**모델:** 기본 1.5B (`Qwen/Qwen2.5-Math-1.5B-Instruct`). 13B로 바꾸려면 실행 전에 `os.environ["OMI_MODEL"] = "MathLLMs/MathCoder-L-13B"` 설정.

이 순서대로 하면 Kaggle에서 데이터로 실제 모델을 돌릴 수 있습니다.
