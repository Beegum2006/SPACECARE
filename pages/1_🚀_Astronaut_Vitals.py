"""
SPACECARE - Subsystem 1: Astronaut Vitals Dashboard
Live simulated vital signs monitoring, Plotly telemetry charts, ECG rhythm strip,
and interactive spaceflight anomaly injection controls.

DISCLAIMER: All data presented here is SYNTHETIC and generated via physiological
simulation algorithms. It is NOT real NASA flight telemetry and NOT a medical diagnostic tool.
"""

import streamlit as st
import plotly.graph_objects as go
from pathlib import Path
import sys
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.queries import (
    get_astronauts, get_latest_vitals, get_vitals_history, log_vitals
)
from src.simulation.vitals_generator import (
    generate_vitals_snapshot, generate_vitals_series, generate_synthetic_ecg_trace, ANOMALY_MODES
)
from src.components.mission_header import render_mission_header, render_crew_selector_sidebar
from src.components.disclaimers import render_medical_disclaimer, render_sidebar_disclaimer
from src.components.badges import render_provenance_badge
from src.components.metrics_card import render_metric_card
from src.ml.service import analyze_astronaut
from src.alerts.alert_engine import evaluate_vitals_for_alerts

st.set_page_config(page_title="SPACECARE | Astronaut Vitals", page_icon="🚀", layout="wide")

# Mission Header & Persistent Disclaimers
render_mission_header("Astronaut Vital Signs Console")
render_medical_disclaimer(compact=True)
selected_astronaut = render_crew_selector_sidebar()
render_sidebar_disclaimer()

# Mandatory Provenance Notice
render_provenance_badge("simulated", "Physiological Stochastic Simulation Engine & Synthetic Telemetry Bus")

if not selected_astronaut:
    st.warning("⚠️ No crew members available. Register astronauts in the Crew Configuration console.")
    st.stop()

ast_id = selected_astronaut["id"]
ast_name = selected_astronaut["name"]
ast_callsign = selected_astronaut["callsign"]

# Ensure at least some initial history exists for the selected astronaut
history = get_vitals_history(ast_id, limit=60)
if not history:
    # Seed initial 30 nominal telemetry readings
    initial_series = generate_vitals_series(selected_astronaut, count=30, interval_seconds=10, anomaly_mode="NOMINAL")
    for r in initial_series:
        log_vitals(
            astronaut_id=ast_id,
            heart_rate=r["heart_rate"],
            blood_pressure_sys=r["blood_pressure_sys"],
            blood_pressure_dia=r["blood_pressure_dia"],
            spo2=r["spo2"],
            core_temperature=r["core_temperature"],
            respiration_rate=r["respiration_rate"],
            hrv_rmssd=r["hrv_rmssd"],
            ecg_status=r["ecg_status"],
            is_simulated=1,
            anomaly_score=r["anomaly_score"],
            anomaly_flag=r["anomaly_flag"]
        )
    history = get_vitals_history(ast_id, limit=60)

latest = history[-1] if history else None

# 1. Run ML anomaly detection
ml_result = analyze_astronaut(
    astronaut=selected_astronaut,
    history=history
)

# 2. Extract ML prediction
ml_prediction = ml_result["prediction"]

# 3. Evaluate clinical and ML alerts
alert_ids = []
if latest:
    alert_ids = evaluate_vitals_for_alerts(
        astronaut=selected_astronaut,
        reading=latest,
        ml_result=ml_prediction
    )

# 4. Store results for dashboard display
st.session_state["ml_result"] = ml_result
st.session_state["ml_prediction"] = ml_prediction
st.session_state["generated_alert_ids"] = alert_ids

# ML Anomaly Detection Results
st.divider()
st.markdown("### 🤖 Machine Learning Anomaly Detection")

ml_col1, ml_col2, ml_col3 = st.columns(3)

with ml_col1:
    st.metric(
        "ML Status",
        ml_prediction.get("status", "UNKNOWN")
    )

with ml_col2:
    st.metric(
        "Anomaly Severity",
        f"{ml_prediction.get('normalized_severity', 0):.3f}"
    )

with ml_col3:
    st.metric(
        "Alerts Generated",
        len(alert_ids)
    )

