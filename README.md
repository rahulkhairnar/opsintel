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

## Planned Architecture

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

Project initialization.

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

## Security

Secrets, credentials, private keys and local VM files must never be committed to this repository.
