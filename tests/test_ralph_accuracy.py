import json
import os

import pytest

from src.evaluation.ralph_accuracy import (
    evaluate_gate_from_saved_dict,
    evaluate_vertex_summary_for_ralph,
    meets_ralph_target,
    ralph_target_accuracy_pct,
    vertex_summary_accuracy_to_observed_pct,
)


def test_meets_target_default_80():
    assert meets_ralph_target(80.0)
    assert meets_ralph_target(100.0)
    assert not meets_ralph_target(79.9)


def test_target_from_env(monkeypatch):
    monkeypatch.setenv("AIMO_RALPH_TARGET_ACCURACY_PCT", "85")
    assert ralph_target_accuracy_pct() == 85.0


def test_gate_overall_pass(tmp_path, monkeypatch):
    monkeypatch.delenv("AIMO_RALPH_GATE_MODE", raising=False)
    monkeypatch.setenv("AIMO_RALPH_TARGET_ACCURACY_PCT", "50")
    data = {"summary": {"accuracy": 60.0, "total": 10, "correct": 6}}
    ok, msg, obs, tgt = evaluate_gate_from_saved_dict(data)
    assert ok
    assert "60" in msg or "60.00" in msg
    assert obs == 60.0
    assert tgt == 50.0


def test_gate_easy_fail_missing_bucket(monkeypatch):
    monkeypatch.setenv("AIMO_RALPH_GATE_MODE", "easy")
    monkeypatch.setenv("AIMO_RALPH_TARGET_ACCURACY_PCT", "50")
    data = {"summary": {"accuracy": 90.0, "by_difficulty": {}}}
    with pytest.raises(ValueError):
        evaluate_gate_from_saved_dict(data)


def test_gate_easy_pass(monkeypatch):
    monkeypatch.setenv("AIMO_RALPH_GATE_MODE", "easy")
    monkeypatch.setenv("AIMO_RALPH_TARGET_ACCURACY_PCT", "70")
    data = {
        "summary": {
            "accuracy": 40.0,
            "by_difficulty": {"easy": {"total": 10, "correct": 8, "accuracy": 80.0}},
        }
    }
    ok, msg, obs, tgt = evaluate_gate_from_saved_dict(data)
    assert ok
    assert obs == 80.0


def test_vertex_summary_fraction_to_pct():
    pct, _ = vertex_summary_accuracy_to_observed_pct({"accuracy": 0.8})
    assert abs(pct - 80.0) < 1e-6


def test_vertex_evaluate_ralph_pass(monkeypatch):
    monkeypatch.setenv("AIMO_RALPH_TARGET_ACCURACY_PCT", "80")
    ok, msg, obs, tgt = evaluate_vertex_summary_for_ralph({"accuracy": 0.85, "n_problems": 10})
    assert ok and obs == 85.0 and tgt == 80.0
    assert "PASS" in msg


def test_vertex_evaluate_ralph_fail(monkeypatch):
    monkeypatch.setenv("AIMO_RALPH_TARGET_ACCURACY_PCT", "80")
    ok, _, _, _ = evaluate_vertex_summary_for_ralph({"accuracy": 0.79})
    assert not ok


def test_cli_json_roundtrip(tmp_path):
    p = tmp_path / "m.json"
    p.write_text(
        json.dumps({"summary": {"accuracy": 81.0, "correct": 81, "total": 100}}, ensure_ascii=False),
        encoding="utf-8",
    )
    import subprocess
    import sys

    r = subprocess.run(
        [sys.executable, "scripts/ralph_accuracy_gate.py", str(p)],
        cwd=os.path.dirname(os.path.dirname(__file__)),
        capture_output=True,
        text=True,
        env={**os.environ, "AIMO_RALPH_TARGET_ACCURACY_PCT": "80"},
    )
    assert r.returncode == 0, r.stderr + r.stdout
