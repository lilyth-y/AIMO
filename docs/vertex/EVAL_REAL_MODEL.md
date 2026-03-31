# 실제 모델로 품질 평가하기

“인프라 스모크(tiny-gpt2)”와 달리, **실제 가중치**로 정답 일치율을 보려면 아래 **두 경로** 중 하나를 쓴다.

| 경로 | 언제 쓰나 | 스크립트 |
|------|-----------|----------|
| **로컬 / HF Hub** | GCS에 아직 없거나, Vertex 없이 빠르게 숫자를 보고 싶을 때 | `scripts/eval_hf_local_quality.py` |
| **Vertex Endpoint** | 이미 배포된 엔드포인트(머지 아티팩트)에 대해 | `scripts/eval_vertex_endpoint_quality.py` |

Ralph 목표 정확도(기본 80%)·Custom Job·요약 JSON 게이트: [../run-eval/RALPH_VERTEX.md](../run-eval/RALPH_VERTEX.md)

채점기는 동일 계열: `AnswerExtractor` + `check_answer_correctness` (Numina 샘플 숫자답 필터).  
`check_answer_correctness`는 정규화 후 문자열 일치 → SymPy 등가 → **스칼라 실수 근사**(`math.isclose`) 순으로 판정하며, 비율(`2:1` vs `2`)·구간 표기 동치는 포함하지 않는다. JSONL에는 `match_kind`(strict / sympy / numeric / none)와 요약 `match_kind_breakdown`이 포함된다.

**품질 실험만 따로** (소량 데이터·배포와 분리): [QUALITY_EXPERIMENT.md](./QUALITY_EXPERIMENT.md)

---

## 1) 로컬·HF 실제 모델 (권장: 먼저 시도)

```powershell
cd C:\startingup\AIMO
# 기본 저장소 설정은 7B (AIMO_MODEL). 명시하려면:
python scripts/eval_hf_local_quality.py --model Qwen/Qwen2.5-Math-7B-Instruct --n-problems 30
# VRAM 부족 시 1.5B: --model Qwen/Qwen2.5-Math-1.5B-Instruct
```

**머지/튜닝 가중치(로컬 HF 디렉터리)** 예:

```powershell
python scripts/eval_hf_local_quality.py --model D:\path\to\merged --n-problems 50 --device auto
```

- `--model`: HF Hub ID 또는 **로컬 머지 루트** (`config.json` 이 있는 폴더). 존재하지 않는 Windows 경로를 주면 시작 전에 오류로 알려 준다.
- 기본 `--n-problems` 는 **30** (통계·프롬프트 준수율 확인에 맞춤). 더 촘촘히 보려면 50 등으로 올린다.
- GPU가 있으면 `device=auto` 기본으로 로드.
- CPU만 쓸 때: `--device cpu` (소형 모델·짧은 `n` 권장).

결과: `results/hf_local_eval_<시간>.jsonl` + stdout JSON 요약.

**프롬프트(`<ANS>...</ANS>`) 준수 확인**

| 확인 위치 | 내용 |
|-----------|------|
| stdout 요약 | `ans_tag_compliance.rate` — 생성 **연속 구간**(프롬프트 제외)에 `<ANS>`·`</ANS>` 쌍 비율 |
| stdout 요약 | `predicted_nonnull.rate` — 추출기가 숫자/식으로 잡은 비율 |
| JSONL 각 줄 | `has_ans_tags`, `completion_head`(연속 앞부분), `raw_text_head`, `extracted` |

베이스 모델이 지시를 잘 안 따르면 `ans_tag_compliance` 가 낮게 나올 수 있다. 머지/튜닝 모델에서 이 비율이 오르는지 같이 보면 된다.

### 엄격 형식 + 재시도 (`eval_hf_local_quality.py`)

배포·채점 전에 **단일·비어 있지 않은 `<ANS>` 블록**을 통과할 때까지 로컬에서 재생성한다.

- 구현: `src/pipeline/ans_format_guard.py` (`validate_ans_strict`, 재시도용 프롬프트)
- 스크립트: `--max-format-retries` (기본 3), `--retry-temperature` (기본 0.35)
- stdout 요약: `strict_format_compliance` — 통과한 문제 비율, `format_attempts` — 재시도 포함 총 생성 횟수
- JSONL: `strict_format_ok`, `format_attempts`, `format_failure_reason`, `scoring_status` (`graded` / `skipped_invalid_format`)
- **정확도(`accuracy`)**는 `scoring_status == graded` 인 경우만 의미 있는 비교(형식 실패 시 채점 스킵).

`AnswerExtractor`는 `<ANS>` 태그 매칭을 **대소문자 무시**로 통일했다.

---

