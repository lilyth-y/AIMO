# 로컬 대용량 문제 데이터(예: 1.2GB JSONL) → SFT용 train/dev/test

한 파일이 크거나 여러 `.jsonl`로 나뉘어 있어도 됨. **`prepare_qwen_numeric_dataset_from_local.py`** 가 **줄 단위 스트리밍** + **reservoir sampling** 으로 처리해 **전체를 RAM에 올리지 않는다**.

## 전제 (한 줄 JSON)

| 필드 | 기본 키 | 설명 |
|------|---------|------|
| 문제 | `problem` (또는 `question` 폴백) | `--problem-key` 로 변경 가능 |
| 답 | `answer` | `--answer-key` 로 변경 가능 |
| 유형 | `question_type` (선택) | 값이 `proof` 이면 제외 (`--no-skip-proof` 로 포함) |

답은 **숫자/분수/과학표기** 형태만 통과 (기존 Numina 파이프와 동일 규칙).

## 이 레포의 `data/numinamath_full.jsonl`

약 **1.3GB**, NuminaMath-1.5 형식 한 줄 JSON (`problem`, `solution`, `answer`, `question_type`, …).  
기본 키(`problem` / `answer`) 그대로 쓰면 됨.

```powershell
cd C:\startingup\AIMO

python scripts/vertex/prepare_qwen_numeric_dataset_from_local.py `
  --input data/numinamath_full.jsonl `
  --seed 41 `
  --train 3000 --dev 1000 --test 1000 `
  --out-dir data/finetune/qwen_numeric
```

- `--max-raw-lines` **없이** 두면 파일 전체를 한 번 스캔한다 (시간 수 분~수십 분 가능, RAM은 과도하게 쓰지 않음).
- 스모크만 쓸 때만 `--max-raw-lines 50000` 등을 붙인다.

## 예시

**디렉터리**(하위 폴더 포함, 기본 `recursive=1`):

```powershell
cd C:\startingup\AIMO

python scripts/vertex/prepare_qwen_numeric_dataset_from_local.py `
  --input-dir "D:\path\to\your\problem_data" `
  --seed 41 `
  --train 3000 --dev 1000 --test 1000 `
  --out-dir data/finetune/qwen_numeric
```

**단일 파일**:

```powershell
python scripts/vertex/prepare_qwen_numeric_dataset_from_local.py `
  --input "D:\path\to\all.jsonl" `
  --train 3000 --dev 1000 --test 1000
```

**필드 이름이 다를 때** (예: 문제 키가 `question`만 있음):

```powershell
python scripts/vertex/prepare_qwen_numeric_dataset_from_local.py `
  --input-dir "D:\data" `
  --problem-key question `
  --answer-key answer
```

**스모크**(앞부분만 스캔):

```powershell
python scripts/vertex/prepare_qwen_numeric_dataset_from_local.py `
  --input-dir "D:\data" `
  --max-raw-lines 50000 `
  --train 100 --dev 20 --test 20 `
  --out-dir data/finetune/qwen_numeric_smoke
```

## 출력

- `data/finetune/qwen_numeric/train.jsonl` (기본)
- `dev.jsonl`, `test.jsonl`  
각 줄: `prompt`, `completion`(`<ANS>...</ANS>`), `answer`, `id`, `local_file`, `local_line` 등

다음 단계: [MERGE_TRAIN_UPLOAD.md](./MERGE_TRAIN_UPLOAD.md) §1 GCS 업로드 → Custom Job.

## 관련 스크립트

| 스크립트 | 입력 |
|----------|------|
| `prepare_qwen_numeric_dataset.py` | 작은 단일 `numina_training_5k.jsonl` |
| `prepare_qwen_numeric_dataset_from_hf.py` | HF `AI-MO/NuminaMath-1.5` 스트리밍 |
| **`prepare_qwen_numeric_dataset_from_local.py`** | **로컬 디렉터리 또는 단일 JSONL** |
