# Kaggle 환경 정합성 검토

AIMO Numina 평가가 Kaggle에서 돌아가도록 할 때, **우리 가정**과 **Kaggle 실제 환경**을 맞춘 검토입니다.

---

## 1. Kaggle 측 사실 (조사 기준)


| 항목           | 내용                                                               | 비고                      |
| ------------ | ---------------------------------------------------------------- | ----------------------- |
| **경로**       | `/kaggle/working` = 쓰기 가능, `/kaggle/input` = 추가한 Dataset 읽기 전용   | 표준 구조                   |
| **GPU**      | T4(×1/×2), P100 등 선택 가능, 주당 할당량 있음                               | Accelerator 설정 필수       |
| **Internet** | Settings에서 On/Off. Off면 HuggingFace 등 외부 접속 불가                   | 모델 다운로드 시 On 필요         |
| **Python**   | 3.x (정확 버전은 이미지에 따라 상이)                                          | 3.9+ 가정                 |
| **사전 설치**    | PyTorch(CUDA), numpy, pandas 등 포함. `torch` 재설치 시 CPU 버전으로 덮어쓸 위험 | Kaggle 기본 `torch` 사용 권장 |
| **세션**       | 연속 실행 시간 제한 있음 (예: 9~12시간)                                       | 60문항 1.5B는 보통 20~40분    |
| **SSH**      | 없음. 노트북/UI에서만 실행                                                 | 디버깅은 로그·Output 의존       |


---

## 2. 우리 코드·설정이 Kaggle에 맞는지

### 2.1 경로


| 용도        | 우리 설정                                                            | Kaggle에서 기대값                       | 정합성 |
| --------- | ---------------------------------------------------------------- | ---------------------------------- | --- |
| 프로젝트 루트   | `WORK_DIR = /kaggle/working/AIMO` (클론 시)                         | 동일                                 | ✅   |
| 데이터 디렉터리  | `AIMO_DATA_DIR` → `find_data_file()` 후보 첫 번째                     | `.../AIMO/data` 또는 `.../input/...` | ✅   |
| 결과 저장     | `AIMO_RESULTS_DIR=/kaggle/working` → `RESULTS_DIR = .../results` | `/kaggle/working/results/`         | ✅   |
| pip 설치 경로 | `-r /kaggle/working/AIMO/requirements-kaggle.txt`                | 클론 후 절대 경로                         | ✅   |


- `src/evaluation/config.py`: `AIMO_DATA_DIR`, `AIMO_RESULTS_DIR`(또는 `KAGGLE_DATA_DIR`, `KAGGLE_WORKING_DIR`)로 override. 노트북/스크립트에서 설정하면 Kaggle 경로와 일치.

### 2.2 환경 변수 (노트북·스크립트에서 설정)


| 변수                     | 설정 위치                                 | 역할                                            |
| ---------------------- | ------------------------------------- | --------------------------------------------- |
| `OMI_MODEL`            | 노트북 평가 셀 / 스크립트                       | HuggingFace repo 또는 `/kaggle/input/...` 로컬 경로 |
| `AIMO_RESULTS_DIR`     | 노트북·`scripts/run_numina_on_kaggle.py` | 결과 부모 → `results/` 생성                         |
| `AIMO_DATA_DIR`        | 노트북(파일 있을 때)·스크립트                     | `numina_eval_balanced.json`이 있는 디렉터리          |
| `EVAL_PROBLEM_TIMEOUT` | 노트북·스크립트                              | 문항당 최대 시간(초), 900 권장                          |
| `MAX_PROBLEMS`         | (선택) 노트북                              | 5 등으로 제한 시 선행 검증용                             |


정합성: 노트북이 **subprocess 전에** 위 변수들을 설정하고, subprocess의 `cwd=WORK_DIR`로 실행하므로 `config.py`의 `PROJECT_ROOT`와 데이터/결과 경로가 `/kaggle/working/AIMO` 기준으로 일치함.

### 2.3 패키지 (requirements-kaggle.txt)

