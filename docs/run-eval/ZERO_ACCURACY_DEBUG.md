# 0% 정확도(전부 오답)일 때 점검 사항

60문항 평가에서 **정답이 하나도 없을 때** 의심할 수 있는 원인과 대응입니다.

## 1. 진단 출력 확인

평가가 끝나고 정확도가 0%이면 스크립트가 자동으로 **DIAGNOSTIC** 블록을 출력합니다.

- **Sample: first 3 problems [reference vs predicted]**  
  → 참조 답(`ref`)과 모델이 준 답(`pred`)이 어떻게 다른지 확인하세요.
- **All predicted answers are None**  
  → 파이프라인 전체가 실패하고 있습니다(모델 미로드, 타임아웃, 실행기 실패 등).
- **All predicted are N/A or empty**  
  → 모델은 돌았지만 답 추출이 되지 않았거나, 오케스트레이터가 `answer`를 비워서 반환하고 있습니다.

## 2. 가능한 원인과 대응

### (1) 모델이 로드되지 않음 (Kaggle/로컬)

- **증상**: `pred`가 전부 `None` 또는 빈 문자열, `method`가 `all_failed` 등.
- **확인**:
  - Kaggle: Settings → **Accelerator: GPU**, **Internet: On** (HuggingFace에서 모델 다운로드).
  - `OMI_MODEL`이 올바른지 확인 (로컬 경로 또는 `Qwen/Qwen2.5-Math-1.5B-Instruct` 등).
- **대응**: GPU 켜기, 인터넷 켜기, 또는 Dataset으로 모델 미리 올려 두고 `OMI_MODEL`을 해당 경로로 설정.

### (2) 타임아웃으로 전부 실패

- **증상**: `method == 'timeout'`, `pred`가 `None`.
- **확인**: `EVAL_PROBLEM_TIMEOUT`(기본 900초)이 너무 짧으면 모든 문제가 타임아웃될 수 있음.
- **대응**: 타임아웃 늘리기, 또는 `MAX_PROBLEMS=5`로 소량만 돌려서 한 문제라도 답이 나오는지 확인.

### (3) 참조 답 형식 불일치

- **증상**: `ref`와 `pred`가 눈으로 보기에 같은 값인데 정답 처리되지 않음.
- **원인**: 데이터셋의 `answer` 필드가 리스트/딕셔너리이거나, LaTeX/문자열 형식이 평가기의 `normalize_answer`·SymPy 해석과 맞지 않음.
- **확인**: `numina_eval_balanced.json`의 첫 몇 개 항목에서 `answer`가 문자열인지, `\frac{1}{2}` vs `0.5` 같은 형식 차이가 있는지 확인.
- **대응**: 데이터 생성 시 `create_evaluation_set`에서 저장하는 항목이 `problem`, `answer`, `source`를 문자열로 갖는지 확인. 필요하면 참조 답만 사전 정규화해 저장.

### (4) SymPy 미설치 또는 버전 이슈

- **증상**: 수식 등가 비교(예: `1/2` vs `0.5`)가 실패해 정답이 틀리게 나옴.
- **확인**: 진단 블록에 `SymPy: NOT available` 이면 SymPy가 없음.
- **대응**: `pip install sympy` 후 재실행. Kaggle에서는 `requirements-kaggle.txt`에 sympy가 포함되어 있는지 확인.

### (5) 코드 실행 실패(샌드박스/환경)

- **증상**: `method`가 `all_failed`, 실행 결과에 `Error`/`SyntaxError` 등.
- **원인**: 생성된 코드가 Kaggle/로컬 환경에서 실행되지 않음(금지된 모듈, 메모리 부족 등).
- **대응**: 로그에서 `execution_result` 또는 `error` 필드 확인. 필요하면 로컬에서 소수 문항만 실행해 어떤 코드가 실패하는지 확인.

### (6) 답 추출 실패

