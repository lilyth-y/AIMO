# 1단계: 실제 `merged/` 아티팩트 준비·검증

Vertex 배포·품질 평가 전에 **HF 포맷 머지 디렉터리**가 있어야 한다. (스모크용 `tiny-gpt2`는 인프라 검증용이며, 숫자 품질 목적이면 **튜닝 머지**가 필요하다.)

## 1. 머지가 생기는 경로

| 경로 | 설명 |
|------|------|
| **학습(Custom Job)** | [VERTEX_TRAIN_DEPLOY_QWEN.md](./VERTEX_TRAIN_DEPLOY_QWEN.md) 에서 `--save-merged` → `gs://.../merged/` |
| **로컬에서 병합** | 베이스+어댑터를 HF 디렉터리로 저장한 폴더 |

상세: [MERGED_MODEL_ARTIFACT.md](./MERGED_MODEL_ARTIFACT.md)

## 2. 검증 명령 (레포 루트)

**로컬:**

```powershell
cd C:\startingup\AIMO
python scripts/vertex/verify_merged_artifact.py --local D:\path\to\merged
```

**GCS:**

```powershell
python scripts/vertex/verify_merged_artifact.py --gcs-uri gs://YOUR_BUCKET/aimo/models/qwen_numeric/merged/
```

- `[OK]`면 **1단계 통과**.
- `gcloud` 로그인·프로젝트·`storage` 권한이 있어야 GCS 검증이 된다.

## 3. 통과 후 바로 할 일 (선택)

로컬 경로가 `[OK]`이면 품질 스모크:

```powershell
python scripts/eval_hf_local_quality.py --model D:\path\to\merged --n-problems 10 --device auto
```

GCS만 있으면 먼저 로컬에 받아 동일하게 해도 되고, 엔드포인트 배포 후 [EVAL_REAL_MODEL.md](./EVAL_REAL_MODEL.md) 의 Vertex 평가로 넘어가도 된다.

## 4. 아직 머지가 없을 때

**Vertex에서 학습 + GCS 업로드까지 한 번에** 보려면 → **[MERGE_TRAIN_UPLOAD.md](./MERGE_TRAIN_UPLOAD.md)**.

요약만 보면:

1. JSONL 준비·GCS 업로드  
2. `vertex-train` 이미지 빌드·푸시  
3. `submit_vertex_custom_job.py ... --gcs-output gs://.../models/qwen_numeric --save-merged`  
4. 완료 후 `verify_merged_artifact.py --gcs-uri .../merged/`

또는 [VERTEX_TRAIN_DEPLOY_QWEN.md](./VERTEX_TRAIN_DEPLOY_QWEN.md) §3~4, Colab/로컬에서 머지 폴더만 만든 뒤 **수동 `gcloud storage cp -r`** 도 가능.

---

**다음 단계(2번)**: 품질 기준 수치(`strict_format`, `accuracy` 목표) 정하기 → [STEP2_QUALITY_GATES.md](./STEP2_QUALITY_GATES.md) (추가 예정 시 링크).
