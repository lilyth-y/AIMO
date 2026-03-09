"""
Mathematical & DevOps Gradient Evaluation

- Mathematical: difficulty gradient metrics, rigor (CI, effect size), domain-wise accuracy.
- DevOps: reproducibility score, CI/CD readiness, deployment readiness (maturity gradients).
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
import os
import json
from pathlib import Path


# --- Mathematical gradient levels (difficulty / rigor) ---

@dataclass
class MathematicalGradientLevel:
    """Single level in the mathematical evaluation gradient."""
    name: str
    score_min: float
    score_max: float
    description: str
    metrics_included: List[str]


MATHEMATICAL_GRADIENT_LEVELS = [
    MathematicalGradientLevel("L1_Basic", 0.0, 0.35, "기본 정확도만 보고", ["accuracy"]),
    MathematicalGradientLevel("L2_Stratified", 0.35, 0.55, "난이도/소스별 분해 및 기본 통계", ["accuracy", "by_difficulty", "by_source"]),
    MathematicalGradientLevel("L3_Statistical", 0.55, 0.75, "신뢰구간, 검정, 오류 분류", ["accuracy_ci", "mcnemar", "error_categorization"]),
    MathematicalGradientLevel("L4_Rigor", 0.75, 0.90, "난이도 구간별 정확도, 효과크기, 정량적 난이도", ["accuracy_by_quantile", "effect_size", "difficulty_score"]),
    MathematicalGradientLevel("L5_Full", 0.90, 1.01, "수학적 완전성: 모든 메트릭 + 도메인별 분석", ["all", "domain_accuracy", "rigor_report"]),
]


@dataclass
class DevOpsGradientLevel:
    """Single level in the DevOps maturity gradient."""
    name: str
    score_min: float
    score_max: float
    description: str
    checks: List[str]


DEVOPS_GRADIENT_LEVELS = [
    DevOpsGradientLevel("D1_AdHoc", 0.0, 0.25, "수동 실행, 문서만 존재", ["readme", "requirements"]),
    DevOpsGradientLevel("D2_Reproducible", 0.25, 0.50, "고정 환경으로 재현 가능", ["docker", "compose", "pinned_versions"]),
    DevOpsGradientLevel("D3_Automated", 0.50, 0.75, "CI/테스트 자동화", ["ci_yml", "tests_runner", "artifacts"]),
    DevOpsGradientLevel("D4_DeployReady", 0.75, 0.90, "배포·모니터링 준비", ["entrypoint", "healthcheck", "resource_limits"]),
    DevOpsGradientLevel("D5_Production", 0.90, 1.01, "프로덕션 수준 파이프라인", ["logging", "metrics_export", "secrets"]),
]


def _score_math_capabilities(metrics: Dict[str, Any]) -> Tuple[float, str, List[str]]:
    """
    Compute mathematical evaluation gradient score (0–1) from available metrics.
    Returns (score, level_name, list of satisfied criteria).
    """
    score = 0.0
    satisfied = []
    # L1: accuracy present
    if metrics.get("accuracy") is not None or metrics.get("total") is not None:
        score += 0.2
        satisfied.append("accuracy")
    # L2: by_difficulty / by_source
    if metrics.get("by_difficulty"):
        score += 0.15
        satisfied.append("by_difficulty")
    if metrics.get("by_source"):
        score += 0.1
        satisfied.append("by_source")
    # L3: confidence interval / error analysis
    if metrics.get("accuracy_ci") or metrics.get("confidence_interval"):
        score += 0.15
        satisfied.append("accuracy_ci")
    if metrics.get("error_types") or metrics.get("error_rate_by_category"):
        score += 0.1
        satisfied.append("error_categorization")
    # L4: quantile / effect size / difficulty score
    if metrics.get("accuracy_by_quantile"):
        score += 0.1
        satisfied.append("accuracy_by_quantile")
    if metrics.get("effect_size") is not None:
        score += 0.05
        satisfied.append("effect_size")
    if metrics.get("difficulty_score") or metrics.get("by_difficulty_score"):
        score += 0.05
        satisfied.append("difficulty_score")
    # L5: domain breakdown / full report
    if metrics.get("by_domain") or metrics.get("domain_accuracy"):
        score += 0.05
        satisfied.append("domain_accuracy")
    if "rigor_report" in str(metrics).lower() or metrics.get("report_path"):
        score += 0.05
        satisfied.append("rigor_report")
    return min(1.0, score), _gradient_level_name(score, MATHEMATICAL_GRADIENT_LEVELS), satisfied


def _score_devops_capabilities(project_root: Optional[Path] = None) -> Tuple[float, str, List[str]]:
    """
    Compute DevOps maturity gradient score (0–1) from repo structure and config.
    Returns (score, level_name, list of satisfied checks).
    """
    root = Path(project_root or Path(__file__).resolve().parent.parent.parent)
    score = 0.0
    satisfied = []
    # D1
    if (root / "README.md").exists():
        score += 0.1
        satisfied.append("readme")
    if (root / "requirements.txt").exists():
        score += 0.1
        satisfied.append("requirements")
    # D2
    if (root / "Dockerfile").exists():
        score += 0.15
        satisfied.append("docker")
    if (root / "compose.yml").exists() or (root / "docker-compose.yml").exists():
        score += 0.1
        satisfied.append("compose")
    # pinned versions in requirements (heuristic: has ==)
    req_file = root / "requirements.txt"
    if req_file.exists():
        try:
            text = req_file.read_text(encoding="utf-8", errors="ignore")
            if "==" in text:
                score += 0.05
                satisfied.append("pinned_versions")
        except Exception:
            pass
    # D3
    ci_dir = root / ".github" / "workflows"
    if ci_dir.exists() and list(ci_dir.glob("*.yml")) or list(ci_dir.glob("*.yaml")):
        score += 0.2
        satisfied.append("ci_yml")
    tests_dir = root / "tests"
    if tests_dir.exists() and list(tests_dir.glob("*.py")):
        score += 0.1
        satisfied.append("tests_runner")
    # D4
    ep = root / "entrypoint.sh"
    if ep.exists():
        score += 0.05
        satisfied.append("entrypoint")
    compose_path = root / "compose.yml"
    if compose_path.exists():
        try:
            content = compose_path.read_text(encoding="utf-8", errors="ignore")
            if "limits:" in content or "memory:" in content or "cpus:" in content:
                score += 0.05
                satisfied.append("resource_limits")
        except Exception:
            pass
    # D5
    if (root / "logs").exists() or "logs" in str(root):
        score += 0.02
    if any((root / "src").rglob("logger*.py")) or "logging" in str(root):
        score += 0.03
        satisfied.append("logging")
    return min(1.0, score), _gradient_level_name(score, DEVOPS_GRADIENT_LEVELS), satisfied


def _gradient_level_name(score: float, levels: List[Any]) -> str:
    """Resolve level name from score; levels have score_min, score_max, name."""
    for lev in levels:
        if lev.score_min <= score < lev.score_max:
            return lev.name
    return levels[-1].name if levels else "Unknown"


def compute_difficulty_gradient(
    by_difficulty: Dict[str, Any],
    difficulty_order: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Compute gradient of accuracy across difficulty levels (easy -> hard).
    Returns trend and per-level stats for mathematical evaluation.
    """
    if difficulty_order is None:
        difficulty_order = ["easy", "medium", "hard", "olympiad"]
    ordered = [d for d in difficulty_order if d in (by_difficulty or {})]
    if not ordered:
        return {"levels": [], "gradient_trend": "unknown", "accuracy_gradient": []}
    accuracies = []
    for d in ordered:
        st = by_difficulty[d]
        if isinstance(st, dict) and "accuracy" in st:
            accuracies.append(float(st["accuracy"]))
        else:
            accuracies.append(0.0)
    # Simple trend: decreasing = expected (harder -> lower accuracy)
    if len(accuracies) >= 2:
        if accuracies[-1] < accuracies[0]:
            trend = "decreasing"
        elif accuracies[-1] > accuracies[0]:
            trend = "increasing"
        else:
            trend = "flat"
    else:
        trend = "single_level"
    return {
        "levels": ordered,
        "accuracy_gradient": accuracies,
        "gradient_trend": trend,
        "by_level": {d: by_difficulty[d] for d in ordered},
    }


