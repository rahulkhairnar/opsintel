import random
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)

OUTPUT_DIR = Path("data/generated")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

START = datetime(2026, 9, 12, 12, 0, 0)

servers = [
    ("web-01", "web"),
    ("web-02", "web"),
    ("web-03", "web"),
    ("web-04", "web"),
    ("api-01", "api"),
    ("api-02", "api"),
    ("db-01", "database"),
]

environment = "production"
region = "ap-south-1"

# 50,000 rows spread across the infrastructure fleet.
rows = []

for i in range(50_000):
    timestamp = START + timedelta(seconds=i * 1.5)

    server, service = random.choice(servers)

    # Normal operating characteristics.
    cpu = random.gauss(42, 8)
    memory = random.gauss(58, 7)
    disk = random.gauss(48, 5)
    network = max(10, random.gauss(180, 35))
    response = max(20, random.gauss(180, 35))
    error_rate = max(0, random.gauss(0.4, 0.25))
    http_5xx = max(0, int(random.gauss(3, 2)))
    requests = max(100, int(random.gauss(4200, 500)))

    health = "healthy"

    # Inject a clear incident on web-03.
    #
    # Incident window:
    # 14:30 - 14:40 UTC
    if (
        server == "web-03"
        and datetime(2026, 9, 12, 14, 30) <= timestamp
        < datetime(2026, 9, 12, 14, 40)
    ):
        cpu = random.gauss(94, 3)
        memory = random.gauss(82, 4)
        disk = random.gauss(52, 3)
        network = max(50, random.gauss(310, 40))
        response = random.gauss(1250, 150)
        error_rate = random.gauss(18, 3)
        http_5xx = max(50, int(random.gauss(180, 35)))
        requests = max(100, int(random.gauss(3900, 450)))
        health = "unhealthy"

    rows.append(
        (
            timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            server,
            service,
            round(max(0, min(cpu, 100)), 2),
            round(max(0, min(memory, 100)), 2),
            round(max(0, min(disk, 100)), 2),
            round(network, 2),
            round(response, 2),
            round(max(0, error_rate), 2),
            http_5xx,
            requests,
            health,
        )
    )

metrics_file = OUTPUT_DIR / "service_metrics.csv"

with metrics_file.open("w") as f:
    f.write(
        "EVENT_TIME,SERVER_NAME,SERVICE_NAME,CPU_PCT,MEMORY_PCT,"
        "DISK_PCT,NETWORK_MBPS,RESPONSE_MS,ERROR_RATE_PCT,HTTP_5XX,"
        "REQUESTS_PER_MIN,HEALTH_STATUS\n"
    )

    for row in rows:
        f.write(",".join(map(str, row)) + "\n")


# Service metadata.
services = [
    ("svc-web-01", "web-01", "web", environment, region, "Web Platform"),
    ("svc-web-02", "web-02", "web", environment, region, "Web Platform"),
    ("svc-web-03", "web-03", "web", environment, region, "Web Platform"),
    ("svc-web-04", "web-04", "web", environment, region, "Web Platform"),
    ("svc-api-01", "api-01", "api", environment, region, "API Platform"),
    ("svc-api-02", "api-02", "api", environment, region, "API Platform"),
    ("svc-db-01", "db-01", "database", environment, region, "Database Platform"),
]

services_file = OUTPUT_DIR / "services.csv"

with services_file.open("w") as f:
    f.write(
        "SERVICE_ID,SERVER_NAME,SERVICE_NAME,ENVIRONMENT,"
        "REGION,OWNER_TEAM,CREATED_AT\n"
    )

    for service in services:
        f.write(
            ",".join(
                map(
                    str,
                    service + ("2026-01-01 00:00:00",),
                )
            )
            + "\n"
        )


# Correlated incident events.
events = [
    (
        "2026-09-12 14:29:30",
        "web-03",
        "web",
        "SYSTEM",
        "warning",
        "CPU utilization crossed warning threshold",
    ),
    (
        "2026-09-12 14:30:00",
        "web-03",
        "web",
        "APPLICATION",
        "critical",
        "Connection pool utilization reached 100 percent",
    ),
    (
        "2026-09-12 14:31:00",
        "web-03",
        "web",
        "APPLICATION",
        "critical",
        "HTTP 5xx error rate increased sharply",
    ),
    (
        "2026-09-12 14:33:00",
        "web-03",
        "web",
        "SYSTEM",
        "critical",
        "Request latency exceeded 1000 ms",
    ),
    (
        "2026-09-12 14:40:00",
        "web-03",
        "web",
        "RECOVERY",
        "info",
        "Connection pool recovered and service health returned to normal",
    ),
]

events_file = OUTPUT_DIR / "incident_events.csv"

with events_file.open("w") as f:
    f.write(
        "EVENT_TIME,SERVER_NAME,SERVICE_NAME,EVENT_TYPE,"
        "SEVERITY,EVENT_MESSAGE\n"
    )

    for event in events:
        f.write(",".join(map(str, event)) + "\n")


print("Dataset generation: SUCCESS")
print(f"Metrics rows: {len(rows):,}")
print(f"Metrics file: {metrics_file}")
print(f"Services rows: {len(services):,}")
print(f"Services file: {services_file}")
print(f"Incident events: {len(events):,}")
print(f"Events file: {events_file}")
print()
print("Injected incident:")
print("  Server: web-03")
print("  Window: 14:30-14:40 UTC")
print("  Symptoms: high CPU, high latency, high error rate, HTTP 5xx")
print("  Correlated event: connection pool utilization reached 100%")
