
"""
SPACECARE - Subsystem 8: Health & Mission Reports
Generates, stores and exports astronaut health reports.
"""

import streamlit as st
import json
from io import BytesIO
from datetime import datetime
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.queries import (
    get_latest_vitals,
    get_vitals_history,
    get_mental_health_history,
    get_active_alerts,
    save_health_report,
    get_reports_for_astronaut,
)

from src.components.mission_header import (
    render_mission_header,
    render_crew_selector_sidebar,
)
from src.components.disclaimers import (
    render_medical_disclaimer,
    render_sidebar_disclaimer,
)
from src.components.badges import render_provenance_badge


st.set_page_config(
    page_title="SPACECARE | Health Reports",
    page_icon="📋",
    layout="wide",
)

render_mission_header("Mission & Clinical Health Reports")
render_medical_disclaimer(compact=True)

selected_astronaut = render_crew_selector_sidebar()
render_sidebar_disclaimer()

st.markdown("### 📋 Flight Surgeon Mission Health Briefs")
render_provenance_badge(
    "simulated",
    "Automated Mission Health Summary Engine",
)

# -------------------------------------------------------------------
# Report generation helper
# -------------------------------------------------------------------

def build_report_markdown(astronaut, report):
    """Create a readable Markdown health report."""

    vitals = report["vitals"]
    mental = report["mental_health"]
    alerts = report["alerts"]

    lines = [
        "# SPACECARE - Flight Surgeon Mission Health Report",
        "",
        f"**Astronaut:** {astronaut['name']}",
        f"**Callsign:** {astronaut['callsign']}",
        f"**Mission:** {astronaut.get('mission', 'Not specified')}",
        f"**Mission Day:** {report['mission_day']}",
        f"**Generated:** {report['generated_at']}",
        f"**Overall Status:** {report['overall_status']}",
        "",
        "## Executive Summary",
        report["executive_summary"],
        "",
        "## Latest Vital Signs",
    ]

    if vitals:
        fields = [
            ("Heart Rate", "heart_rate", "bpm"),
            ("Systolic BP", "blood_pressure_sys", "mmHg"),
            ("Diastolic BP", "blood_pressure_dia", "mmHg"),
            ("SpO2", "spo2", "%"),
            ("Core Temperature", "core_temperature", "°C"),
            ("Respiration Rate", "respiration_rate", "/min"),
            ("HRV RMSSD", "hrv_rmssd", "ms"),
        ]

        for label, key, unit in fields:
            lines.append(f"- **{label}:** {vitals.get(key, 'N/A')} {unit}")

        lines.append(f"- **ECG Status:** {vitals.get('ecg_status', 'N/A')}")
        lines.append(f"- **Reading Timestamp:** {vitals.get('timestamp', 'N/A')}")
        lines.append(
            f"- **Reading Source:** "
            f"{'Simulated' if vitals.get('is_simulated', 1) else 'Non-simulated'}"
        )
    else:
        lines.append("No vital-sign records available.")

    lines.extend(["", "## Mental Health & Sleep"])

    if mental:
        lines.extend([
            f"- Sleep duration: {mental.get('sleep_duration_hours', 'N/A')} hours",
            f"- Sleep efficiency: {mental.get('sleep_efficiency_pct', 'N/A')}%",
            f"- Circadian drift: {mental.get('circadian_drift_hours', 'N/A')} hours",
            f"- Overall NASA-TLX score: {mental.get('overall_tlx_score', 'N/A')}",
            f"- Fatigue risk index: {mental.get('fatigue_risk_index', 'N/A')}",
            f"- Stress level: {mental.get('stress_level', 'N/A')}",
        ])
    else:
        lines.append("No mental-health records available.")

    lines.extend([
        "",
        "## Alerts",
        f"Total active alerts: {len(alerts)}",
    ])

    if alerts:
        for alert in alerts:
            lines.extend([
                f"- **{alert.get('severity', 'N/A')} - "
                f"{alert.get('title', 'Alert')}**",
                f"  {alert.get('message', '')}",
            ])
    else:
        lines.append("No active alerts found for this astronaut.")

    lines.extend([
        "",
        "## Anomaly Summary",
        f"Anomalies in retrieved vitals history: {report['anomalies_count']}",
        "",
        "## Data Limitations",
        "- Radiation accumulation is not included because a verified "
        "astronaut-specific cumulative dose was not available.",
        "- This report uses the latest available database records.",
        "- Simulated readings are identified as simulated.",
        "- This is a research prototype, not a clinical diagnosis.",
        "",
        "## Recommendations",
        report["recommendations"],
        "",
        "---",
        "**SPACECARE Research Prototype - Not for clinical decision-making.**",
    ])

    return "\n".join(lines)


def create_pdf(markdown_text):
    """Create a PDF report using ReportLab."""

    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
    )
    from reportlab.lib.units import mm
    from xml.sax.saxutils import escape

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )

    styles = getSampleStyleSheet()
    story = []

    for line in markdown_text.splitlines():
        line = line.strip()

        if not line or line == "---":
            story.append(Spacer(1, 6))
            continue

        if line.startswith("# "):
            story.append(Paragraph(escape(line[2:]), styles["Title"]))
        elif line.startswith("## "):
            story.append(Paragraph(escape(line[3:]), styles["Heading2"]))
        else:
            line = escape(line)
            line = line.replace("**", "")
            story.append(Paragraph(line, styles["BodyText"]))

        story.append(Spacer(1, 4))

    document.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# -------------------------------------------------------------------
# Main page
# -------------------------------------------------------------------

