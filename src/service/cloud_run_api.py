"""
Cloud Run entrypoint for AIMO orchestrator.
Run with:
  uvicorn src.service.cloud_run_api:app --host 0.0.0.0 --port 8080
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import FastAPI
from pydantic import BaseModel

from src.pipeline.orchestrator import PipelineOrchestrator
from src.pipeline.stage1_labeling import ProblemAnalyzer


class SolveRequest(BaseModel):
    problem_text: str
    time_budget: float = 60.0
    domain: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None


app = FastAPI(title="AIMO Cloud Run API")
_orchestrator = PipelineOrchestrator()
_analyzer = ProblemAnalyzer()


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/solve")
def solve(req: SolveRequest) -> Dict[str, Any]:
    domain = req.domain or _analyzer.classify_domain(req.problem_text)
    variables = req.variables or _analyzer.extract_variables(req.problem_text)
    result = _orchestrator.solve_problem(
        domain=domain,
        variables=variables,
        problem_text=req.problem_text,
        time_budget=req.time_budget,
    )

    # Orchestrator may inject callables (e.g., reverse_func) into variables.
    # Pydantic cannot serialize those, so strip them before returning.
    safe_variables: Dict[str, Any] = {k: v for k, v in variables.items() if not callable(v)}

    return {
        "domain": domain,
        "variables": safe_variables,
        "result": result,
    }

