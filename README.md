# OpsIntel

AI-powered infrastructure incident investigation and anomaly detection using Exasol Personal.

## Exasol AI + Data Challenge 2026

OpsIntel is being developed for the Exasol AI + Data Challenge 2026.

## Problem

Infrastructure teams generate large volumes of monitoring and operational data. Finding the root cause of an incident often requires manually correlating CPU, memory, disk, network, HTTP, application and event data.

## Solution

OpsIntel combines Exasol analytics with an AI-powered investigation agent.

A user can ask questions such as:

> Why did web-03 become unhealthy around 14:30?

The system analyzes infrastructure data stored in Exasol, identifies anomalies and correlations, and provides an evidence-based explanation.

## Architecture

Monitoring / Infrastructure Data
        |
        v
     Exasol
        |
        v
SQL Analytics / Anomaly Detection
        |
        v
AI Investigation Agent
        |
        v
Web Interface / Investigation Report

## Current Status

Working MVP completed: Exasol analytics, anomaly detection, evidence-backed AI investigation, SQL safety validation, Streamlit dashboard, incident timeline, and performance instrumentation.

## Technology

- Exasol Personal
- SQL
- Python
- AI/LLM
- Infrastructure monitoring data
- Git/GitHub

## Documentation

- `docs/architecture.md`
- `docs/testing.md`
- `docs/evidence.md`

## How It Works

1. Infrastructure telemetry and operational events are stored in Exasol Personal.
2. SQL analytics calculate baseline behavior for the selected server.
3. Anomaly detection compares incident behavior against the baseline.
4. Correlated operational events are retrieved from Exasol.
5. A read-only SQL safety gate validates database queries before execution.
6. The AI investigation agent receives the structured evidence and produces an incident report.
7. Streamlit presents the evidence, report, timeline, confidence, and measured execution times.

## Example Result

For the included `web-03` incident, OpsIntel detects a critical anomaly across CPU, memory, latency, error rate, and HTTP 5xx signals. The investigation correlates five operational events and identifies connection-pool exhaustion as the strongest evidence-supported hypothesis while distinguishing correlation from confirmed causation.

## Performance

The dashboard records Exasol execution time, AI report-generation time, and total investigation time. This provides measured end-to-end performance rather than estimated latency.

## Security

API keys and credentials must remain in the local `.env` file and must never be committed. The repository contains only `.env.example` as a configuration template.
