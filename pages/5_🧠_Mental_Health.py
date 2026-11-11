"""
SPACECARE - Subsystem 5: Mental Health & Cognitive Load
Circadian rhythm drift, sleep architecture, and NASA Task Load Index (NASA-TLX).

DISCLAIMER: All calculations and assessments presented here are SYNTHETIC
behavioral models for aerospace engineering and educational simulation.
"""

import streamlit as st
import plotly.graph_objects as go
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.mental_health.sleep_tracker import simulate_sleep_profile, generate_sleep_history
from src.mental_health.tlx_assessment import calculate_raw_tlx, calculate_fatigue_risk_index
from src.database.queries import log_mental_health, get_mental_health_history, create_alert
from src.alerts.protocols import get_protocol
from src.components.mission_header import render_mission_header, render_crew_selector_sidebar
from src.components.disclaimers import render_medical_disclaimer, render_sidebar_disclaimer
from src.components.badges import render_provenance_badge
from src.components.metrics_card import render_metric_card

st.set_page_config(page_title="SPACECARE | Mental Health", page_icon="🧠", layout="wide")

# Mission Header & Persistent Disclaimers
render_mission_header("Mental Health & Cognitive Load Console")
render_medical_disclaimer(compact=True)
selected_astronaut = render_crew_selector_sidebar()
render_sidebar_disclaimer()

# Mandatory Provenance Notice
render_provenance_badge("simulated", "Actigraphy & NASA-TLX Cognitive Workload Model")

if not selected_astronaut:
    st.warning("⚠️ No crew members available. Register astronauts in the Crew Configuration console.")
    st.stop()

ast_id = selected_astronaut["id"]
ast_name = selected_astronaut["name"]
ast_callsign = selected_astronaut["callsign"]

st.markdown(
    """
    <div style="background: rgba(11, 61, 145, 0.15); border: 1px solid rgba(59, 130, 246, 0.35); border-radius: 8px; padding: 12px 18px; margin-bottom: 20px; font-size: 0.86rem; color: #cbd5e1; line-height: 1.5;">
        🧠 <strong>AEROSPACE NEUROBEHAVIORAL HEALTH:</strong><br>
        Astronauts aboard the ISS experience 16 sunrises and sunsets every 24 hours (a 90-minute orbital period),
        which induces circadian phase drift and sleep debt. This console tracks simulated actigraphy sleep architecture,
        circadian misalignment, and the standardized <strong>NASA Task Load Index (NASA-TLX)</strong> cognitive workload.
    </div>
    """,
    unsafe_allow_html=True
)

tab_sleep, tab_tlx, tab_logs = st.tabs([
    "🛌 Sleep Architecture & Circadian Phase",
    "📝 NASA-TLX Workload Assessment",
    "📋 Longitudinal Assessment Archive"
])

# ============================================================================
# TAB 1: Sleep Architecture & Circadian Phase
# ============================================================================
with tab_sleep:
    st.markdown(f"#### 🛌 14-Day Actigraphy Sleep Profile: **{ast_name}** (`{ast_callsign}`)")

    sleep_data = generate_sleep_history(ast_id, days=14)
    latest_sleep = sleep_data[-1]

    # Metrics Row
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        s_dur = latest_sleep["sleep_duration_hours"]
        render_metric_card("Sleep Duration", f"{s_dur:.1f}", "hrs", "nominal" if s_dur >= 7.0 else "warning", "Target: 7.0 - 8.5 hrs")
    with m2:
        s_eff = latest_sleep["sleep_efficiency_pct"]
        render_metric_card("Sleep Efficiency", f"{s_eff:.1f}", "%", "nominal" if s_eff >= 85.0 else "warning", "Target: > 85.0 %")
    with m3:
        drift = latest_sleep["circadian_drift_hours"]
        render_metric_card("Circadian Phase Shift", f"{drift:+.2f}", "hrs", "warning" if abs(drift) > 1.5 else "nominal", "Target: < ±1.0 hr")
    with m4:
        debt = latest_sleep["sleep_debt_hours"]
        render_metric_card("Cumulative Sleep Debt", f"{debt:.1f}", "hrs", "warning" if debt > 2.0 else "nominal", "Target: < 1.0 hr")

    # Plotly Charts
    dates = [s["timestamp"].split()[0] for s in sleep_data]
    durations = [s["sleep_duration_hours"] for s in sleep_data]
    efficiencies = [s["sleep_efficiency_pct"] for s in sleep_data]
    drifts = [s["circadian_drift_hours"] for s in sleep_data]

    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        fig_sleep = go.Figure()
        fig_sleep.add_trace(go.Bar(
            x=dates, y=durations, name="Sleep Duration (hrs)",
            marker_color="#38bdf8"
        ))
        fig_sleep.add_hline(y=7.0, line_dash="dash", line_color="rgba(16, 185, 129, 0.8)", annotation_text="Minimum Rest Target (7.0 hrs)")
        fig_sleep.add_hline(y=6.0, line_dash="dash", line_color="rgba(239, 68, 68, 0.8)", annotation_text="Fatigue Threshold (6.0 hrs)")
        fig_sleep.update_layout(
            title="Actigraphy Sleep Duration (14-Day Timeline)",
            height=300,
            template="plotly_dark",
            paper_bgcolor="#0f172a",
            plot_bgcolor="#0f172a",
            yaxis=dict(range=[4.0, 10.0]),
            margin=dict(l=30, r=20, t=40, b=30)
        )
        st.plotly_chart(fig_sleep, use_container_width=True)

    with col_chart2:
        fig_drift = go.Figure()
        fig_drift.add_trace(go.Scatter(
            x=dates, y=drifts, mode="lines+markers", name="Circadian Drift (hrs)",
            line=dict(color="#ec4899", width=2.5), marker=dict(size=6)
        ))
        fig_drift.add_hline(y=1.5, line_dash="dot", line_color="rgba(245, 158, 11, 0.7)", annotation_text="+1.5h Desynchrony Alert")
        fig_drift.add_hline(y=-1.5, line_dash="dot", line_color="rgba(245, 158, 11, 0.7)", annotation_text="-1.5h Desynchrony Alert")
        fig_drift.update_layout(
            title="Circadian Phase Angle Shift (Orbital Drift)",
            height=300,
            template="plotly_dark",
            paper_bgcolor="#0f172a",
            plot_bgcolor="#0f172a",
            yaxis=dict(range=[-3.0, 3.0], title="Phase Angle Offset (Hours)"),
            margin=dict(l=30, r=20, t=40, b=30)
        )
        st.plotly_chart(fig_drift, use_container_width=True)