def evaluate_mathematical_and_devops(
    metrics: Dict[str, Any],
    project_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Full evaluation combining mathematical gradient and DevOps gradient.
    Intended for project progress reports and dashboards.
    """
    math_score, math_level, math_satisfied = _score_math_capabilities(metrics)
    devops_score, devops_level, devops_satisfied = _score_devops_capabilities(project_root)
    # Optional: difficulty gradient from metrics
    by_difficulty = metrics.get("by_difficulty") or {}
    difficulty_gradient = compute_difficulty_gradient(by_difficulty)
    return {
        "mathematical": {
            "score": round(math_score, 3),
            "level": math_level,
            "criteria_satisfied": math_satisfied,
            "difficulty_gradient": difficulty_gradient,
        },
        "devops": {
            "score": round(devops_score, 3),
            "level": devops_level,
            "criteria_satisfied": devops_satisfied,
        },
        "summary": {
            "math_level_description": next(
                (l.description for l in MATHEMATICAL_GRADIENT_LEVELS if l.name == math_level),
                "",
            ),
            "devops_level_description": next(
                (l.description for l in DEVOPS_GRADIENT_LEVELS if l.name == devops_level),
                "",
            ),
        },
    }


def get_gradient_levels_documentation() -> Dict[str, Any]:
    """Return documentation of all gradient levels for reports."""
    return {
        "mathematical_levels": [
            {"name": l.name, "score_range": [l.score_min, l.score_max], "description": l.description}
            for l in MATHEMATICAL_GRADIENT_LEVELS
        ],
        "devops_levels": [
            {"name": l.name, "score_range": [l.score_min, l.score_max], "description": l.description}
            for l in DEVOPS_GRADIENT_LEVELS
        ],
    }