- **torch**: 목록에 없음. Kaggle 기본 PyTorch(CUDA) 사용 권장. ✅  
- **transformers, datasets, accelerate, safetensors, sentencepiece**: 우리가 설치. Kaggle 이미지에 따라 이미 있을 수 있으나, 버전 통일을 위해 명시. ✅  
- **sympy, pandas, tqdm, grpcio, pyarrow 등**: 평가·데이터 로딩에 필요. ✅

잠재 이슈: Kaggle 이미지 업데이트로 사전 설치 버전이 바뀌면 `pip install -r`과 충돌할 수 있음. → **먼저 5문항으로 동작 여부 확인** 권장.

### 2.4 데이터 파일

- **필요 파일**: `numina_eval_balanced.json` (항목에 `problem`, `answer`, `source` 포함).
- **위치**:  
  - 클론 시 `.../AIMO/data/numina_eval_balanced.json`  
  - 또는 2.5 셀에서 HuggingFace로 생성 → `.../AIMO/data/numina_eval_balanced.json`
- `find_data_file()`은 `DATA_DIRS` 순서로 검색. `AIMO_DATA_DIR`가 `.../AIMO/data`로 설정되면 정합. ✅  
- **정합성 이슈**: 리포에 `data/numina_eval_balanced.json`이 없고 2.5 셀도 안 돌리면 `FileNotFoundError`. 문서/노트북에서 "2.5 데이터 준비 필수" 명시 필요.

### 2.5 실행 경로 두 가지


| 방식  | 진입점                                                                | env 설정                                | 비고                  |
| --- | ------------------------------------------------------------------ | ------------------------------------- | ------------------- |
| A   | 노트북에서 env 설정 후 `subprocess.run(examples/run_numina_evaluation.py)` | 노트북 셀                                 | 현재 노트북 방식           |
| B   | `python scripts/run_numina_on_kaggle.py`                           | 스크립트 내부에서 `_is_kaggle()` 시 setdefault | 체크리스트/KAGGLE_RUN 문서 |


둘 다 최종적으로 같은 `examples/run_numina_evaluation.py`를 부르며, Kaggle일 때 결과/데이터 경로가 동일하게 잡히면 정합. ✅  
단, **노트북은 현재 (A)** 이므로 `scripts/run_numina_on_kaggle.py`를 쓰지 않음. 문서에서 "노트북은 (A), 터미널처럼 한 번에 돌릴 때는 (B)"로 정리 필요.

---

## 3. 정합성 갭·리스크 요약


| 갭/리스크                              | 대응                                                             |
| ---------------------------------- | -------------------------------------------------------------- |
| Kaggle Python/패키지 버전 변경            | 5문항 선행 검증, 문제 시 requirements-kaggle.txt 버전 고정 검토               |
| 리포에 `numina_eval_balanced.json` 없음 | 노트북 2.5 셀(데이터 준비) 실행 필수 안내                                     |
| Internet Off 대회                    | 모델을 Dataset으로 올리고 `OMI_MODEL=/kaggle/input/...` 사용 (기존 문서 반영됨) |
| 0% 정확도                             | DIAGNOSTIC 출력 + ZERO_ACCURACY_DEBUG.md로 원인 좁히기                 |
| 노트북 vs 스크립트 설명 불일치                 | "작동시키는 과정" 문서에서 (A)/(B) 명시                                     |


---

## 4. 결론

- **경로·env·패키지**는 Kaggle 표준(`/kaggle/working`, `/kaggle/input`)과 맞게 설계되어 있음.
- **정합성 갭**은 (1) 데이터 파일 존재 여부, (2) Kaggle 환경 변경, (3) 문서/노트북 일치성 정리로 보완 가능.
- **보장은 없음**이므로, **5문항 선행 검증**과 **진단/문서**를 전제로 "Kaggle에서 작동시키는 과정"을 단일 절차로 정리하는 것이 좋음.

다음 문서: [KAGGLE_SETUP_PROCESS.md](KAGGLE_SETUP_PROCESS.md) (작동시키는 과정).