st.write("**ML Explanation:**", ml_prediction.get("explanation", "N/A"))
st.write("**Training Source:**", ml_result.get("training_source", "N/A"))
st.write("**Training Samples:**", ml_result.get("training_samples", 0))

# ============================================================================
# Telemetry Controls & Anomaly Injection Bar
# ============================================================================
with st.container():
    st.markdown("#### ⚡ Telemetry Stream & Anomaly Injection Controls")
    ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4 = st.columns([2, 2, 1.5, 1.5])

    with ctrl_col1:
        anomaly_selection = st.selectbox(
            "Induce Simulated Scenario:",
            ANOMALY_MODES,
            index=0,
            help="Choose an operational or emergency physiological scenario to simulate."
        )

    with ctrl_col2:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button("📡 Stream Single Telemetry Tick", type="primary", use_container_width=True):
            reading = generate_vitals_snapshot(selected_astronaut, anomaly_mode=anomaly_selection)
            log_vitals(
                astronaut_id=ast_id,
                heart_rate=reading["heart_rate"],
                blood_pressure_sys=reading["blood_pressure_sys"],
                blood_pressure_dia=reading["blood_pressure_dia"],
                spo2=reading["spo2"],
                core_temperature=reading["core_temperature"],
                respiration_rate=reading["respiration_rate"],
                hrv_rmssd=reading["hrv_rmssd"],
                ecg_status=reading["ecg_status"],
                is_simulated=1,
                anomaly_score=reading["anomaly_score"],
                anomaly_flag=reading["anomaly_flag"]
            )
            st.rerun()

    with ctrl_col3:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button("⏩ Simulate 20-Point Burst", use_container_width=True):
            burst = generate_vitals_series(
                selected_astronaut, count=20, interval_seconds=5, anomaly_mode=anomaly_selection, anomaly_onset_index=5
            )
            for r in burst:
                log_vitals(
                    astronaut_id=ast_id,
                    heart_rate=r["heart_rate"],
                    blood_pressure_sys=r["blood_pressure_sys"],
                    blood_pressure_dia=r["blood_pressure_dia"],
                    spo2=r["spo2"],
                    core_temperature=r["core_temperature"],
                    respiration_rate=r["respiration_rate"],
                    hrv_rmssd=r["hrv_rmssd"],
                    ecg_status=r["ecg_status"],
                    is_simulated=1,
                    anomaly_score=r["anomaly_score"],
                    anomaly_flag=r["anomaly_flag"]
                )
            st.rerun()

    with ctrl_col4:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button("🔄 Reset to Nominal Series", use_container_width=True):
            reset_series = generate_vitals_series(selected_astronaut, count=30, interval_seconds=10, anomaly_mode="NOMINAL")
            for r in reset_series:
                log_vitals(
                    astronaut_id=ast_id,
                    heart_rate=r["heart_rate"],
                    blood_pressure_sys=r["blood_pressure_sys"],
                    blood_pressure_dia=r["blood_pressure_dia"],
                    spo2=r["spo2"],
                    core_temperature=r["core_temperature"],
                    respiration_rate=r["respiration_rate"],
                    hrv_rmssd=r["hrv_rmssd"],
                    ecg_status=r["ecg_status"],
                    is_simulated=1,
                    anomaly_score=r["anomaly_score"],
                    anomaly_flag=r["anomaly_flag"]
                )
            st.rerun()

st.divider()

