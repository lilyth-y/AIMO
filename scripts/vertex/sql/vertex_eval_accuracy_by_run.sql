-- Vertex 평가 적재 테이블(기본: project.aimo_vertex.eval_runs) 예시 집계
-- run_id별 정확도·지연·형식 준수율

SELECT
  run_id,
  endpoint_id,
  COUNT(*) AS n,
  AVG(IF(is_correct, 1.0, 0.0)) AS accuracy,
  AVG(latency_s) AS avg_latency_s,
  AVG(IF(strict_format_ok, 1.0, 0.0)) AS strict_format_rate,
  MIN(ingested_at) AS run_start
FROM `REPLACE_PROJECT.REPLACE_DATASET.eval_runs`
GROUP BY run_id, endpoint_id
ORDER BY run_start DESC
LIMIT 50;
