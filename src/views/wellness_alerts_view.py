"""
SPACECARE View: Crew Mental Wellness, Early Warning Alerts & Medical Reports
(Member 3 - UI Workspace | src/views/)

Renders sleep architecture analytics, circadian/stress/fatigue tracking,
multi-severity alert triage, and clinical health report download.
All data sourced exclusively via data_adapter.py.
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from typing import Dict, Any

from src.components.data_adapter import (
    get_mental_wellness_data,
    get_active_alerts_and_protocols,
    generate_health_report,
)
from src.components.mission_header import render_mission_header
from src.components.disclaimers import render_medical_disclaimer
from src.components.metrics_card import render_metric_card
from src.components.badges import render_provenance_badge


# ── Severity colour palette ─────────────────────────────────────────────────
_SEV_COLORS = {
    "CRITICAL": "#ef4444",
    "WARNING": "#f59e0b",
    "ADVISORY": "#3b82f6",
    "INFO": "#64748b",
}
_SEV_ICONS = {
    "CRITICAL": "🔴",
    "WARNING": "🟡",
    "ADVISORY": "🔵",
    "INFO": "⚪",
}


def _status_for(value: float, low: float, high: float) -> str:
    """Return 'nominal', 'warning', or 'critical' for a metric."""
    if low <= value <= high:
        return "nominal"
    if value < low * 0.85 or value > high * 1.15:
        return "critical"
    return "warning"


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════
def render_wellness_alerts_view(
    astronaut_profile: Dict[str, Any],
    time_window_hours: int,
) -> None:
    """Full-page render of mental wellness analytics, alert triage, and reports."""

    ast_id = astronaut_profile.get("astronaut_id", "AST-01")
    ast_name = astronaut_profile.get("name", "Crew Member")

    render_mission_header("Crew Mental Wellness, Early Warning Alerts & Medical Reports")
    render_medical_disclaimer(compact=True)

    # ── Data acquisition ─────────────────────────────────────────────────
    wellness = get_mental_wellness_data(astronaut_id=ast_id, days=14)
    alerts_resp = get_active_alerts_and_protocols(astronaut_id=ast_id)
    report_resp = generate_health_report(astronaut_id=ast_id)

    w_df = wellness["data"]
    w_summary = wellness["summary"]
    alerts_list = alerts_resp["data"]
    a_summary = alerts_resp["summary"]

    # Data provenance
    w_source = wellness.get("source", "simulated_fallback")
    badge_type = "real" if w_source == "live" else "simulated"
    render_provenance_badge(badge_type, f"Mental Wellness Telemetry — {ast_name}")

    # ── TOP: Alert Ticker ────────────────────────────────────────────────
    if alerts_list:
        ticker_items = []
        for al in alerts_list[:8]:
            sev = al.get("severity", "INFO").upper()
            icon = _SEV_ICONS.get(sev, "⚪")
            color = _SEV_COLORS.get(sev, "#64748b")
            title = al.get("title", "Alert")
            ticker_items.append(
                f'<span style="color:{color}; margin-right:18px;">'
                f"{icon} <strong>[{sev}]</strong> {title}</span>"
            )
        st.markdown(
            f"""
            <div style="background: rgba(15, 23, 42, 0.85); border: 1px solid #1e293b;
                        border-radius: 8px; padding: 10px 16px; margin-bottom: 16px;
                        font-size: 0.82rem; overflow-x: auto; white-space: nowrap;">
                🚨 <strong style="color:#f8fafc;">Active Alerts:</strong>&ensp;
                {''.join(ticker_items)}
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.success("✅ No active alerts for this crew member.")

    # ── ROW 1: 4 KPI Cards ──────────────────────────────────────────────
    st.markdown("#### 🧠 Wellness Key Performance Indicators (14-Day Aggregate)")

    avg_sleep = w_summary.get("avg_total_sleep_hrs", 7.0)
    avg_quality = w_summary.get("avg_sleep_quality_score", 70.0)
    avg_circadian = w_summary.get("avg_circadian_alignment_pct", 80.0)
    avg_fatigue = w_summary.get("avg_fatigue_score", 35.0)
    avg_stress = w_summary.get("avg_stress_index", 30.0)

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    with kpi1:
        render_metric_card(
            "Sleep Duration",
            f"{avg_sleep:.1f}",
            unit="hrs/night",
            status=_status_for(avg_sleep, 6.0, 8.5),
            normal_range="6.0 – 8.5 hrs",
        )
    with kpi2:
        render_metric_card(
            "Sleep Quality",
            f"{avg_quality:.0f}",
            unit="/100",
            status=_status_for(avg_quality, 60, 100),
            normal_range="≥ 60 (NASA-STD-3001)",
        )
    with kpi3:
        render_metric_card(
            "Circadian Alignment",
            f"{avg_circadian:.0f}",
            unit="%",
            status=_status_for(avg_circadian, 70, 100),
            normal_range="≥ 70%",
        )
    with kpi4:
        composite = (avg_fatigue + avg_stress) / 2.0
        render_metric_card(
            "Fatigue / Stress",
            f"{composite:.0f}",
            unit="/100",
            status="nominal" if composite < 40 else ("warning" if composite < 65 else "critical"),
            normal_range="< 40 nominal",
            delta=f"F:{avg_fatigue:.0f} S:{avg_stress:.0f}",
        )

    # ── ROW 2: Sleep Architecture & Stress/Fatigue Trends ────────────────
    st.markdown("---")
    st.markdown("#### 😴 Sleep Architecture & Psychophysiological Trend Analysis")

    chart_left, chart_right = st.columns([3, 2])

    with chart_left:
        # 14-day stacked bar: deep / REM / light sleep
        if w_df is not None and not w_df.empty:
            dates = w_df["date"].astype(str).tolist()
            fig_sleep = go.Figure()
            fig_sleep.add_trace(go.Bar(
                x=dates,
                y=w_df["deep_sleep_hrs"],
                name="Deep Sleep",
                marker_color="#6366f1",
            ))
            fig_sleep.add_trace(go.Bar(
                x=dates,
                y=w_df["rem_sleep_hrs"],
                name="REM Sleep",
                marker_color="#8b5cf6",
            ))
            fig_sleep.add_trace(go.Bar(
                x=dates,
                y=w_df["light_sleep_hrs"],
                name="Light Sleep",
                marker_color="#a78bfa",
            ))
            fig_sleep.update_layout(
                barmode="stack",
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                title=dict(text="14-Day Sleep Architecture", font=dict(size=14, color="#f8fafc")),
                xaxis_title="Date",
                yaxis_title="Hours",
                height=340,
                margin=dict(t=40, b=40, l=50, r=20),
                legend=dict(orientation="h", y=-0.2),
            )
            # Add NASA recommended band
            fig_sleep.add_hline(
                y=7.0, line_dash="dash", line_color="#10b981",
                annotation_text="NASA Min (7 hrs)",
                annotation_position="top left",
                annotation_font_color="#10b981",
            )
            st.plotly_chart(fig_sleep, use_container_width=True, key="sleep_arch_chart")
        else:
            st.info("No sleep architecture data available.")

    with chart_right:
        # Dual-axis: stress_index & fatigue_score lines + interruption bars
        if w_df is not None and not w_df.empty:
            dates = w_df["date"].astype(str).tolist()
            fig_sf = make_subplots(specs=[[{"secondary_y": True}]])
            fig_sf.add_trace(
                go.Scatter(
                    x=dates, y=w_df["stress_index"],
                    name="Stress Index", mode="lines+markers",
                    line=dict(color="#ef4444", width=2),
                    marker=dict(size=5),
                ),
                secondary_y=False,
            )
            fig_sf.add_trace(
                go.Scatter(
                    x=dates, y=w_df["fatigue_score"],
                    name="Fatigue Score", mode="lines+markers",
                    line=dict(color="#f59e0b", width=2),
                    marker=dict(size=5),
                ),
                secondary_y=False,
            )
            fig_sf.add_trace(
                go.Bar(
                    x=dates, y=w_df["sleep_interruptions"],
                    name="Interruptions", marker_color="rgba(148,163,184,0.4)",
                    marker_line_width=0,
                ),
                secondary_y=True,
            )
            fig_sf.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                title=dict(text="Stress / Fatigue & Sleep Interruptions", font=dict(size=14, color="#f8fafc")),
                height=340,
                margin=dict(t=40, b=40, l=50, r=50),
                legend=dict(orientation="h", y=-0.25),
            )
            fig_sf.update_yaxes(title_text="Score (0-100)", secondary_y=False)
            fig_sf.update_yaxes(title_text="Interruptions", secondary_y=True)
            st.plotly_chart(fig_sf, use_container_width=True, key="stress_fatigue_chart")
        else:
            st.info("No stress / fatigue trend data available.")

    # ── ROW 3: Alert Triage & Health Report ──────────────────────────────
    st.markdown("---")
    st.markdown("#### ⚠️ Alert Triage Console & 📋 Health Report")

    col_alerts, col_report = st.columns([3, 2])

    with col_alerts:
        st.markdown("##### 🚨 Active Alerts & Recommended Protocols")

        # Severity filter pills
        sev_options = ["ALL", "CRITICAL", "WARNING", "ADVISORY", "INFO"]
        selected_sev = st.radio(
            "Filter by Severity:",
            sev_options,
            horizontal=True,
            key="alert_sev_filter",
        )

        # Category filter
        all_categories = sorted(set(al.get("category", "GENERAL") for al in alerts_list)) if alerts_list else []
        if all_categories:
            selected_cat = st.selectbox(
                "Filter by Category:",
                ["ALL"] + all_categories,
                key="alert_cat_filter",
            )
        else:
            selected_cat = "ALL"

        # Filter alerts
        filtered = alerts_list
        if selected_sev != "ALL":
            filtered = [a for a in filtered if a.get("severity", "").upper() == selected_sev]
        if selected_cat != "ALL":
            filtered = [a for a in filtered if a.get("category", "") == selected_cat]

        total_count = a_summary.get("total_alerts", len(alerts_list))
        crit_count = a_summary.get("critical_count", 0)
        warn_count = a_summary.get("warning_count", 0)

        st.caption(
            f"Showing **{len(filtered)}** of **{total_count}** alerts  "
            f"(🔴 {crit_count} Critical · 🟡 {warn_count} Warning)"
        )

        if filtered:
            for al in filtered:
                sev = al.get("severity", "INFO").upper()
                icon = _SEV_ICONS.get(sev, "⚪")
                color = _SEV_COLORS.get(sev, "#64748b")
                title = al.get("title", "Untitled Alert")
                ts = al.get("timestamp", "")
                desc = al.get("description", "No details available.")
                trigger = al.get("trigger_metric", "")
                protocol = al.get("recommended_protocol", "")

                # Alert card
                st.markdown(
                    f"""
                    <div style="background: rgba(15, 23, 42, 0.8); border-left: 4px solid {color};
                                border-radius: 6px; padding: 12px 16px; margin-bottom: 10px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="color:{color}; font-weight:700; font-size:0.9rem;">
                                {icon} [{sev}] {title}
                            </span>
                            <span style="color:#64748b; font-size:0.72rem;">{ts}</span>
                        </div>
                        <div style="color:#cbd5e1; font-size:0.82rem; margin-top:6px;">{desc}</div>
                        <div style="color:#94a3b8; font-size:0.74rem; margin-top:4px;">
                            Trigger: <code>{trigger}</code>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Expandable protocol checklist
                if protocol:
                    with st.expander(f"📋 Recommended Protocol — {title}", expanded=False):
                        protocol_lines = protocol.split("\n") if isinstance(protocol, str) else [str(protocol)]
                        for line in protocol_lines:
                            line = line.strip()
                            if line:
                                st.markdown(f"- {line}")
        else:
            st.info("No alerts match current filter criteria.")

    with col_report:
        st.markdown("##### 📋 Clinical Health Report")

        report_data = report_resp.get("data", {})
        report_md = report_data.get("markdown_report", "Report generation unavailable.")
        report_json = report_data.get("json_digest", {})
        report_source = report_resp.get("source", "simulated_fallback")

        report_badge = "real" if report_source == "live" else "simulated"
        render_provenance_badge(report_badge, f"Health Report Engine — {ast_name}")

        with st.expander("📄 Report Preview", expanded=True):
            st.markdown(
                f"""
                <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid #1e293b;
                            border-radius: 8px; padding: 14px; font-size: 0.82rem;
                            color: #e2e8f0; max-height: 400px; overflow-y: auto;">
                    {report_md.replace(chr(10), '<br>')}
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Download buttons
        st.markdown("")  # spacer
        dl_col1, dl_col2 = st.columns(2)
        with dl_col1:
            st.download_button(
                label="⬇️ Download .md",
                data=report_md,
                file_name=f"SPACECARE_Report_{ast_id}.md",
                mime="text/markdown",
                use_container_width=True,
                key="dl_report_md",
            )
        with dl_col2:
            st.download_button(
                label="⬇️ Download .json",
                data=json.dumps(report_json, indent=2, default=str),
                file_name=f"SPACECARE_Report_{ast_id}.json",
                mime="application/json",
                use_container_width=True,
                key="dl_report_json",
            )

        # Summary stats
        st.markdown("")
        st.markdown(
            f"""
            <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid #1e293b;
                        border-radius: 6px; padding: 10px; font-size: 0.76rem; color: #94a3b8;">
                <strong>Report Metadata:</strong><br>
                Astronaut: {ast_name} ({ast_id})<br>
                Source: <span style="color:{'#10b981' if report_source == 'live' else '#f59e0b'};">
                    {report_source.upper().replace('_', ' ')}</span><br>
                Status Note: {report_resp.get('status_note', 'N/A')}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── Footer ───────────────────────────────────────────────────────────
    st.markdown("---")
    render_medical_disclaimer(compact=True)
