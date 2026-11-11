"""
SPACECARE - Subsystem 2: ISS Environmental Telemetry (ECLSS)
Live cabin atmosphere monitoring, life support subsystem statuses,
interactive anomaly injection (CDRA failure, depressurization), and Plotly trends.

DISCLAIMER: All environmental data presented here is SYNTHETIC and generated via
spacecraft life support simulations. It is NOT real NASA flight telemetry.
"""

import streamlit as st
import plotly.graph_objects as go
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.queries import (
    get_latest_environment, get_environment_history, log_environment
)
from src.simulation.iss_env_generator import (
    generate_env_snapshot, generate_env_series, ENV_ANOMALY_MODES, ISS_MODULES
)
from src.nasa_data.eda_client import (
    load_eda_benchmarks, get_eda_statistical_summary, compare_reading_against_eda
)
from src.components.mission_header import render_mission_header, render_crew_selector_sidebar
from src.components.disclaimers import render_medical_disclaimer, render_sidebar_disclaimer
from src.components.badges import render_provenance_badge
from src.components.metrics_card import render_metric_card

st.set_page_config(page_title="SPACECARE | ISS Environment", page_icon="🛰️", layout="wide")

# Mission Header & Persistent Disclaimers
render_mission_header("ISS Environmental Life Support (ECLSS)")
render_medical_disclaimer(compact=True)
selected_astronaut = render_crew_selector_sidebar()
render_sidebar_disclaimer()

# Mandatory Provenance Notice
render_provenance_badge("simulated", "ISS ECLSS Life Support Model & Synthetic Atmosphere Telemetry")

# Ensure initial history exists in database
env_history = get_environment_history(limit=60)
if not env_history:
    initial_env_series = generate_env_series(count=30, interval_seconds=15, anomaly_mode="NOMINAL")
    for r in initial_env_series:
        log_environment(
            cabin_pressure_psi=r["cabin_pressure_psi"],
            co2_partial_pressure_mmhg=r["co2_partial_pressure_mmhg"],
            o2_percentage=r["o2_percentage"],
            temperature_celsius=r["temperature_celsius"],
            relative_humidity_pct=r["relative_humidity_pct"],
            radiation_level_usv_h=r["radiation_level_usv_h"],
            module_name=r["module_name"],
            is_simulated=1
        )
    env_history = get_environment_history(limit=60)

latest_env = env_history[-1] if env_history else None

# ============================================================================
# ECLSS Simulation & Anomaly Controls
# ============================================================================
with st.container():
    st.markdown("#### ⚡ ECLSS Telemetry Controls & Malfunction Injection")
    c1, c2, c3, c4 = st.columns([2, 2, 1.5, 1.5])

    with c1:
        selected_module = st.selectbox("Orbital Module:", ISS_MODULES, index=0)

    with c2:
        selected_anomaly = st.selectbox(
            "Induce ECLSS Anomaly:",
            ENV_ANOMALY_MODES,
            index=0,
            help="Simulate life-support hardware malfunctions."
        )

    with c3:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button("📡 Stream ECLSS Tick", type="primary", use_container_width=True):
            r = generate_env_snapshot(module_name=selected_module, anomaly_mode=selected_anomaly)
            log_environment(
                cabin_pressure_psi=r["cabin_pressure_psi"],
                co2_partial_pressure_mmhg=r["co2_partial_pressure_mmhg"],
                o2_percentage=r["o2_percentage"],
                temperature_celsius=r["temperature_celsius"],
                relative_humidity_pct=r["relative_humidity_pct"],
                radiation_level_usv_h=r["radiation_level_usv_h"],
                module_name=r["module_name"],
                is_simulated=1
            )
            st.rerun()

    with c4:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button("⏩ Simulate 20-Point Run", use_container_width=True):
            burst = generate_env_series(
                module_name=selected_module, count=20, interval_seconds=10,
                anomaly_mode=selected_anomaly, anomaly_onset_index=5
            )
            for r in burst:
                log_environment(
                    cabin_pressure_psi=r["cabin_pressure_psi"],
                    co2_partial_pressure_mmhg=r["co2_partial_pressure_mmhg"],
                    o2_percentage=r["o2_percentage"],
                    temperature_celsius=r["temperature_celsius"],
                    relative_humidity_pct=r["relative_humidity_pct"],
                    radiation_level_usv_h=r["radiation_level_usv_h"],
                    module_name=r["module_name"],
                    is_simulated=1
                )
            st.rerun()

