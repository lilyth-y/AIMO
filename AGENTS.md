# AGENTS.md

## Cursor Cloud specific instructions

### Project overview

OMI (Orchestrated Math Interpreter) is an AI math-problem-solving pipeline. See `README.md` for full docs. The core is a Python project under `src/` with a 5-stage pipeline (analysis → retrieval → routing → execution → verification).

### Running tests

```bash
AIMO_FAST_TEST=1 PYTHONPATH=src pytest tests/ -q --tb=short
```

- `AIMO_FAST_TEST=1` enables mock mode — no ML model downloads, no GPU needed. Always use this for CI and quick checks.
- `PYTHONPATH=src` is required for all imports to resolve.
- 9 tests are expected to be skipped (they require real inference or GPU).

### Lint checks (CI parity)

The CI runs import-based lint checks (not a traditional linter like flake8/ruff). Replicate with:

```bash
python3 -c "import sys; sys.path.insert(0, 'src'); from evaluation.evaluation_utils import EvaluationMetrics, check_answer_correctness; from evaluation.config import PROJECT_ROOT; print('evaluation OK')"
python3 -c "import sys; sys.path.insert(0, 'src'); from pipeline.config import HF_MODEL_NAME; print('pipeline config OK')"
```

### Running the FastAPI service

```bash
AIMO_FAST_TEST=1 PYTHONPATH=src uvicorn src.service.cloud_run_api:app --host 0.0.0.0 --port 8080
```

- Health check: `GET /health` → `{"status":"ok"}`
- Solve endpoint: `POST /solve` with JSON body `{"problem_text": "...", "time_budget": 60.0}`
- In mock mode (`AIMO_FAST_TEST=1`), the solver returns `"0"` for all problems — this is expected.
- Requires `fastapi` and `uvicorn[standard]` (install with `pip install fastapi 'uvicorn[standard]'`).

### Ralph accuracy gate

```bash
python3 scripts/ralph_accuracy_gate.py tests/fixtures/ralph_gate_pass.json
```

The fixture file is a known-pass case (85%). The tier-3 smoke test (`scripts/ralph_tier3_numina_smoke.py`) runs an eval in mock mode and expects the gate to FAIL (0% accuracy in mock mode is correct).

### Key environment variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `AIMO_FAST_TEST=1` | Mock solver mode, no model download | `0` |
| `PYTHONPATH=src` | Required for imports | not set |
| `OMI_MODEL` / `AIMO_MODEL` | HuggingFace model repo ID | `Qwen/Qwen2.5-Math-7B-Instruct` |
| `OMI_QUANTIZATION` / `AIMO_QUANTIZATION` | Quantization level | `8bit` |

### Gotchas

- The system Python is `python3`, not `python`. Use `python3` explicitly.
- pip installs to `~/.local/bin` which may not be on PATH. Ensure `export PATH="$HOME/.local/bin:$PATH"` if commands like `pytest` are not found.
- The `dashboard/` directory contains a Vite+React app with `node_modules` already committed; it is a presentation dashboard and not required for core development.
- All settings are centralized in `src/pipeline/settings.py` with env-var overrides.
