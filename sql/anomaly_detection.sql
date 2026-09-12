-- OpsIntel anomaly detection and incident scoring
-- Produces an evidence-based incident assessment for web-03.

WITH baseline AS (
    SELECT
        AVG(CPU_PCT) AS baseline_cpu,
        AVG(MEMORY_PCT) AS baseline_memory,
        AVG(RESPONSE_MS) AS baseline_response,
        AVG(ERROR_RATE_PCT) AS baseline_error,
        AVG(HTTP_5XX) AS baseline_5xx
    FROM OPSINTEL.SERVICE_METRICS
    WHERE SERVER_NAME = 'web-03'
      AND NOT (
          EVENT_TIME >= TIMESTAMP '2026-09-12 14:30:00'
          AND EVENT_TIME < TIMESTAMP '2026-09-12 14:40:00'
      )
),

incident AS (
    SELECT
        AVG(CPU_PCT) AS incident_cpu,
        AVG(MEMORY_PCT) AS incident_memory,
        AVG(RESPONSE_MS) AS incident_response,
        AVG(ERROR_RATE_PCT) AS incident_error,
        AVG(HTTP_5XX) AS incident_5xx
    FROM OPSINTEL.SERVICE_METRICS
    WHERE SERVER_NAME = 'web-03'
      AND EVENT_TIME >= TIMESTAMP '2026-09-12 14:30:00'
      AND EVENT_TIME < TIMESTAMP '2026-09-12 14:40:00'
),

scored AS (
    SELECT
        CASE
            WHEN i.incident_cpu >= b.baseline_cpu * 2 THEN 1
            ELSE 0
        END AS cpu_anomaly,

        CASE
            WHEN i.incident_memory >= b.baseline_memory * 1.3 THEN 1
            ELSE 0
        END AS memory_anomaly,

        CASE
            WHEN i.incident_response >= b.baseline_response * 3 THEN 1
            ELSE 0
        END AS latency_anomaly,

        CASE
            WHEN i.incident_error >= b.baseline_error * 5 THEN 1
            ELSE 0
        END AS error_anomaly,

        CASE
            WHEN i.incident_5xx >= b.baseline_5xx * 10 THEN 1
            ELSE 0
        END AS http5xx_anomaly,

        b.*,
        i.*
    FROM baseline b
    CROSS JOIN incident i
)

SELECT
    'web-03' AS server_name,

    cpu_anomaly,
    memory_anomaly,
    latency_anomaly,
    error_anomaly,
    http5xx_anomaly,

    cpu_anomaly
        + memory_anomaly
        + latency_anomaly
        + error_anomaly
        + http5xx_anomaly AS anomaly_score,

    CASE
        WHEN (
            cpu_anomaly
            + memory_anomaly
            + latency_anomaly
            + error_anomaly
            + http5xx_anomaly
        ) >= 4 THEN 'CRITICAL'

        WHEN (
            cpu_anomaly
            + memory_anomaly
            + latency_anomaly
            + error_anomaly
            + http5xx_anomaly
        ) >= 2 THEN 'WARNING'

        ELSE 'NORMAL'
    END AS severity,

    ROUND(baseline_cpu, 2) AS baseline_cpu,
    ROUND(incident_cpu, 2) AS incident_cpu,

    ROUND(baseline_response, 2) AS baseline_response_ms,
    ROUND(incident_response, 2) AS incident_response_ms,

    ROUND(baseline_error, 2) AS baseline_error_rate,
    ROUND(incident_error, 2) AS incident_error_rate,

    ROUND(baseline_5xx, 2) AS baseline_5xx,
    ROUND(incident_5xx, 2) AS incident_5xx

FROM scored;
