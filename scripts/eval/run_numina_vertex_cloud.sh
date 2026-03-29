#!/usr/bin/env bash
# Numina 평가 on cloud (Vertex Gemini). Can run from any cwd — script jumps to repo root.
# See docs/run-eval/CLOUD_NUMINA_RUN.md (must clone repo so this file exists).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

if [[ ! -f "$ROOT/requirements.txt" ]]; then
  echo "ERROR: requirements.txt not found under $ROOT"
  echo "Clone this repo and run: cd /path/to/AIMO && bash scripts/eval/run_numina_vertex_cloud.sh"
  exit 1
fi

export GOOGLE_CLOUD_PROJECT="${GOOGLE_CLOUD_PROJECT:-gen-lang-client-0300734101}"
export GOOGLE_CLOUD_LOCATION="${GOOGLE_CLOUD_LOCATION:-us-central1}"
export AIMO_EVAL_IN_PROCESS="${AIMO_EVAL_IN_PROCESS:-1}"
export MAX_PROBLEMS="${MAX_PROBLEMS:-50}"

echo "GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT"
echo "GOOGLE_CLOUD_LOCATION=$GOOGLE_CLOUD_LOCATION"
echo "MAX_PROBLEMS=$MAX_PROBLEMS"
echo "Starting: python examples/run_numina_evaluation.py --data-file numina_eval_balanced.json"
echo "(Ensure ADC or GOOGLE_GENAI_API_KEY is set — see docs/run-eval/VERTEX_AI.md)"

python examples/run_numina_evaluation.py --data-file numina_eval_balanced.json