# ============================================================================
# Real-Time Telemetry Cards
# ============================================================================
if latest:
    hr_val = latest["heart_rate"]
    spo2_val = latest["spo2"]
    sys_val = latest["blood_pressure_sys"]
    dia_val = latest["blood_pressure_dia"]
    temp_val = latest["core_temperature"]
    rr_val = latest["respiration_rate"]
    hrv_val = latest["hrv_rmssd"]
    ecg_rhythm = latest.get("ecg_status", "NORMAL_SINUS")

    # Evaluate status halo colors
    hr_status = "critical" if (hr_val > 130 or hr_val < 45) else ("warning" if (hr_val > 105 or hr_val < 55) else "nominal")
    spo2_status = "critical" if spo2_val < 90 else ("warning" if spo2_val < 94 else "nominal")
    bp_status = "critical" if (sys_val > 150 or sys_val < 90) else ("warning" if sys_val > 135 else "nominal")
    temp_status = "critical" if (temp_val > 38.5 or temp_val < 35.5) else ("warning" if temp_val > 37.6 else "nominal")
    rr_status = "critical" if (rr_val > 25 or rr_val < 8) else ("warning" if rr_val > 20 else "nominal")
    hrv_status = "warning" if hrv_val < 25 else "nominal"

    st.markdown(f"### 🧑‍🚀 Astronaut Telemetry: **{ast_name}** (`{ast_callsign}`)")

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        render_metric_card("Heart Rate", f"{hr_val:.1f}", "bpm", hr_status, f"{selected_astronaut['baseline_hr']} bpm")
    with c2:
        render_metric_card("Blood Pressure", f"{int(sys_val)}/{int(dia_val)}", "mmHg", bp_status, f"{int(selected_astronaut['baseline_bp_sys'])}/{int(selected_astronaut['baseline_bp_dia'])}")
    with c3:
        render_metric_card("Blood Oxygen (SpO2)", f"{spo2_val:.1f}", "%", spo2_status, f"{selected_astronaut['baseline_spo2']}%")
    with c4:
        render_metric_card("Core Temperature", f"{temp_val:.2f}", "°C", temp_status, f"{selected_astronaut['baseline_temp']}°C")
    with c5:
        render_metric_card("Respiration Rate", f"{rr_val:.1f}", "br/min", rr_status, f"{selected_astronaut['baseline_rr']}")
    with c6:
        render_metric_card("HRV (RMSSD)", f"{hrv_val:.1f}", "ms", hrv_status, f"{selected_astronaut['baseline_hrv']} ms")

# ============================================================================
# Synthetic ECG Rhythm Strip Waveform
# ============================================================================
st.markdown("#### 📈 Electrocardiogram (ECG) Lead II Rhythm Strip (Simulated)")
t_ecg, v_ecg = generate_synthetic_ecg_trace(
    heart_rate_bpm=latest["heart_rate"] if latest else 72.0,
    duration_sec=3.5,
    sampling_rate=120,
    rhythm=latest.get("ecg_status", "NORMAL_SINUS") if latest else "NORMAL_SINUS"
)

fig_ecg = go.Figure()
fig_ecg.add_trace(go.Scatter(
    x=t_ecg,
    y=v_ecg,
    mode="lines",
    line=dict(color="#10b981" if hr_status == "nominal" else ("#f59e0b" if hr_status == "warning" else "#ef4444"), width=2),
    name="ECG Lead II",
    hoverinfo="skip"
))

fig_ecg.update_layout(
    height=170,
    margin=dict(l=30, r=20, t=10, b=30),
    template="plotly_dark",
    paper_bgcolor="#0b1120",
    plot_bgcolor="#0b1120",
    xaxis=dict(
        title="Time Window (seconds)",
        showgrid=True,
        gridcolor="#1e293b",
        zeroline=False
    ),
    yaxis=dict(
        title="Voltage (mV)",
        showgrid=True,
        gridcolor="#1e293b",
        range=[-0.8, 1.8],
        zeroline=True,
        zerolinecolor="#334155"
    )
)
st.plotly_chart(fig_ecg, use_container_width=True)

# Rhythm Status Label
rhythm_color = "#34d399" if hr_status == "nominal" else ("#fbbf24" if hr_status == "warning" else "#f87171")
st.markdown(
    f"<div style='font-size: 0.8rem; color: #94a3b8; margin-top: -12px; margin-bottom: 20px;'>"
    f"Current Rhythm State: <strong style='color: {rhythm_color}; font-family: monospace;'>{latest.get('ecg_status', 'NORMAL_SINUS')}</strong> • "
    f"Sampling Rate: <span style='color: #38bdf8;'>120 Hz</span> • Calibration: 10mm/mV • Time: 25mm/s (Simulated)"
    f"</div>",
    unsafe_allow_html=True
)

# ============================================================================
# High-Frequency Plotly Time Series Charts
# ============================================================================
st.markdown("#### 📊 Historical Telemetry Trends (Last 60 Data Points)")

timestamps = [h["timestamp"] for h in history]
hr_history = [h["heart_rate"] for h in history]
hrv_history = [h["hrv_rmssd"] for h in history]
sys_history = [h["blood_pressure_sys"] for h in history]
dia_history = [h["blood_pressure_dia"] for h in history]
spo2_history = [h["spo2"] for h in history]
rr_history = [h["respiration_rate"] for h in history]
temp_history = [h["core_temperature"] for h in history]

