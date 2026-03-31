# 난이도별 목표 정확도 (Target Accuracy by Difficulty)

평가·벤치마크 해석 시 참고용 목표 구간입니다.

| 난이도 | 소스 예시 | 목표 정확도 |
|--------|-----------|-------------|
| **Easy** | Orca | 80–90% |
| **Medium** | K-12 | 60–70% |
| **Hard** | Olympiad | 30–40% |

코드에서 사용할 때는 `src.evaluation.config`의 상수를 사용하면 됩니다.

```python
from src.evaluation.config import (
    TARGET_ACCURACY_EASY,
    TARGET_ACCURACY_MEDIUM,
    TARGET_ACCURACY_HARD,
    TARGET_ACCURACY_BY_DIFFICULTY,
)
# TARGET_ACCURACY_EASY = (80, 90)
# TARGET_ACCURACY_BY_DIFFICULTY["easy"] 등
```

## Ralph 루프 (Cursor) — 완료 기준

- **기본 목표**: 전체 정확도 **≥ 80%** (`TARGET_ACCURACY_EASY` 하한과 동일). 변경: `AIMO_RALPH_TARGET_ACCURACY_PCT`.
- **검증**: `EvaluationMetrics.save_results` JSON에 대해 `python scripts/ralph_accuracy_gate.py <파일>` 이 종료 코드 0.
- **Easy만 볼 때**: `AIMO_RALPH_GATE_MODE=easy` (요약에 `by_difficulty.easy` 필요).
- **정확도 우선 실행**: `AIMO_OPTIMIZE_ACCURACY=1` → 투표 기본 활성, 후보 수 기본 4(환경으로 덮어쓰기 가능). `src/evaluation/ralph_accuracy.py` 참고.
