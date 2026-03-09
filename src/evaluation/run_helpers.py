"""
Evaluation run helpers: gradient report + error summary after metrics.
Call after metrics.save_results() to save gradient and error summary alongside.
Includes git SHA for reproducibility (computing engine / artifact naming).
"""

import json
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from .config import PROJECT_ROOT, RESULTS_DIR, ensure_dir


def get_run_revision() -> Dict[str, Any]:
    """
    Return run revision for reproducibility (e.g. for computing engine, artifact naming).
    Uses git rev-parse HEAD and dirty flag if repo exists.
    """
    rev = {"sha": None, "short_sha": None, "dirty": False, "ref": None}
    try:
        root = Path(PROJECT_ROOT) if PROJECT_ROOT else Path.cwd()
        if not (root / ".git").exists():
            return rev
        rev["sha"] = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=5,
        ).strip()
        rev["short_sha"] = rev["sha"][:7] if rev["sha"] else None
        try:
            status = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=5,
            )
            rev["dirty"] = bool(status.stdout.strip())
        except Exception:
            pass
        try:
            rev["ref"] = subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=root,
                text=True,
                stderr=subprocess.DEVNULL,
                timeout=5,
            ).strip()
        except Exception:
            pass
    except Exception:
        pass
    return rev


def save_gradient_and_error_summary(
    metrics_dict: Dict[str, Any],
    results_list: Optional[List[Any]] = None,
    output_dir: Optional[Path] = None,
    dataset_name: str = "eval",
    filename: Optional[str] = None,
) -> str:
    """
    Compute mathematical + DevOps gradient report and optional error summary,
    save to output_dir. Returns path to saved file.

    metrics_dict: from metrics.calculate_metrics()
    results_list: optional list of EvaluationResult or dict with 'error' key
    """
    output_dir = Path(output_dir or RESULTS_DIR or PROJECT_ROOT / "results")
    try:
        ensure_dir(output_dir)
    except Exception:
        output_dir.mkdir(parents=True, exist_ok=True)

    run_rev = get_run_revision()
    out = {
        "dataset": dataset_name,
        "summary": metrics_dict.get("accuracy"),
        "total": metrics_dict.get("total"),
        "run_revision": run_rev,
    }

    # Gradient report
    try:
        from .mathematical_devops_gradients import evaluate_mathematical_and_devops
        gradient_report = evaluate_mathematical_and_devops(metrics_dict, project_root=PROJECT_ROOT)
        out["gradient"] = gradient_report
    except Exception as e:
        out["gradient"] = {"error": str(e)}

    # Error summary (if results with errors provided)
    if results_list:
        errors = []
        for r in results_list:
            if isinstance(r, dict):
                err = r.get("error")
            else:
                err = getattr(r, "error", None)
            if err:
                errors.append({"error": err[:500] if isinstance(err, str) else str(err)[:500]})
        if errors:
            try:
                from .advanced_metrics import ErrorCategorizer
                out["error_summary"] = ErrorCategorizer.analyze_error_patterns(errors)
            except Exception as e:
                out["error_summary"] = {"total_errors": len(errors), "categorize_error": str(e)}

    if filename is None:
        from datetime import datetime
        short = (run_rev.get("short_sha") or "norev") + ("-dirty" if run_rev.get("dirty") else "")
        filename = f"gradient_report_{dataset_name}_{short}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    path = output_dir / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    return str(path)


def print_gradient_summary(metrics_dict: Dict[str, Any]) -> None:
    """Print a short gradient summary to console."""
    try:
        from .mathematical_devops_gradients import evaluate_mathematical_and_devops
        r = evaluate_mathematical_and_devops(metrics_dict)
        print("\n[Gradient] Math:", r["mathematical"]["score"], r["mathematical"]["level"],
              "| DevOps:", r["devops"]["score"], r["devops"]["level"])
    except Exception as e:
        print("\n[Gradient] (skip)", e)
