import time
from datetime import datetime

import streamlit as st

from app.agent import investigate_and_report


st.set_page_config(
    page_title="OpsIntel",
    page_icon="🛠️",
    layout="wide",
)


# -----------------------------
# Page styling
# -----------------------------

st.title("🛠️ OpsIntel")
st.subheader("AI Infrastructure Incident Investigator")

st.caption(
    "Evidence-backed incident investigation powered by Exasol. "
    "All database queries pass through a read-only SQL safety gate."
)


# -----------------------------
# Sidebar
# -----------------------------

with st.sidebar:
    st.header("Investigation")

    server_name = st.text_input(
        "Server",
        value="web-03",
        help="Infrastructure server to investigate.",
    )

    incident_date = st.date_input(
        "Incident date",
        value=datetime(2026, 9, 12).date(),
    )

    start_time = st.time_input(
        "Incident start",
        value=datetime(2026, 9, 12, 14, 30).time(),
    )

    end_time = st.time_input(
        "Incident end",
        value=datetime(2026, 9, 12, 14, 40).time(),
    )

    investigate_button = st.button(
        "🔎 Investigate Incident",
        type="primary",
        use_container_width=True,
    )

    st.divider()

    st.markdown("### System")

    st.success("Exasol connected")
    st.info("SQL safety gate enabled")
    st.info("Evidence-backed analysis")


# -----------------------------
# Main investigation
# -----------------------------

if investigate_button:

    start_datetime = datetime.combine(
        incident_date,
        start_time,
    )

    end_datetime = datetime.combine(
        incident_date,
        end_time,
    )

    if start_datetime >= end_datetime:
        st.error("Incident start time must be before the end time.")
        st.stop()

    with st.spinner("Investigating incident using Exasol evidence..."):

        query_start = time.perf_counter()

        try:
            result = investigate_and_report(
                server_name=server_name,
                start_time=start_datetime,
                end_time=end_datetime,
            )

            query_time = time.perf_counter() - query_start

        except Exception as exc:
            st.error(f"Investigation failed: {exc}")
            st.stop()

    evidence = result["evidence"]
    events = result["events"]

    # -------------------------
    # Incident status
    # -------------------------

    st.divider()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Server",
            evidence["server_name"],
        )

    with col2:
        st.metric(
            "Confidence",
            evidence["investigation_confidence"],
        )

    with col3:
        st.metric(
            "Critical Events",
            int(evidence["critical_event_count"]),
        )

    with col4:
        st.metric(
            "Query Time",
            f"{query_time * 1000:.1f} ms",
        )

    # -------------------------
    # Metrics
    # -------------------------

    st.subheader("Incident Signals")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "CPU",
            f"{evidence['incident_cpu']:.2f}%",
            f"+{evidence['cpu_change_pct']:.2f}%",
        )

    with col2:
        st.metric(
            "Memory",
            f"{evidence['incident_memory']:.2f}%",
            f"{evidence['incident_memory'] - evidence['baseline_memory']:.2f} pts",
        )

    with col3:
        st.metric(
            "Latency",
            f"{evidence['incident_response_ms']:.2f} ms",
            f"{evidence['response_multiplier']:.2f}×",
        )

    with col4:
        st.metric(
            "Error Rate",
            f"{evidence['incident_error_rate']:.2f}%",
            f"{evidence['error_multiplier']:.2f}×",
        )

    with col5:
        st.metric(
            "HTTP 5xx",
            f"{evidence['incident_http_5xx']:.2f}",
            f"{evidence['http5xx_multiplier']:.2f}×",
        )

    # -------------------------
    # AI investigation
    # -------------------------

    st.divider()

    st.subheader("🤖 Investigation Report")

    st.markdown(result["report"])

    # -------------------------
    # Timeline
    # -------------------------

    st.divider()

    st.subheader("Incident Timeline")

    if events:
        for event in events:

            severity = str(event["severity"]).upper()

            if severity == "CRITICAL":
                st.error(
                    f"**{event['event_time']}** — "
                    f"{event['message']}"
                )

            elif severity == "WARNING":
                st.warning(
                    f"**{event['event_time']}** — "
                    f"{event['message']}"
                )

            else:
                st.info(
                    f"**{event['event_time']}** — "
                    f"{event['message']}"
                )

    else:
        st.info("No correlated operational events were found.")

    # -------------------------
    # Evidence / SQL
    # -------------------------

    st.divider()

    with st.expander("🔐 Exasol Evidence & SQL"):

        st.markdown(
            "**SQL safety:** "
            "Read-only validation passed before execution."
        )

        st.code(
            result["investigation_sql"],
            language="sql",
        )

        st.code(
            result["events_sql"],
            language="sql",
        )

        st.markdown("### Raw Evidence")

        st.json(evidence)

        st.markdown("### Correlated Events")

        st.json(events)

    # -------------------------
    # Footer
    # -------------------------

    st.divider()

    st.caption(
        f"Investigation completed in {query_time * 1000:.1f} ms · "
        "Data source: Exasol Personal · "
        "OpsIntel read-only safety policy active"
    )

else:

    st.info(
        "Select an incident and click **Investigate Incident** "
        "to begin."
    )

    st.markdown(
        """
### What OpsIntel does

OpsIntel combines infrastructure telemetry and operational events
stored in **Exasol** to investigate incidents.

**Investigation flow**

`Infrastructure data → Exasol → SQL analytics → Safety gate → AI reasoning → Incident report`

The system compares incident metrics against a historical baseline,
correlates operational events, and produces an evidence-backed
investigation report.
"""
    )