# ============================================================================
# TAB 2: NASA Task Load Index (NASA-TLX) Survey
# ============================================================================
with tab_tlx:
    st.markdown("#### 📝 Standardized NASA-TLX Cognitive Workload Questionnaire")
    st.markdown(
        """
        The **NASA Task Load Index (NASA-TLX)** is an aerospace psychometric instrument assessing subjective workload 
        across six operational subscales on a 100-point scale.
        """
    )

    with st.form("form_nasa_tlx"):
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            tlx_mental = st.slider("1. Mental Demand (Thinking, deciding, calculating, remembering)", 0.0, 100.0, 45.0, step=5.0)
            tlx_physical = st.slider("2. Physical Demand (Pushing, pulling, turning, controlling)", 0.0, 100.0, 35.0, step=5.0)
            tlx_temporal = st.slider("3. Temporal Demand (Time pressure, pace of operations)", 0.0, 100.0, 40.0, step=5.0)

        with col_t2:
            tlx_perf = st.slider("4. Performance Difficulty (Level of dissatisfaction with performance)", 0.0, 100.0, 20.0, step=5.0)
            tlx_effort = st.slider("5. Effort (How hard you worked to achieve your level of performance)", 0.0, 100.0, 50.0, step=5.0)
            tlx_frust = st.slider("6. Frustration Level (Insecure, discouraged, irritated vs content)", 0.0, 100.0, 15.0, step=5.0)

        notes_input = st.text_input("Operational Context / Flight Notes:", placeholder="e.g. Conducted SSRMS robotic arm berthing maneuver during orbital night.")
        submit_tlx = st.form_submit_button("Record NASA-TLX Assessment", type="primary")

    if submit_tlx:
        raw_tlx = calculate_raw_tlx(tlx_mental, tlx_physical, tlx_temporal, tlx_perf, tlx_effort, tlx_frust)
        fatigue_risk, risk_category = calculate_fatigue_risk_index(
            tlx_score=raw_tlx,
            sleep_duration_hours=latest_sleep["sleep_duration_hours"],
            sleep_efficiency_pct=latest_sleep["sleep_efficiency_pct"],
            circadian_drift_hours=latest_sleep["circadian_drift_hours"]
        )

        stress_label = "High" if fatigue_risk > 65 else ("Moderate" if fatigue_risk > 35 else "Normal")

        # Save to SQLite database
        log_id = log_mental_health(
            astronaut_id=ast_id,
            sleep_duration_hours=latest_sleep["sleep_duration_hours"],
            sleep_efficiency_pct=latest_sleep["sleep_efficiency_pct"],
            circadian_drift_hours=latest_sleep["circadian_drift_hours"],
            nasa_tlx_mental=tlx_mental,
            nasa_tlx_physical=tlx_physical,
            nasa_tlx_temporal=tlx_temporal,
            nasa_tlx_performance=tlx_perf,
            nasa_tlx_effort=tlx_effort,
            nasa_tlx_frustration=tlx_frust,
            overall_tlx_score=raw_tlx,
            fatigue_risk_index=fatigue_risk,
            stress_level=stress_label,
            notes=notes_input
        )

        # Trigger Early Warning Alert if Fatigue is High
        if fatigue_risk > 65.0:
            proto = get_protocol("COGNITIVE_FATIGUE")
            create_alert(
                severity="WARNING",
                category="MENTAL_HEALTH",
                title=f"Critical Cognitive Fatigue: {ast_name}",
                message=f"Fatigue Risk Index reached {fatigue_risk:.1f}/100 (NASA-TLX: {raw_tlx:.1f}). Workload rest protocol required.",
                flight_surgeon_protocol="\n".join(proto["checklists"]),
                astronaut_id=ast_id,
                metric_name="fatigue_risk_index",
                metric_value=fatigue_risk,
                threshold_limit=65.0
            )
            st.warning(f"⚠️ High Cognitive Fatigue detected! Alert dispatched to Flight Surgeon console.")

        st.success(f"NASA-TLX Evaluation recorded successfully (Log ID: {log_id}). Raw TLX Score: {raw_tlx:.1f} • Fatigue Risk Index: {fatigue_risk:.1f} ({risk_category})")

# ============================================================================
# TAB 3: Longitudinal Assessment Archive
# ============================================================================
with tab_logs:
    st.markdown(f"#### 📋 Assessment Archive for **{ast_name}**")
    logs = get_mental_health_history(ast_id, limit=20)
    if logs:
        st.dataframe(logs, use_container_width=True)
    else:
        st.info("No prior assessments recorded for this astronaut. Complete a NASA-TLX survey to record entries.")
