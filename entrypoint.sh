#!/bin/sh
set -e
MODE="$1"
if [ -z "$MODE" ]; then
  MODE="test"
fi
case "$MODE" in
  test)
    echo "[ENTRYPOINT] Running solver smoke test"
    exec python test_solver.py
    ;;
  eval)
    echo "[ENTRYPOINT] Running Numina evaluation (balanced subset)"
    exec python run_numina_evaluation.py
    ;;
  aimo)
    echo "[ENTRYPOINT] Running AIMO reference problem evaluation (5 IMO-level problems)"
    exec python run_aimo_evaluation.py
    ;;
  shell)
    echo "[ENTRYPOINT] Dropping to shell"
    exec /bin/sh
    ;;
  *)
    echo "[ENTRYPOINT] Treating argument as python target: $MODE"
    exec python "$MODE"
    ;;
esac
