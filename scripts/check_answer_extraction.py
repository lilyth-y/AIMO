"""Quick sanity check for answer extraction (reasoning_utils)."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from pipeline.reasoning_utils import (
    extract_answer,
    normalize_multi_agent_answer,
    _extract_answer_from_long_text,
    _is_placeholder_ans,
)

# 1) Placeholder ANS rejected
ans_placeholder = "<ANS>ONLY compact canonical form.</ANS>"
out1 = extract_answer(ans_placeholder)
print("1) Placeholder ANS ->", repr(out1))
assert out1 is None or (out1 and "canonical" not in out1.lower()), "Placeholder should be rejected"

# 2) Normal ANS
ans_ok = r"<ANS>\frac{1}{6}</ANS>"
out2 = extract_answer(ans_ok)
print("2) Normal ANS ->", repr(out2))

# 3) Long text -> number
long_blob = """선택: 1
이유: good
최종 답안: 302
"""
out3 = normalize_multi_agent_answer(long_blob)
print("3) Long text (최종 답안: 302) ->", repr(out3))
assert out3 == "302" or "302" in str(out3), "Should extract 302"

# 4) Dialogue-style string
dialogue = "some role content ... 최종 답안: 42"
out4 = normalize_multi_agent_answer(dialogue)
print("4) Dialogue with 42 ->", repr(out4))

print("OK - extraction logic works.")
