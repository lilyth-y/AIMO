# 2단계: 품질 기준(게이트) 정하기

이 문서는 Vertex 배포 전 **Go/No-Go 판정 기준**을 고정한다.

## 측정 도구

- 로컬 측정: `scripts/eval_hf_local_quality.py`
- Vertex 측정: `scripts/vertex/eval_vertex_endpoint_quality.py`

## 고정 임계값 (필수)

샘플 수와 기준을 같이 충족해야 통과한다.

- 샘플 수: `n-problems >= 50` (권장 100)
- `strict_format_rate >= 0.98`
- `accuracy >= 0.20`
- `predicted_null_rate <= 0.20`
- API 오류 비율 <= `0.05`: `(api_error + verify_api_error) / n_problems` (`--enforce-gates` 집계와 동일)

## 실행 예시

```bash
python scripts/vertex/eval_vertex_endpoint_quality.py \
  --endpoint-id <ENDPOINT_ID> \
  --project <PROJECT_ID> \
  --location <LOCATION> \
  --n-problems 50 \
  --enforce-gates
```

`--enforce-gates` 를 쓰면 위 임계값을 만족하지 않을 때 **프로세스 exit code 2**로 종료한다 (CI 연동용).

## 판정 규칙

- PASS: 모든 임계값 충족
- FAIL: 하나라도 미충족

## FAIL 시 조치 순서

1. `strict_format_rate` 미달: 프롬프트/형식 게이트 옵션(`--max-format-retries`) 점검 후 재평가
2. `accuracy` 미달: 데이터 품질/학습 파라미터 재점검 후 재학습
3. `api_error`·`verify_api_error`(합산 비율) 또는 `predicted_null_rate` 과다: 타임아웃·머신타입·서빙 컨테이너 로그 점검
4. 배포 유지가 부적절하면 엔드포인트 undeploy/delete 후 재시도

1단계: [STEP1_MERGED_ARTIFACT.md](./STEP1_MERGED_ARTIFACT.md)
