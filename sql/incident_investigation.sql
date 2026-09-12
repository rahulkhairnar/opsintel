-- OpsIntel evidence-backed incident investigation.
-- Combines anomaly scoring with correlated operational events.

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
        b.*,
        i.*,

        CASE WHEN i.incident_cpu >= b.baseline_cpu * 2
             THEN 1 ELSE 0 END AS cpu_anomaly,

        CASE WHEN i.incident_memory >= b.baseline_memory * 1.3
             THEN 1 ELSE 0 END AS memory_anomaly,

        CASE WHEN i.incident_response >= b.baseline_response * 3
             THEN 1 ELSE 0 END AS latency_anomaly,

        CASE WHEN i.incident_error >= b.baseline_error * 5
             THEN 1 ELSE 0 END AS error_anomaly,

        CASE WHEN i.incident_5xx >= b.baseline_5xx * 10
             THEN 1 ELSE 0 END AS http5xx_anomaly

    FROM baseline b
    CROSS JOIN incident i
),

event_summary AS (
    SELECT
        COUNT(*) AS correlated_event_count,
        SUM(
            CASE
                WHEN SEVERITY = 'critical' THEN 1
                ELSE 0
            END
        ) AS critical_event_count
    FROM OPSINTEL.INCIDENT_EVENTS
    WHERE SERVER_NAME = 'web-03'
      AND EVENT_TIME >= TIMESTAMP '2026-09-12 14:29:00'
      AND EVENT_TIME <= TIMESTAMP '2026-09-12 14:40:00'
)

SELECT
    'web-03' AS server_name,

    (
        cpu_anomaly
        + memory_anomaly
        + latency_anomaly
        + error_anomaly
        + http5xx_anomaly
    ) AS anomaly_score,

    CASE
        WHEN (
            cpu_anomaly
            + memory_anomaly
            + latency_anomaly
            + error_anomaly
            + http5xx_anomaly
        ) >= 4
        THEN 'CRITICAL'

        WHEN (
            cpu_anomaly
            + memory_anomaly
            + latency_anomaly
            + error_anomaly
            + http5xx_anomaly
        ) >= 2
        THEN 'WARNING'

        ELSE 'NORMAL'
    END AS severity,

    ROUND(
        (incident_cpu - baseline_cpu)
        / NULLIF(baseline_cpu, 0) * 100,
        2
    ) AS cpu_change_pct,

    ROUND(
        incident_response
        / NULLIF(baseline_response, 0),
        2
    ) AS response_multiplier,

    ROUND(
        incident_error
        / NULLIF(baseline_error, 0),
        2
    ) AS error_multiplier,

    ROUND(
        incident_5xx
        / NULLIF(baseline_5xx, 0),
        2
    ) AS http5xx_multiplier,

    event_summary.correlated_event_count,
    event_summary.critical_event_count,

    CASE
        WHEN (
            cpu_anomaly
            + memory_anomaly
            + latency_anomaly
            + error_anomaly
            + http5xx_anomaly
        ) >= 4
        AND event_summary.critical_event_count >= 2
        THEN 'HIGH'

        WHEN (
            cpu_anomaly
            + memory_anomaly
            + latency_anomaly
            + error_anomaly
            + http5xx_anomaly
        ) >= 2
        THEN 'MEDIUM'

        ELSE 'LOW'
    END AS INVESTIGATION_CONFIDENCE

FROM scored
CROSS JOIN event_summary;