st.divider()

# ============================================================================
# Real-Time Telemetry Cards
# ============================================================================
if latest_env:
    press_val = latest_env["cabin_pressure_psi"]
    co2_val = latest_env["co2_partial_pressure_mmhg"]
    o2_val = latest_env["o2_percentage"]
    temp_val = latest_env["temperature_celsius"]
    hum_val = latest_env["relative_humidity_pct"]
    rad_val = latest_env.get("radiation_level_usv_h", 22.5)

    # Status halos
    press_status = "critical" if press_val < 13.5 else ("warning" if press_val < 14.2 or press_val > 15.2 else "nominal")
    co2_status = "critical" if co2_val > 4.5 else ("warning" if co2_val > 3.5 else "nominal")
    o2_status = "critical" if o2_val < 18.5 else ("warning" if o2_val < 20.0 or o2_val > 23.0 else "nominal")
    temp_status = "critical" if temp_val > 28.0 else ("warning" if temp_val > 25.0 or temp_val < 18.0 else "nominal")
    hum_status = "warning" if hum_val > 65.0 or hum_val < 30.0 else "nominal"

    st.markdown(f"### 🛰️ Module Atmosphere: **{latest_env['module_name']}**")

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    with m1:
        render_metric_card("Cabin Pressure", f"{press_val:.2f}", "psi", press_status, "14.2 - 14.9 psi")
    with m2:
        render_metric_card("CO2 Partial Press.", f"{co2_val:.2f}", "mmHg", co2_status, "< 3.5 mmHg")
    with m3:
        render_metric_card("Oxygen Level", f"{o2_val:.2f}", "%", o2_status, "20.5 - 21.8 %")
    with m4:
        render_metric_card("Cabin Temp", f"{temp_val:.1f}", "°C", temp_status, "20.0 - 24.0 °C")
    with m5:
        render_metric_card("Rel. Humidity", f"{hum_val:.1f}", "%", hum_status, "40.0 - 60.0 %")
    with m6:
        render_metric_card("Cabin Dosimeter", f"{rad_val:.1f}", "µSv/h", "nominal", "15 - 35 µSv/h")

# ============================================================================
# High-Frequency Plotly Time Series Charts
# ============================================================================
st.markdown("#### 📊 Historical ECLSS Telemetry Trends (Last 60 Data Points)")

timestamps = [h["timestamp"] for h in env_history]
press_history = [h["cabin_pressure_psi"] for h in env_history]
co2_history = [h["co2_partial_pressure_mmhg"] for h in env_history]
o2_history = [h["o2_percentage"] for h in env_history]
temp_history = [h["temperature_celsius"] for h in env_history]
hum_history = [h["relative_humidity_pct"] for h in env_history]

c_col1, c_col2 = st.columns(2)

