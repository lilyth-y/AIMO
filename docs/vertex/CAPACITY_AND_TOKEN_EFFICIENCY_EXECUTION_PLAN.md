# Capacity 신청 체크리스트 + Token 효율화 최소 패치 실행안

본 문서는 `429 RESOURCE_EXHAUSTED` 빈발과 문제당 평균 지연 시간 증가를 동시에 낮추기 위한
실행 가능한 운영/코드 절차를 정리한다.

## 1) Capacity 신청 체크리스트 (운영)

- [ ] 현재 기준선 수집: 최근 평가 로그에서 `429 비율`, `평균/중앙/p90 지연`, `문제당 LLM 호출 수`를 추출
- [ ] 지역별 비교 데이터 준비: 동일 설정으로 `us-central1`, `us-east5` 최소 3문항 smoke 비교
- [ ] 서비스/모델 식별: `aiplatform.googleapis.com` 기준, 실제 호출 모델(엔드포인트/퍼블리셔)을 명시
- [ ] Quota 증설 요청 초안 작성:
  - 현재 한도(요청/분, 토큰/분, 동시성 관련 항목)
  - 피크 시간대와 관측 실패율(429)
  - 요청 증설량(예: 2x 또는 3x)과 근거(평균 지연/재시도 감소 목표)
- [ ] 승인 전 임시 완화책 적용 여부 확인:
  - 재시도 상한
  - 문제당 호출 cap
  - rate-limit 모드(고비용 경로 비활성)
- [ ] 승인 후 재평가 계획 준비: 동일 벤치마크/동일 하이퍼파라미터로 전후 비교

## 2) Token 효율화 최소 패치 (코드)

이번 최소 패치의 목적은 구조를 크게 바꾸지 않고 호출 폭주를 먼저 차단하는 것이다.

### 적용 항목

1. 문제당 LLM 호출 cap
   - 환경변수: `AIMO_LLM_CALL_CAP_PER_PROBLEM` (기본 12)
   - cap 초과 시 즉시 에러 문자열 반환하여 추가 호출 확산 방지

2. 429 감지 플래그
   - LLM 클라이언트가 응답 텍스트에서 `429`/`RESOURCE_EXHAUSTED`를 감지하면
     현재 solve 범위에서 `last_rate_limited=True`로 유지

3. rate-limit 시 multi-agent 우회
   - early multi-agent 및 최후 multi-agent fallback을 건너뜀
   - 목적: 429가 발생한 문제에서 고비용 다중 호출 경로를 추가로 열지 않음

## 3) 실행 순서 (실험당 변수 1개)

아래 순서는 반드시 **한 실험에 한 변수만 변경** 원칙을 따른다.

### Step A. 코드 정상 실행 확인 (Tier 1)

- 변경: 없음 (현재 패치 상태)
- 실행: 1~3문항 smoke
- 성공 기준:
  - 실행 중 예외 없음
  - cap 초과/429 시 graceful fallback 동작

### Step B. cap 민감도 소규모 평가 (Tier 2)

- 변경 변수: `AIMO_LLM_CALL_CAP_PER_PROBLEM`만 변경
  - 실험군 예시: `10`, `12`, `14`
- 고정: 모델/region/문항셋/기타 하이퍼파라미터
- 성공 기준:
  - 429 비율 감소 또는 동일 수준 유지
  - 평균 지연 증가 없는지 확인

### Step C. region 비교 (Tier 2)

- 변경 변수: `GOOGLE_CLOUD_LOCATION`만 변경
  - 실험군: `us-central1` vs `us-east5`
- 고정: cap 값, 문항셋, 모델
- 성공 기준:
  - 429 비율 및 p90 지연의 우세 region 식별

### Step D. capacity 증설 전/후 본평가 (Tier 3)

- 변경 변수: capacity(할당량)만 변경
- 고정: 코드/모델/데이터셋/평가 스크립트
- 기록 항목:
  - 정확도
  - 평균/중앙/p90/p99 지연
  - 429 비율
  - 문제당 평균 호출 수

## 4) 리스크와 반례 체크

- cap이 너무 낮으면 정답률이 하락할 수 있음
- region 변경만으로 429가 항상 해결되지는 않음 (시간대/공유 사용량 영향)
- token 상한만 줄이면 오히려 재시도 증가로 총 호출이 늘어날 수 있음
- 따라서 `호출 수`와 `429`, `지연`을 함께 모니터링해야 함

## 5) 즉시 실행 권장 기본값

- `AIMO_LLM_CALL_CAP_PER_PROBLEM=10` (현재 샘플 기준 latency/429 균형점)
- region 우선순위: `us-east5` -> `us-central1`
- multi-agent는 자동 조건부 사용 (429 감지 시 우회)
- smoke -> 소규모 비교 -> 본평가 순서 유지

## 6) 최신 실험 스냅샷 (2026-04-07)

동일 스크립트: `examples/run_numina_evaluation.py`

| Run | Region | Cap | Problems | Accuracy | Avg solve(s) | Total(s) | Rate-limited events |
|---|---|---:|---:|---:|---:|---:|---:|
| Tier1 smoke | us-central1 | 12 | 1 | 0.00% | 69.47 | 69.48 | 2 |
| Tier2 cap test | us-central1 | 10 | 3 | 0.00% | 168.22 | 504.68 | 11 |
| Tier2 cap test | us-central1 | 12 | 3 | 0.00% | 637.25 | 1911.75 | 29 |
| Tier2 region test | us-east5 | 10 | 3 | 33.33% | 93.62 | 280.88 | 0 |

추가 관찰:

- `cap=14` 실험은 2회 모두 비정상 종료/중단
  - 1차: 네트워크 오류(DNS/connection) 혼입
  - 2차: timeout 누적 및 장시간 지연
- 샘플 기준으로는 `cap=12`가 `cap=10` 대비 명확히 느렸고, 429도 증가했다.

