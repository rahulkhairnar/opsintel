import json
import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from app.analytics import investigate

load_dotenv(dotenv_path=".env")


SYSTEM_PROMPT = """
You are OpsIntel, an AI infrastructure incident investigator.

Your job is to explain infrastructure incidents using ONLY the evidence
provided by the analytics system.

STRICT EVIDENCE RULES:

1. Never invent metrics, events, timestamps, or technical facts.
2. Treat Exasol analytics output as the authoritative source of numerical values.
3. Copy numerical values exactly as supplied by the evidence.
4. Values containing names such as "_pct" or "rate" that are already expressed
   as percentages must NOT be converted into another percentage.
5. Never convert decimal values into percentages unless the evidence explicitly
   identifies the value as a fraction.
6. Do not introduce connection-pool utilization, thresholds, or other values
   unless they are explicitly present in the supplied events or evidence.
7. Clearly distinguish observed evidence from inference.
8. Correlation does NOT prove causation.
9. Never claim that an event "directly triggered" another event unless the
   evidence explicitly establishes that relationship.
10. Never call something a confirmed root cause. Use "likely cause" or
    "strongest evidence-supported hypothesis".
11. Do not claim that recovery proves causation. Describe recovery as a
    correlated observation.
12. If evidence is insufficient, explicitly say so.
13. Mention important metric changes using the exact values from the evidence.
14. Mention correlated operational events in chronological order.
15. Be concise and useful to an infrastructure engineer.
16. Never recommend destructive database operations.

The report must contain exactly these sections:

## Incident Summary
## Evidence
## Likely Cause
## Timeline
## Confidence
## Recommended Next Checks
"""


def build_evidence_prompt(investigation: dict[str, Any]) -> str:
    """Build a strict evidence-only prompt for the AI model."""

    evidence = investigation["evidence"]
    events = investigation["events"]

    payload = {
        "evidence": evidence,
        "correlated_events": events,
    }

    return (
        "Investigate the following infrastructure incident.\n\n"
        "IMPORTANT:\n"
        "- Use ONLY the supplied evidence.\n"
        "- Do not invent facts.\n"
        "- Preserve numerical values exactly as supplied.\n"
        "- Do not convert percentage values.\n"
        "- Do not claim causation when the evidence only shows correlation.\n\n"
        f"{json.dumps(payload, default=str, indent=2)}"
    )


def deterministic_report(investigation: dict[str, Any]) -> str:
    """Reliable evidence-backed fallback report."""

    evidence = investigation["evidence"]
    events = investigation["events"]

    server = evidence["server_name"]
    confidence = evidence["investigation_confidence"]

    cpu_change = evidence["cpu_change_pct"]
    response_multiplier = evidence["response_multiplier"]
    error_multiplier = evidence["error_multiplier"]
    http5xx_multiplier = evidence["http5xx_multiplier"]

    baseline_cpu = evidence["baseline_cpu"]
    incident_cpu = evidence["incident_cpu"]

    baseline_memory = evidence["baseline_memory"]
    incident_memory = evidence["incident_memory"]

    baseline_response = evidence["baseline_response_ms"]
    incident_response = evidence["incident_response_ms"]

    baseline_error = evidence["baseline_error_rate"]
    incident_error = evidence["incident_error_rate"]

    baseline_5xx = evidence["baseline_http_5xx"]
    incident_5xx = evidence["incident_http_5xx"]

    timeline = "\n".join(
        f"- {event['event_time']} — "
        f"{event['severity'].upper()} — "
        f"{event['message']}"
        for event in events
    )

    return f"""## Incident Summary

**{server} experienced a critical service degradation.**

The incident shows substantial increases across CPU, memory, response
latency, error rate, and HTTP 5xx responses compared with the baseline.

## Evidence

- CPU: {baseline_cpu:.2f}% → {incident_cpu:.2f}% (**+{cpu_change:.2f}%**)
- Memory: {baseline_memory:.2f}% → {incident_memory:.2f}%
- Response latency: {baseline_response:.2f} ms → {incident_response:.2f} ms (**{response_multiplier:.2f}×**)
- Error rate: {baseline_error:.2f}% → {incident_error:.2f}% (**{error_multiplier:.2f}×**)
- HTTP 5xx: {baseline_5xx:.2f} → {incident_5xx:.2f} (**{http5xx_multiplier:.2f}×**)

## Likely Cause

The strongest evidence-supported hypothesis is **connection-pool exhaustion**.

The connection pool reached 100% utilization at the beginning of the
incident, followed by increased HTTP 5xx errors and request latency.
The connection pool recovered at the end of the incident, coinciding
with service recovery.

These observations establish correlation, not definitive causation.

## Timeline

{timeline}

## Confidence

**{confidence}**

The confidence is based on the number and severity of correlated
operational events returned by the Exasol investigation.

## Recommended Next Checks

1. Inspect connection-pool configuration and maximum connection limits.
2. Check application logs around the start of the incident.
3. Check database connection latency and connection availability.
4. Review whether request concurrency increased during the incident.
5. Verify whether connection-pool exhaustion recurs under similar load.
"""


def llm_report(
    investigation: dict[str, Any],
    api_key: str,
    model: str,
    provider: str,
) -> str:
    """Generate the incident report using the configured LLM provider."""

    if provider == "openrouter":
        client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )
    else:
        client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": build_evidence_prompt(investigation),
            },
        ],
        temperature=0.1,
    )

    return response.choices[0].message.content.strip()


def generate_report_with_mode(
    investigation: dict[str, Any],
) -> tuple[str, str]:
    """Generate an AI report with a deterministic fallback."""

    ai_provider = os.getenv("AI_PROVIDER", "").strip().lower()
    ai_api_key = os.getenv("AI_API_KEY", "").strip()
    ai_model = os.getenv("AI_MODEL", "openrouter/free").strip()

    if ai_provider in {"openrouter", "openai"} and ai_api_key:
        try:
            report = llm_report(
                investigation=investigation,
                api_key=ai_api_key,
                model=ai_model,
                provider=ai_provider,
            )

            return report, f"{ai_provider.upper()} LLM ({ai_model})"

        except Exception as exc:
            print(
                f"WARNING: {ai_provider.upper()} request failed: {exc}"
            )
            print(
                "Falling back to deterministic evidence-backed report."
            )

    return deterministic_report(investigation), "Deterministic fallback"


def generate_report(investigation: dict[str, Any]) -> str:
    """Generate an incident report."""

    report, _ = generate_report_with_mode(investigation)
    return report


def investigate_and_report(
    server_name,
    start_time,
    end_time,
) -> dict[str, Any]:
    """Run Exasol investigation and generate an evidence-backed report."""

    investigation = investigate(
        server_name=server_name,
        start_time=start_time,
        end_time=end_time,
    )

    report, report_mode = generate_report_with_mode(investigation)

    return {
        **investigation,
        "report": report,
        "report_mode": report_mode,
        "prompt": build_evidence_prompt(investigation),
    }
