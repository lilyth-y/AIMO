"""
Vertex 온라인 평가(JSONL) ↔ BigQuery 적재 공통.

환경:
  GOOGLE_CLOUD_PROJECT / PROJECT_ID — 기본 프로젝트
  VERTEX_EVAL_BQ_DATASET — 기본 데이터셋 (예: aimo_vertex)
  VERTEX_EVAL_BQ_TABLE — 기본 테이블 ID (dataset.table 또는 project.dataset.table)

인증: Application Default Credentials (Vertex와 동일).
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from vertex_common import resolve_location, resolve_project_id

try:
    from google.api_core.exceptions import NotFound
    from google.cloud import bigquery
except ImportError:
    NotFound = Exception  # type: ignore
    bigquery = None  # type: ignore


DEFAULT_DATASET = os.getenv("VERTEX_EVAL_BQ_DATASET", "aimo_vertex")
DEFAULT_TABLE = os.getenv("VERTEX_EVAL_BQ_TABLE", "eval_runs")


def _require_bq():
    if bigquery is None:
        raise ImportError(
            "google-cloud-bigquery 필요: pip install -r requirements-vertex-bq.txt"
        )


def eval_run_schema() -> List["bigquery.SchemaField"]:
    _require_bq()
    return [
        bigquery.SchemaField("run_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("ingested_at", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("endpoint_id", "STRING"),
        bigquery.SchemaField("vertex_project", "STRING"),
        bigquery.SchemaField("vertex_location", "STRING"),
        bigquery.SchemaField("sample_idx", "INTEGER"),
        bigquery.SchemaField("problem_id", "INTEGER"),
        bigquery.SchemaField("source", "STRING"),
        bigquery.SchemaField("difficulty", "STRING"),
        bigquery.SchemaField("reference_answer", "STRING"),
        bigquery.SchemaField("latency_s", "FLOAT"),
        bigquery.SchemaField("error", "STRING"),
        bigquery.SchemaField("strict_format_ok", "BOOLEAN"),
        bigquery.SchemaField("format_attempts", "INTEGER"),
        bigquery.SchemaField("format_failure_reason", "STRING"),
        bigquery.SchemaField("scoring_status", "STRING"),
        bigquery.SchemaField("raw_text_head", "STRING"),
        bigquery.SchemaField("predicted_answer", "STRING"),
        bigquery.SchemaField("is_correct", "BOOLEAN"),
        bigquery.SchemaField("extracted_json", "STRING"),
        bigquery.SchemaField("verify_agent_json", "STRING"),
    ]


def _parse_table_ref(
    table_arg: str,
    *,
    default_project: str,
) -> tuple[str, str, str]:
    """
    'dataset.table' 또는 'project.dataset.table' → (project, dataset, table_id short name)
    """
    parts = table_arg.replace("`", "").strip().split(".")
    if len(parts) == 2:
        return default_project, parts[0], parts[1]
    if len(parts) == 3:
        return parts[0], parts[1], parts[2]
    raise ValueError(
        f"테이블 ID 형식: <dataset>.<table> 또는 <project>.<dataset>.<table>, got: {table_arg!r}"
    )


def ensure_eval_table(
    client: "bigquery.Client",
    full_table_id: str,
    *,
    dataset_location: str = "asia-northeast3",
) -> None:
    _require_bq()
    parts = full_table_id.replace("`", "").strip().split(".")
    if len(parts) != 3:
        raise ValueError(f"full_table_id는 project.dataset.table 형식이어야 함: {full_table_id!r}")
    project, dataset_id, table_name = parts
    try:
        client.get_table(full_table_id)
        return
    except NotFound:
        pass
    ds_ref = bigquery.DatasetReference(project, dataset_id)
    try:
        client.get_dataset(ds_ref)
    except NotFound:
        ds = bigquery.Dataset(ds_ref)
        ds.location = dataset_location
        client.create_dataset(ds, exists_ok=True)
    table = bigquery.Table(
        bigquery.TableReference(ds_ref, table_name),
        schema=eval_run_schema(),
    )
    client.create_table(table, exists_ok=True)


def _json_safe(obj: Any) -> Optional[str]:
    if obj is None:
        return None
    try:
        return json.dumps(obj, ensure_ascii=False)
    except TypeError:
        return json.dumps(str(obj), ensure_ascii=False)


def jsonl_row_to_bq_row(
    obj: Dict[str, Any],
    *,
    run_id: str,
    endpoint_id: str,
    vertex_project: str,
    vertex_location: str,
) -> Dict[str, Any]:
    ingested = datetime.now(timezone.utc).isoformat()
    extracted = obj.get("extracted")
    verify = obj.get("verify_agent")
    return {
        "run_id": run_id,
        "ingested_at": ingested,
        "endpoint_id": endpoint_id,
        "vertex_project": vertex_project,
        "vertex_location": vertex_location,
        "sample_idx": obj.get("sample_idx"),
        "problem_id": obj.get("problem_id"),
        "source": obj.get("source"),
        "difficulty": obj.get("difficulty"),
        "reference_answer": obj.get("reference_answer"),
        "latency_s": obj.get("latency_s"),
        "error": obj.get("error"),
        "strict_format_ok": obj.get("strict_format_ok"),
        "format_attempts": obj.get("format_attempts"),
        "format_failure_reason": obj.get("format_failure_reason"),
        "scoring_status": obj.get("scoring_status"),
        "raw_text_head": obj.get("raw_text_head"),
        "predicted_answer": obj.get("predicted_answer"),
        "is_correct": obj.get("is_correct"),
        "extracted_json": _json_safe(extracted),
        "verify_agent_json": _json_safe(verify),
    }


def iter_jsonl(path: Path) -> Iterator[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def upload_jsonl_to_bigquery(
    jsonl_path: Path,
    *,
    table: str,
    run_id: Optional[str] = None,
    endpoint_id: str = "",
    vertex_project: Optional[str] = None,
    vertex_location: Optional[str] = None,
    create_table: bool = True,
    dataset_location: str = "asia-northeast3",
) -> tuple[int, str]:
    """
    JSONL 한 파일을 BigQuery에 insert_rows_json으로 적재.

    Returns:
        (row_count, run_id)
    """
    _require_bq()
    default_project = vertex_project or resolve_project_id(prefer_cleanup_alias=False)
    loc = vertex_location or resolve_location()
    rid = run_id or str(uuid.uuid4())

    proj, dataset_id, table_name = _parse_table_ref(table, default_project=default_project)
    full_id = f"{proj}.{dataset_id}.{table_name}"

    client = bigquery.Client(project=proj)
    if create_table:
        ensure_eval_table(client, full_id, dataset_location=dataset_location)

    rows: List[Dict[str, Any]] = []
    for obj in iter_jsonl(jsonl_path):
        rows.append(
            jsonl_row_to_bq_row(
                obj,
                run_id=rid,
                endpoint_id=endpoint_id,
                vertex_project=proj,
                vertex_location=loc,
            )
        )

    if not rows:
        return 0, rid

    errors = client.insert_rows_json(full_id, rows)
    if errors:
        raise RuntimeError(f"BigQuery insert_rows_json 실패: {errors[:3]}...")
    return len(rows), rid


def new_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:8]