chart_col1, chart_col2 = st.columns(2)

# Chart 1: Heart Rate & HRV
with chart_col1:
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x=timestamps, y=hr_history, mode="lines+markers", name="Heart Rate (bpm)",
        line=dict(color="#38bdf8", width=2), marker=dict(size=4)
    ))
    fig1.add_trace(go.Scatter(
        x=timestamps, y=hrv_history, mode="lines", name="HRV RMSSD (ms)",
        line=dict(color="#a855f7", width=1.5, dash="dot")
    ))
    # Threshold line
    fig1.add_hline(y=100.0, line_dash="dash", line_color="rgba(245, 158, 11, 0.6)", annotation_text="Tachycardia Threshold (100 bpm)")
    fig1.update_layout(
        title="Heart Rate & Heart Rate Variability",
        height=280,
        margin=dict(l=30, r=20, t=40, b=30),
        template="plotly_dark",
        paper_bgcolor="#0f172a",
        plot_bgcolor="#0f172a",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig1, use_container_width=True)

# Chart 2: Blood Pressure
with chart_col2:
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=timestamps, y=sys_history, mode="lines+markers", name="Systolic (mmHg)",
        line=dict(color="#f43f5e", width=2), marker=dict(size=4)
    ))
    fig2.add_trace(go.Scatter(
        x=timestamps, y=dia_history, mode="lines+markers", name="Diastolic (mmHg)",
        line=dict(color="#fb923c", width=1.8), marker=dict(size=4)
    ))
    fig2.add_hline(y=140.0, line_dash="dash", line_color="rgba(239, 68, 68, 0.6)", annotation_text="Hypertension Sys Limit (140 mmHg)")
    fig2.update_layout(
        title="Blood Pressure (Systolic / Diastolic)",
        height=280,
        margin=dict(l=30, r=20, t=40, b=30),
        template="plotly_dark",
        paper_bgcolor="#0f172a",
        plot_bgcolor="#0f172a",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig2, use_container_width=True)

chart_col3, chart_col4 = st.columns(2)

# Chart 3: SpO2 & Respiration
with chart_col3:
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=timestamps, y=spo2_history, mode="lines+markers", name="SpO2 (%)",
        line=dict(color="#06b6d4", width=2), marker=dict(size=4)
    ))
    fig3.add_trace(go.Scatter(
        x=timestamps, y=rr_history, mode="lines+markers", name="Respiration Rate (br/min)",
        line=dict(color="#10b981", width=1.8), yaxis="y2", marker=dict(size=4)
    ))
    fig3.add_hline(y=90.0, line_dash="dash", line_color="rgba(239, 68, 68, 0.6)", annotation_text="Hypoxia Warning (90%)")
    fig3.update_layout(
        title="Oxygen Saturation & Respiration Rate",
        height=280,
        margin=dict(l=30, r=30, t=40, b=30),
        template="plotly_dark",
        paper_bgcolor="#0f172a",
        plot_bgcolor="#0f172a",
        yaxis=dict(title="SpO2 (%)", range=[75, 101]),
        yaxis2=dict(title="Respiration (br/min)", overlaying="y", side="right", range=[5, 35]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig3, use_container_width=True)

# Chart 4: Core Temperature
with chart_col4:
    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(
        x=timestamps, y=temp_history, mode="lines+markers", name="Core Temp (°C)",
        line=dict(color="#eab308", width=2), marker=dict(size=4)
    ))
    fig4.add_hline(y=37.5, line_dash="dash", line_color="rgba(245, 158, 11, 0.6)", annotation_text="Elevated Temp (37.5°C)")
    fig4.add_hline(y=38.5, line_dash="dash", line_color="rgba(239, 68, 68, 0.6)", annotation_text="Heat Stress (38.5°C)")
    fig4.update_layout(
        title="Core Body Temperature (°C)",
        height=280,
        margin=dict(l=30, r=20, t=40, b=30),
        template="plotly_dark",
        paper_bgcolor="#0f172a",
        plot_bgcolor="#0f172a",
        yaxis=dict(range=[35.5, 40.5]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig4, use_container_width=True)