# Chart 1: Cabin Pressure
with c_col1:
    fig_p = go.Figure()
    fig_p.add_trace(go.Scatter(
        x=timestamps, y=press_history, mode="lines+markers", name="Cabin Pressure (psi)",
        line=dict(color="#38bdf8", width=2), marker=dict(size=4)
    ))
    fig_p.add_hline(y=14.2, line_dash="dash", line_color="rgba(245, 158, 11, 0.6)", annotation_text="Low Pressure Advisory (14.2 psi)")
    fig_p.add_hline(y=13.5, line_dash="dash", line_color="rgba(239, 68, 68, 0.7)", annotation_text="Decompression Warning (13.5 psi)")
    fig_p.update_layout(
        title="Cabin Total Pressure (psi)",
        height=280,
        margin=dict(l=30, r=20, t=40, b=30),
        template="plotly_dark",
        paper_bgcolor="#0f172a",
        plot_bgcolor="#0f172a",
        yaxis=dict(range=[11.0, 16.0]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_p, use_container_width=True)

# Chart 2: CO2 Partial Pressure
with c_col2:
    fig_co2 = go.Figure()
    fig_co2.add_trace(go.Scatter(
        x=timestamps, y=co2_history, mode="lines+markers", name="CO2 Pressure (mmHg)",
        line=dict(color="#f59e0b", width=2), marker=dict(size=4)
    ))
    fig_co2.add_hline(y=3.5, line_dash="dash", line_color="rgba(245, 158, 11, 0.6)", annotation_text="CDRA Advisory (> 3.5 mmHg)")
    fig_co2.add_hline(y=4.5, line_dash="dash", line_color="rgba(239, 68, 68, 0.7)", annotation_text="Hypercapnia Warning (> 4.5 mmHg)")
    fig_co2.update_layout(
        title="Carbon Dioxide Partial Pressure (mmHg)",
        height=280,
        margin=dict(l=30, r=20, t=40, b=30),
        template="plotly_dark",
        paper_bgcolor="#0f172a",
        plot_bgcolor="#0f172a",
        yaxis=dict(range=[1.0, 8.0]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_co2, use_container_width=True)

c_col3, c_col4 = st.columns(2)

# Chart 3: Oxygen Level
with c_col3:
    fig_o2 = go.Figure()
    fig_o2.add_trace(go.Scatter(
        x=timestamps, y=o2_history, mode="lines+markers", name="Oxygen Concentration (%)",
        line=dict(color="#10b981", width=2), marker=dict(size=4)
    ))
    fig_o2.add_hline(y=19.5, line_dash="dash", line_color="rgba(239, 68, 68, 0.7)", annotation_text="Hypoxia Warning (19.5%)")
    fig_o2.update_layout(
        title="Oxygen Atmospheric Concentration (%)",
        height=280,
        margin=dict(l=30, r=20, t=40, b=30),
        template="plotly_dark",
        paper_bgcolor="#0f172a",
        plot_bgcolor="#0f172a",
        yaxis=dict(range=[16.0, 24.0]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_o2, use_container_width=True)

# Chart 4: Temperature & Relative Humidity
with c_col4:
    fig_th = go.Figure()
    fig_th.add_trace(go.Scatter(
        x=timestamps, y=temp_history, mode="lines+markers", name="Temperature (°C)",
        line=dict(color="#ec4899", width=2), marker=dict(size=4)
    ))
    fig_th.add_trace(go.Scatter(
        x=timestamps, y=hum_history, mode="lines+markers", name="Relative Humidity (%)",
        line=dict(color="#8b5cf6", width=1.8), yaxis="y2", marker=dict(size=4)
    ))
    fig_th.update_layout(
        title="Thermal Control & Relative Humidity",
        height=280,
        margin=dict(l=30, r=30, t=40, b=30),
        template="plotly_dark",
        paper_bgcolor="#0f172a",
        plot_bgcolor="#0f172a",
        yaxis=dict(title="Temp (°C)", range=[16.0, 36.0]),
        yaxis2=dict(title="Humidity (%)", overlaying="y", side="right", range=[20.0, 90.0]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_th, use_container_width=True)

# ============================================================================
# ECLSS Subsystem Status Matrix
# ============================================================================
st.markdown("#### 🛠️ Life Support Subsystem Status Matrix")

sub1, sub2, sub3, sub4 = st.columns(4)

with sub1:
    cdra_status = "CRITICAL" if co2_val > 4.5 else ("WARNING" if co2_val > 3.5 else "OPERATIONAL")
    cdra_badge = "critical" if cdra_status == "CRITICAL" else ("warning" if cdra_status == "WARNING" else "nominal")
    st.markdown(
        f"""
        <div class="telemetry-card {cdra_badge}">
            <div style="font-weight: 700; color: #f8fafc;">CDRA CO2 Scrubber</div>
            <div style="font-size: 0.78rem; color: #94a3b8; margin: 4px 0;">Carbon Dioxide Removal Assembly</div>
            <span class="status-pill {cdra_badge}">{cdra_status}</span>
        </div>
        """,
        unsafe_allow_html=True
    )

with sub2:
    ogs_status = "WARNING" if o2_val < 20.0 else "OPERATIONAL"
    ogs_badge = "warning" if ogs_status == "WARNING" else "nominal"
    st.markdown(
        f"""
        <div class="telemetry-card {ogs_badge}">
            <div style="font-weight: 700; color: #f8fafc;">OGS Oxygen Generator</div>
            <div style="font-size: 0.78rem; color: #94a3b8; margin: 4px 0;">Electrolysis Oxygen Generation</div>
            <span class="status-pill {ogs_badge}">{ogs_status}</span>
        </div>
        """,
        unsafe_allow_html=True
    )

with sub3:
    iatcs_status = "WARNING" if temp_val > 25.0 else "OPERATIONAL"
    iatcs_badge = "warning" if iatcs_status == "WARNING" else "nominal"
    st.markdown(
        f"""
        <div class="telemetry-card {iatcs_badge}">
            <div style="font-weight: 700; color: #f8fafc;">IATCS Thermal Loop</div>
            <div style="font-size: 0.78rem; color: #94a3b8; margin: 4px 0;">Internal Active Thermal Control</div>
            <span class="status-pill {iatcs_badge}">{iatcs_status}</span>
        </div>
        """,
        unsafe_allow_html=True
    )

with sub4:
    press_status_label = "CRITICAL" if press_val < 13.5 else ("WARNING" if press_val < 14.2 else "PRESSURIZED")
    press_badge = "critical" if press_status_label == "CRITICAL" else ("warning" if press_status_label == "WARNING" else "nominal")
    st.markdown(
        f"""
        <div class="telemetry-card {press_badge}">
            <div style="font-weight: 700; color: #f8fafc;">PCA Pressure Control</div>
            <div style="font-size: 0.78rem; color: #94a3b8; margin: 4px 0;">Pressure Control Assembly</div>
            <span class="status-pill {press_badge}">{press_status_label}</span>
        </div>
        """,
        unsafe_allow_html=True
    )

# ============================================================================
# NASA EDA Flight Benchmark Comparison
# ============================================================================
st.markdown("---")
st.markdown("### 🛰️ NASA Flight Environmental Baseline (ECLSS Engineering Reference)")
render_provenance_badge("simulated", "NASA ECLSS Engineering Baseline Reference Fixture (NASA-STD-3001)", "Calibrated to Published ISS Operational Tolerances")

st.markdown(
    """
    The table below compares the current simulated ECLSS telemetry with **calibrated reference engineering specifications** 
    derived from published NASA ISS life support operational standards (NASA-STD-3001).
    """
)

eda_comparison = compare_reading_against_eda(latest_env) if latest_env else None
eda_stats = get_eda_statistical_summary()

if eda_comparison and "details" in eda_comparison:
    comparison_rows = []
    metric_labels = {
        "cabin_pressure_psi": "Cabin Total Pressure",
        "co2_partial_pressure_mmhg": "CO2 Partial Pressure",
        "o2_percentage": "Oxygen Concentration",
        "temperature_celsius": "Cabin Temperature",
        "relative_humidity_pct": "Relative Humidity"
    }

    for key, label in metric_labels.items():
        if key in eda_comparison["details"] and key in eda_stats:
            d = eda_comparison["details"][key]
            ref = eda_stats[key]
            status_tag = "🟢 Within Flight Baseline" if d["within_nasa_bounds"] else "🟠 Deviating from Baseline"
            comparison_rows.append({
                "Atmospheric Metric": label,
                "Current Telemetry (Simulated)": f"{d['value']} {d['unit']}",
                "NASA Recorded Mean (EDA)": f"{ref['mean']} {ref['unit']}",
                "NASA Recorded Range": f"{ref['min']} - {ref['max']} {ref['unit']}",
                "Validation Status": status_tag
            })

    st.table(comparison_rows)

with st.expander("📄 View Authentic NASA EDA Flight Telemetry Records (CSV Preview)"):
    eda_df = load_eda_benchmarks()
    if not eda_df.empty:
        st.dataframe(eda_df, use_container_width=True)
    else:
        st.info("No local EDA records loaded.")