if selected_astronaut:

    astronaut_id = selected_astronaut["id"]
    astronaut_name = selected_astronaut["name"]

    st.markdown(
        f"**Selected Astronaut:** "
        f"`{astronaut_name} ({selected_astronaut['callsign']})`"
    )

    st.divider()

    st.markdown("#### Generate New Health Report")

    mission_day = st.number_input(
        "Mission Day",
        min_value=0,
        max_value=2000,
        value=42,
        step=1,
    )

    if st.button(
        "📄 Generate Health Report",
        type="primary",
        use_container_width=True,
    ):

        latest_vitals = get_latest_vitals(astronaut_id)
        vitals_history = get_vitals_history(astronaut_id, limit=100)
        mental_history = get_mental_health_history(
            astronaut_id,
            limit=30,
        )

        all_alerts = get_active_alerts(limit=100)

        astronaut_alerts = [
            alert for alert in all_alerts
            if alert.get("astronaut_id") == astronaut_id
        ]

        latest_mental = (
            mental_history[-1] if mental_history else None
        )

        anomaly_count = sum(
            int(row.get("anomaly_flag") or 0)
            for row in vitals_history
        )

        critical_count = sum(
            1 for alert in astronaut_alerts
            if alert.get("severity") == "CRITICAL"
        )

        warning_count = sum(
            1 for alert in astronaut_alerts
            if alert.get("severity") == "WARNING"
        )

        if critical_count:
           overall_status = "CRITICAL"
        elif warning_count:
           overall_status = "WARNING"
        elif astronaut_alerts:
          overall_status = "ADVISORY"
        else:
          overall_status = "NOMINAL"
        generated_at = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        summary = (
            f"Health report generated for {astronaut_name}. "
            f"Overall prototype status: {overall_status}. "
            f"{len(astronaut_alerts)} active alerts were found. "
            f"{anomaly_count} anomaly-flagged records were found "
            f"in the retrieved vitals history."
        )

        if not latest_vitals:
            summary += " No vital-sign records were available."

        if not latest_mental:
            summary += " No mental-health records were available."

        recommendations = (
            "Review the displayed vital signs, anomaly records and "
            "active alerts. Verify simulated readings against their "
            "source labels. Review sleep and fatigue information "
            "when available. This prototype does not provide "
            "medical treatment recommendations."
        )

        report_data = {
            "mission_day": int(mission_day),
            "generated_at": generated_at,
            "overall_status": overall_status,
            "executive_summary": summary,
            "vitals": latest_vitals,
            "mental_health": latest_mental,
            "alerts": astronaut_alerts,
            "anomalies_count": anomaly_count,
            "radiation_data_available": False,
        }

        vitals_json = json.dumps(
            report_data,
            default=str,
        )

        try:
            report_id = save_health_report(
                astronaut_id=astronaut_id,
                report_title=f"Mission Health Report - {astronaut_name}",
                mission_day=int(mission_day),
                overall_status=overall_status,
                executive_summary=summary,
                vitals_summary_json=vitals_json,
                anomalies_detected_count=anomaly_count,
                radiation_accumulated_msv=0.0,
                recommendations=recommendations,
            )

            st.session_state["generated_report"] = {
                "id": report_id,
                "astronaut": selected_astronaut,
                "data": report_data,
                "recommendations": recommendations,
            }

            st.success(
                f"Report #{report_id} generated and saved successfully!"
            )

        except Exception as error:
            st.error(f"Report generation failed: {error}")


# -------------------------------------------------------------------
# Display generated report and download options
# -------------------------------------------------------------------

if "generated_report" in st.session_state:

    saved = st.session_state["generated_report"]
    report_data = saved["data"]

    # Only show the current report when it belongs to the selected astronaut.
    if (
        selected_astronaut
        and saved["astronaut"]["id"] == selected_astronaut["id"]
    ):

        markdown_report = build_report_markdown(
            saved["astronaut"],
            {
                **report_data,
                "recommendations": saved["recommendations"],
            },
        )

        st.divider()
        st.markdown("### 📄 Generated Health Report")

        st.markdown(markdown_report)

        safe_name = (
            saved["astronaut"]["callsign"]
            .replace(" ", "_")
            .replace("/", "_")
        )

        st.download_button(
            "⬇️ Download Markdown Report",
            data=markdown_report,
            file_name=f"SPACECARE_{safe_name}_health_report.md",
            mime="text/markdown",
            use_container_width=True,
        )

        try:
            pdf_bytes = create_pdf(markdown_report)

            st.download_button(
                "⬇️ Download PDF Report",
                data=pdf_bytes,
                file_name=f"SPACECARE_{safe_name}_health_report.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

        except ImportError:
            st.warning(
                "PDF export requires ReportLab. "
                "Markdown download is available."
            )

        except Exception as error:
            st.warning(f"PDF creation issue: {error}")


# -------------------------------------------------------------------
# Archived reports
# -------------------------------------------------------------------

if selected_astronaut:

    st.divider()
    st.markdown("### 📚 Archived Health Reports")

    reports = get_reports_for_astronaut(
        selected_astronaut["id"]
    )

    if reports:

        for report in reports:

            with st.expander(
                f"📄 {report['report_title']} "
                f"- Mission Day {report['mission_day']}"
            ):

                st.markdown(
                    f"**Generated:** {report['generated_at']}"
                )
                st.markdown(
                    f"**Status:** {report['overall_status']}"
                )
                st.write(report["executive_summary"])

                st.write(
                    f"**Anomalies detected:** "
                    f"{report['anomalies_detected_count']}"
                )

    else:
        st.info("No archived reports yet. Generate your first report above.")


st.caption(
    "SPACECARE is a research and aerospace simulation prototype. "
    "Reports are generated from available database records and are "
    "not certified clinical documents."
)
