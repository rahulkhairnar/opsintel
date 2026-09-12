# OpsIntel Architecture

## Overview

OpsIntel uses Exasol as the analytical data platform for infrastructure monitoring and incident investigation.

## Data Flow

1. Infrastructure monitoring data is collected.
2. Data is stored in Exasol.
3. SQL analytics calculate operational metrics.
4. Anomaly detection identifies unusual behaviour.
5. The AI investigation agent queries Exasol.
6. Evidence is correlated and presented to the user.

## Components

- Exasol Personal
- Python application
- SQL analytics
- AI investigation agent
- Web interface
