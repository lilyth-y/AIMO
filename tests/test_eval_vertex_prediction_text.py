"""eval_vertex_endpoint_quality._prediction_text extraction (no Vertex SDK calls)."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_eval_module():
    root = Path(__file__).resolve().parents[1]
    p = root / "scripts" / "vertex" / "eval_vertex_endpoint_quality.py"
    name = "eval_vertex_endpoint_quality"
    spec = importlib.util.spec_from_file_location(name, p)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_prediction_text_plain_dict():
    m = _load_eval_module()
    assert m._prediction_text({"text": "  hello  "}) == "hello"


def test_prediction_text_nested_openai_style():
    m = _load_eval_module()
    raw = {"choices": [{"message": {"content": "<ANS>42</ANS>"}}]}
    assert "42" in m._prediction_text(raw) or "<ANS>" in m._prediction_text(raw)


def test_prediction_text_json_string():
    m = _load_eval_module()
    s = '{"text": "<ANS>3</ANS>"}'
    out = m._prediction_text(s)
    assert "3" in out or "<ANS>" in out


def test_prediction_text_longest_string_fallback():
    m = _load_eval_module()
    raw = {"meta": "x", "payload": "the full model completion here"}
    assert "completion" in m._prediction_text(raw)
