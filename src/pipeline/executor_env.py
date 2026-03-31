"""
Single source of truth for code executor wall-clock default (seconds).

Precedence (first set wins):
  AIMO_EXECUTOR_WALL_TIME_SEC → AIMO_EXECUTOR_TIMEOUT_SEC → OMI_EXECUTOR_TIMEOUT

If none are set, wall-clock execution is unlimited (float('inf')).
If a variable is set to 0 or a negative value, that also means unlimited.

Any positive finite value caps wall time for that run.
"""

from __future__ import annotations

import os


def executor_wall_seconds_from_env() -> float:
    for key in ("AIMO_EXECUTOR_WALL_TIME_SEC", "AIMO_EXECUTOR_TIMEOUT_SEC", "OMI_EXECUTOR_TIMEOUT"):
        raw = os.getenv(key)
        if raw is not None and str(raw).strip() != "":
            val = float(raw)
            if val <= 0:
                return float("inf")
            return val
    return float("inf")