- **증상**: `pred`가 `N/A` 또는 빈 문자열인데, 로그 상으로는 모델 출력/실행 결과에 답이 있음.
- **원인**: `<ANS>...</ANS>`, `\boxed{}`, 마지막 숫자 등 추출 규칙이 해당 출력 형식과 맞지 않음.
- **대응**: `src/pipeline/answer_extraction.py`, `reasoning_utils.extract_answer` / `extract_final_answer_from_output`에서 실제 모델 출력 샘플로 패턴 확인 및 폴백 추가.

## 3. 빠른 확인용(5문항)

원인 좁히기 위해 5문항만 돌려보기:

```bash
MAX_PROBLEMS=5 python examples/run_numina_evaluation.py
```

또는 Kaggle 노트북에서:

```python
import os
os.environ["MAX_PROBLEMS"] = "5"
# 그 다음 평가 셀 실행
```

한 문제라도 정답이 나오면 파이프라인·모델은 동작하는 것이므로, 0%는 **데이터 형식**, **타임아웃**, **특정 난이도/소스**에서만 실패하는지 등으로 범위를 줄일 수 있습니다.

## 4. 결과 파일로 상세 확인

저장된 `results/numina_balanced_results.json`(또는 gradient 리포트)에서 다음을 확인할 수 있습니다.

- `predicted_answer`, `reference_answer`, `is_correct`, `method`, `error` per problem.
- `by_difficulty` 등으로 난이도별 정확도: 전부 0%인지, 특정 난이도만 0%인지 구분.

이 문서는 `docs/run-eval/KAGGLE_ENV_CHECK.md` 및 평가 스크립트의 0% 진단 출력과 함께 사용하면 됩니다.

---

## 5. 데이터 형식이 결과(정답 판정)에 미치는 영향

**질문:** 데이터 형식에 따라 답이 달라지는지, 결과물에 이상이 있는 건지?

**요약:** 네. **참조 답(reference_answer)과 예측 답(predicted_answer)의 형식**이 정규화·비교 단계를 거치므로, 데이터 형식이 정답 판정과 결과물에 영향을 줍니다.

| 원인 | 설명 |
|------|------|
| **참조 답 형식** | 데이터셋의 `answer` 필드가 문자열이 아니거나(예: 리스트·딕셔너리), `"1/2"` vs `"0.5"` vs `"\\frac{1}{2}"` 처럼 표현만 다르면, `normalize_answer()`·SymPy 전에 문자열로 통일되지 않으면 오답 처리될 수 있음. |
| **예측 답 형식** | 파이프라인이 추출한 값이 `"42"` vs `42`(숫자) vs `"42.0"` 이면 정규화 후에는 보통 같게 보지만, LaTeX·분수 등은 SymPy 등가 비교에 의존함. SymPy 미설치/실패 시 문자열 비교만 하므로 형식 차이로 오답이 될 수 있음. |
| **데이터 소스별 차이** | `numina_eval_balanced.json`(JSON 배열)과 JSONL(한 줄 한 항목)은 **로드 방식만 다름**. 항목 구조가 `problem`, `answer`, `source`를 문자열로 갖는지가 중요함. JSONL에서 `answer`가 없고 `solution`만 있으면 참조 답이 비어 0%로 이어질 수 있음. |

**결과물 이상인지 확인하는 방법**

1. **DIAGNOSTIC 출력** (0%일 때): `ref` vs `pred` 샘플을 보고, 같은 값인데 오답이면 형식/정규화 이슈 가능.
2. **저장된 결과 JSON**: `reference_answer`, `predicted_answer`, `is_correct`를 문항별로 확인. `ref`와 `pred`가 수학적으로 같은데 `is_correct: false`면 정규화·SymPy 이슈.
3. **데이터 파일 점검**: 사용한 JSON/JSONL의 한두 항목에서 `answer`(또는 사용한 필드)가 **문자열**인지, LaTeX/분수인 경우 동일 데이터로 `check_answer_correctness(ref, pred)`를 직접 호출해 보기.

정리: **데이터 형식(필드 이름·타입·수학 표현)이 정답 판정과 결과에 영향을 주므로**, 0%나 의심스러운 정확도일 때는 위 항목을 확인하면 “형식 때문인지” vs “모델/파이프라인 오류인지”를 구분할 수 있습니다.
