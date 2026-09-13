from datetime import datetime
from typing import Any

from app.database import get_connection
from app.safety import validate_sql


INVESTIGATION_SQL = """
WITH baseline AS (
    SELECT
        AVG(CPU_PCT) AS baseline_cpu,
        AVG(MEMORY_PCT) AS baseline_memory,
        AVG(RESPONSE_MS) AS baseline_response_ms,
        AVG(ERROR_RATE_PCT) AS baseline_error_rate,
        AVG(HTTP_5XX) AS baseline_http_5xx
    FROM OPSINTEL.SERVICE_METRICS
    WHERE SERVER_NAME = '{server_name}'
      AND EVENT_TIME < '{start_time}'
),
incident AS (
    SELECT
        AVG(CPU_PCT) AS incident_cpu,
        AVG(MEMORY_PCT) AS incident_memory,
        AVG(RESPONSE_MS) AS incident_response_ms,
        AVG(ERROR_RATE_PCT) AS incident_error_rate,
        AVG(HTTP_5XX) AS incident_http_5xx
    FROM OPSINTEL.SERVICE_METRICS
    WHERE SERVER_NAME = '{server_name}'
      AND EVENT_TIME >= '{start_time}'
      AND EVENT_TIME <= '{end_time}'
),
events AS (
    SELECT
        COUNT(*) AS correlated_event_count,
        SUM(
            CASE
                WHEN UPPER(SEVERITY) = 'CRITICAL' THEN 1
                ELSE 0
            END
        ) AS critical_event_count
    FROM OPSINTEL.INCIDENT_EVENTS
    WHERE SERVER_NAME = '{server_name}'
      AND EVENT_TIME >= '{start_time}'
      AND EVENT_TIME <= '{end_time}'
)
SELECT
    '{server_name}' AS server_name,

    ROUND(
        ((incident_cpu - baseline_cpu) / NULLIF(baseline_cpu, 0)) * 100,
        2
    ) AS cpu_change_pct,

    ROUND(
        incident_response_ms / NULLIF(baseline_response_ms, 0),
        2
    ) AS response_multiplier,

    ROUND(
        incident_error_rate / NULLIF(baseline_error_rate, 0),
        2
    ) AS error_multiplier,

    ROUND(
        incident_http_5xx / NULLIF(baseline_http_5xx, 0),
        2
    ) AS http5xx_multiplier,

    correlated_event_count,
    critical_event_count,

    CASE
        WHEN correlated_event_count >= 3
             AND critical_event_count >= 2
        THEN 'HIGH'
        WHEN correlated_event_count >= 1
        THEN 'MEDIUM'
        ELSE 'LOW'
    END AS investigation_confidence,

    baseline_cpu,
    incident_cpu,
    baseline_memory,
    incident_memory,
    baseline_response_ms,
    incident_response_ms,
    baseline_error_rate,
    incident_error_rate,
    baseline_http_5xx,
    incident_http_5xx

FROM baseline
CROSS JOIN incident
CROSS JOIN events
"""


EVENTS_SQL = """
SELECT
    EVENT_TIME,
    EVENT_TYPE,
    SEVERITY,
    EVENT_MESSAGE
FROM OPSINTEL.INCIDENT_EVENTS
WHERE SERVER_NAME = '{server_name}'
  AND EVENT_TIME >= '{event_start_time}'
  AND EVENT_TIME <= '{end_time}'
ORDER BY EVENT_TIME
"""


def _validate_identifier(value: str) -> str:
    """Allow only simple server identifiers."""

    if not isinstance(value, str):
        raise ValueError("Server name must be a string.")

    value = value.strip()

    if not value:
        raise ValueError("Server name cannot be empty.")

    if not value.replace("-", "").replace("_", "").isalnum():
        raise ValueError("Invalid server name.")

    return value


def _validate_timestamp(value: datetime) -> str:
    """Convert a datetime to a safe SQL timestamp literal."""

    if not isinstance(value, datetime):
        raise ValueError("Timestamp must be a datetime object.")

    return value.strftime("%Y-%m-%d %H:%M:%S")


def _execute_readonly(connection, sql: str):
    """Validate SQL and execute it."""

    safe_sql = validate_sql(sql)
    return connection.execute(safe_sql).fetchall()


def investigate(
    server_name: str,
    start_time: datetime,
    end_time: datetime,
) -> dict[str, Any]:
    """
    Investigate an infrastructure incident using Exasol evidence.
    """

    server_name = _validate_identifier(server_name)
    start_time_sql = _validate_timestamp(start_time)
    end_time_sql = _validate_timestamp(end_time)

    if start_time >= end_time:
        raise ValueError("start_time must be before end_time.")

    investigation_sql = INVESTIGATION_SQL.format(
        server_name=server_name,
        start_time=start_time_sql,
        end_time=end_time_sql,
    )

    event_start_time = _validate_timestamp(
        start_time - __import__("datetime").timedelta(seconds=30)
    )
    events_sql = EVENTS_SQL.format(
        server_name=server_name,
        event_start_time=event_start_time,
        end_time=end_time_sql,
    )

    connection = get_connection()

    try:
        investigation_rows = _execute_readonly(
            connection,
            investigation_sql,
        )

        event_rows = _execute_readonly(
            connection,
            events_sql,
        )
    finally:
        connection.close()

    if not investigation_rows:
        raise RuntimeError(
            "No investigation data was returned for the requested server "
            "and time window."
        )

    columns = [
        "server_name",
        "cpu_change_pct",
        "response_multiplier",
        "error_multiplier",
        "http5xx_multiplier",
        "correlated_event_count",
        "critical_event_count",
        "investigation_confidence",
        "baseline_cpu",
        "incident_cpu",
        "baseline_memory",
        "incident_memory",
        "baseline_response_ms",
        "incident_response_ms",
        "baseline_error_rate",
        "incident_error_rate",
        "baseline_http_5xx",
        "incident_http_5xx",
    ]

    evidence = dict(zip(columns, investigation_rows[0]))

    events = [
        {
            "event_time": row[0],
            "event_type": row[1],
            "severity": row[2],
            "message": row[3],
        }
        for row in event_rows
    ]

    return {
        "evidence": evidence,
        "events": events,
        "investigation_sql": investigation_sql,
        "events_sql": events_sql,
    }