## 2) Vertex에 배포한 뒤 엔드포인트로

1. [MERGED_MODEL_ARTIFACT.md](./MERGED_MODEL_ARTIFACT.md) 대로 `merged/` 를 GCS에 두고 배포. (베이스 Hub 모델만 올릴 때는 `scripts/vertex/upload_hf_model_to_gcs.py` 참고.)
2. 엔드포인트 ID 확인 후:

```powershell
python scripts/eval_vertex_endpoint_quality.py --endpoint-id <ENDPOINT_ID> --n-problems 50
```

기본적으로 **`ans_format_guard`** 와 동일하게 첫 프롬프트(`build_prompt_strict_first`) + 형식 실패 시 재시도(`build_format_repair_prompt`, `--max-format-retries`)를 쓴다. 형식이 끝까지 안 맞으면 `\\boxed{}` 보조 추출 등 **완화 채점**(`--no-fallback-boxed` 로 끄기 가능). 구버전 한 번만 호출은 `--no-format-gate`.

**서빙(`docker/vertex-serve/serve.py`)** 은 `predictions[].text` 에 **새로 생성된 토큰만** 넣는다. (과거에는 프롬프트+전체를 디코드해 응답 앞부분이 항상 지시문·문제 본문처럼 보이고, `eval` 의 `raw_text_head`(800자) 만으로는 `<ANS>` 가 안 보이는 경우가 많았다.) 이미지를 바꾼 뒤에는 `docker build` → `push` → 엔드포인트에 **재배포**해야 반영된다.

### 생성 토큰 한도 (서빙·평가)

- **완전 무제한은 불가** (모델 `max_position_embeddings`·GPU 메모리 한도).
- 서빙 컨테이너: `AIMO_MAX_NEW_TOKENS` 기본 **8192**; **`0` / `none` / `unlimited`** 이면 프롬프트 길이를 뺀 컨텍스트만큼 생성(추가 상한 `AIMO_MAX_NEW_TOKENS_HARD_CAP`, 기본 32768).
- 평가 스크립트: `VERTEX_MAX_NEW_TOKENS` 기본 **8192**; 동일하게 `0` 등으로 “남는 만큼” 전달 가능. **`VERTEX_PREDICT_TIMEOUT_SECONDS`** 기본 **600** (`--predict-timeout`), SDK에 넘기기 전 **`VERTEX_PREDICT_TIMEOUT_MAX`(기본 600)** 으로 상한 클램프. `<=0`·미지정에 가까운 값은 **`VERTEX_PREDICT_TIMEOUT_FLOOR`(기본 600)** 으로 올려 gRPC 기본(~60초) 503을 피한다. **최소**는 **`VERTEX_PREDICT_TIMEOUT_MIN`(기본 90)**. **60초 전후 503**은 여전히 짧은 타임아웃·엔드포인트 측 한도 가능성이 있다. 실패 시 JSONL **`predict_progress`**에 형식 라운드·`predict_calls` 단위 기록.

### serve 이미지 수정 후 재배포 (요약)

```powershell
cd C:\startingup\AIMO
gcloud auth configure-docker us-central1-docker.pkg.dev --quiet
docker build -t us-central1-docker.pkg.dev/gen-lang-client-0300734101/aimo/vertex-serve:latest -f docker/vertex-serve/Dockerfile .
docker push us-central1-docker.pkg.dev/gen-lang-client-0300734101/aimo/vertex-serve:latest

# 서울에 동일 아티팩트로 새 엔드포인트 (예)
# 7B 배포 시 GCS 경로 예시 (업로드는 upload_hf_model_to_gcs.py — [DEPLOY_QWEN_7B_VERTEX.md](./DEPLOY_QWEN_7B_VERTEX.md))
$env:ARTIFACT_URI = "gs://gen-lang-client-0300734101-aimo-vertex-341687483990/aimo/models/hf/Qwen2.5-Math-7B-Instruct/"
# 1.5B 스모크: .../Qwen2.5-Math-1.5B-Instruct/
$env:SMOKE_PREDICT_TIMEOUT_SECONDS = "900"
$env:SMOKE_MAX_NEW_TOKENS = "8192"
python scripts/vertex/track_colab_vertex_smoke_seoul.py
```

### Vertex Custom Job (평가 프로세스까지 GCP에서)

로컬 노트북/PC에서 `eval_vertex_endpoint_quality.py`를 돌리지 않고, **Vertex Custom Job**으로 같은 스크립트를 실행할 수 있다. 컨테이너는 **CPU만** 쓰고(가중치 로드 없음), 추론은 기존과 동일하게 **배포된 엔드포인트**에 `predict`한다.

1. **데이터**: `numinamath_full.jsonl` 등 큰 파일은 **GCS에 올린 뒤** `--gcs-data-uri`로 넘긴다(컨테이너가 `/data`로 받고 `AIMO_DATA_DIR` 설정).
2. **이미지 빌드·푸시** (저장소 루트에서):

```powershell
docker build -f docker/vertex-eval/Dockerfile -t REGION-docker.pkg.dev/PROJECT/REPO/vertex-eval:latest .
docker push REGION-docker.pkg.dev/PROJECT/REPO/vertex-eval:latest
```

3. **잡 제출**:

```powershell
python scripts/vertex/submit_vertex_eval_job.py `
  --project YOUR_PROJECT --location asia-northeast3 `
  --staging-bucket gs://YOUR_BUCKET/vertex-staging `
  --container-image REGION-docker.pkg.dev/PROJECT/REPO/vertex-eval:latest `
  --endpoint-id YOUR_ENDPOINT_ID `
  --gcs-data-uri gs://YOUR_BUCKET/aimo/data/numinamath_full.jsonl `
  --gcs-output-uri gs://YOUR_BUCKET/aimo/results/vertex_eval.jsonl `
  --n-problems 200 --data-file numinamath_full.jsonl --difficulty-at-most medium
```

#### IAM (역할·주체)

권한은 **(A) 잡을 제출하는 주체**와 **(B) Custom Job 워커가 사용하는 서비스 계정**으로 나뉜다.

**(A) 제출자** (로컬 `gcloud`/ADC로 `submit_vertex_eval_job.py`를 실행하는 사용자 또는 CI SA)

| 필요 작업 | 권장 역할 (프로젝트 또는 리소스에 바인딩) |
|-----------|------------------------------------------|
| Custom Job 생성·제출 | `roles/aiplatform.user` (부족하면 `roles/aiplatform.admin`은 과함; 거부 시 `Custom Job` 생성 권한이 포함된 역할 확인) |
| 스테이징 버킷 `--staging-bucket` 에 잡 산출물 기록 | 해당 버킷에 `roles/storage.objectUser` 이상 (또는 프로젝트 `roles/storage.objectAdmin`) |

**(B) 워커 실행 SA** (`--service-account`로 지정; 생략 시 프로젝트 **기본 Compute Engine SA** `PROJECT_NUMBER-compute@developer.gserviceaccount.com` 등이 쓰일 수 있음 — 콘솔 Vertex Custom Job 상세에서 확인)

| 필요 작업 | 권장 |
|-----------|------|
| `DATA_GCS_URI` 객체 읽기 | 해당 버킷(또는 객체)에 `roles/storage.objectViewer` |
| `OUTPUT_GCS_URI` 객체 쓰기 | 해당 버킷에 `roles/storage.objectCreator` 또는 `roles/storage.objectUser` |
| `staging-bucket` 사용 시 쓰기 | 동일하게 해당 버킷에 객체 생성 권한 |
| 배포된 **엔드포인트**에 `predict` | 동일 프로젝트면 보통 `roles/aiplatform.user` (온라인 예측 포함). 최소 권한만 주려면 리소스 단위로 `aiplatform.endpoints.predict` 부여 |
| **Artifact Registry**에서 `--container-image` pull | 이미지가 있는 프로젝트/리포지토리에 `roles/artifactregistry.reader` (같은 프로젝트 기본 SA에 이미 있을 수 있음; 크로스 프로젝트면 필수) |

**한 줄 요약 (같은 프로젝트·같은 버킷으로 단순화할 때)**  
워커 SA에 `roles/aiplatform.user` + 데이터/결과/스테이징이 들어 있는 버킷에 대한 `roles/storage.objectAdmin` (또는 버킷 단위로 Viewer + Creator 분리).

**BigQuery 적재** (`eval_vertex_endpoint_quality.py` 의 `--bq-table`) 를 Custom Job 안에서 쓸 경우: 워커 SA에 `roles/bigquery.dataEditor` 및 (테이블 생성 시) `roles/bigquery.jobUser` 등이 추가로 필요하다.

완료 후 콘솔 **Vertex AI → Training → Custom jobs**에서 로그를 확인하고, `--gcs-output-uri`를 주었으면 결과 JSONL이 GCS에 올라간다.

---

## 3) 데이터 파일

기본은 `evaluation.config` 의 `numina_training_5k.jsonl` (또는 `AIMO_DATA_DIR` 아래).  
없으면 `prepare_qwen_numeric*` 등으로 만든 데이터와는 별개이므로, **파일이 있는지** 먼저 확인한다.

---

## 4) 스택 선택 이유

[WHY_THIS_VERTEX_STACK.md](./WHY_THIS_VERTEX_STACK.md) 참고.
