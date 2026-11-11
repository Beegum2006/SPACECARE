"""
SPACECARE - Subsystem 4: Space Radiation Data
Authentic NASA space radiation dosimetry telemetry, RadLab data integration,
and astronaut career permissible exposure limit (PEL) tracking.

REGULATORY CITATIONS:
- NASA-STD-3001 Vol 1 Rev B: Standard for Spaceflight Human-System Standard (Crew Health),
  Section 3.2.1 mandates a 600 mSv career effective dose limit based on <= 3% REID at 95% CL.
- Measurements: Absorbed Dose Rate (µGy/h) & Ambient Dose Equivalent H*(10) Rate (µSv/h).
"""

import streamlit as st
import plotly.graph_objects as go
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.nasa_data.radiation_service import (
    fetch_radlab_telemetry, calculate_radiation_summary, sync_radlab_records_to_db, NASA_RADIATION_STANDARDS
)
from src.components.mission_header import render_mission_header, render_crew_selector_sidebar
from src.components.disclaimers import render_medical_disclaimer, render_sidebar_disclaimer
from src.components.badges import render_provenance_badge
from src.components.metrics_card import render_metric_card

st.set_page_config(page_title="SPACECARE | Space Radiation", page_icon="☢️", layout="wide")

# Mission Header & Persistent Disclaimers
render_mission_header("Space Radiation Dosimetry Console")
render_medical_disclaimer(compact=True)
selected_astronaut = render_crew_selector_sidebar()
render_sidebar_disclaimer()

# Fetch telemetry records (attempts live RadLab API, falls back cleanly to local calibrated fixtures)
records, is_live = fetch_radlab_telemetry(spacecraft="ISS", limit=20, timeout_sec=5)
stats = calculate_radiation_summary(records, mission_days=42)

# Provenance Badge reflecting true origin
badge_status = "real" if is_live else "simulated"
badge_label = "NASA RadLab Data API (Verified Live Response)" if is_live else "RadLab Calibrated Reference Dosimetry Fixture"
render_provenance_badge(badge_status, badge_label, "ISS Liulin-5 & DOSTEL Detectors")

st.markdown(
    r"""
    <div style="background: rgba(11, 61, 145, 0.15); border: 1px solid rgba(59, 130, 246, 0.35); border-radius: 8px; padding: 12px 18px; margin-bottom: 20px; font-size: 0.86rem; color: #cbd5e1; line-height: 1.5;">
        ☢️ <strong>NASA SPACE DOSIMETRY & REGULATORY STANDARDS:</strong><br>
        This console monitors ionizing space radiation based on the <strong>NASA-STD-3001 Volume 1, Rev B</strong> 
        spaceflight health standard (Universal <strong>600 mSv</strong> career effective dose ceiling).<br>
        <em>Note on Quantities:</em> Point-in-time dosimeter telemetry in <strong>$\mu\text{Gy/hour}$</strong> (absorbed dose) 
        and <strong>$\mu\text{Sv/hour}$</strong> represents ambient dose equivalent $H^*(10)$ at the detector location.
        Full organ-weighted effective dose ($E$) requires ionizing transport modeling (HZETRN).
    </div>
    """,
    unsafe_allow_html=True
)

# ============================================================================
# Controls & Sync Bar
# ============================================================================
c_ctrl1, c_ctrl2, c_ctrl3 = st.columns([2, 2, 2])

with c_ctrl1:
    selected_detector = st.selectbox(
        "Active Radiation Detector:",
        ["All Instruments", "Liulin-5 Charged Particle Telescope", "DOSTEL (Dosimetry Telescope)", "TEPC Proportional Counter"]
    )

with c_ctrl2:
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    if st.button("📥 Ingest Records to SQLite", type="primary", use_container_width=True):
        count = sync_radlab_records_to_db(records)
        flag_desc = "is_simulated = 0 (Live API)" if is_live else "is_simulated = 1 (Calibrated Reference Fixture)"
        st.success(f"Persisted {count} records to database ({flag_desc}).")

with c_ctrl3:
    source_label = "🟢 Live NASA RadLab API Response" if is_live else "📦 Calibrated Reference Dosimetry Fixture"
    st.markdown(f"<div style='font-size: 0.82rem; color: #94a3b8; padding-top: 32px;'>Data Source: <strong>{source_label}</strong></div>", unsafe_allow_html=True)

# Filter by detector if selected
if selected_detector != "All Instruments":
    filtered_records = [r for r in records if selected_detector.split()[0].lower() in r.get("instrument", "").lower()]
    if filtered_records:
        records = filtered_records
        stats = calculate_radiation_summary(records, mission_days=42)

st.divider()

# ============================================================================
# Dosimetry Metrics Display
# ============================================================================
status_color = "warning" if stats["status"] in ("WARNING", "ELEVATED_SAA") else ("critical" if stats["status"] == "CRITICAL" else "nominal")

st.markdown("### 📊 Active Orbital Radiation Telemetry")

r1, r2, r3, r4, r5, r6 = st.columns(6)
with r1:
    render_metric_card("Avg Dose Equiv. Rate", f"{stats['avg_dose_rate_usv_h']:.1f}", "µSv/h", status_color, "15.0 - 25.0 µSv/h")
with r2:
    render_metric_card("Avg Absorbed Rate", f"{stats['avg_absorbed_rate_ugy_h']:.1f}", "µGy/h", "nominal", "10.0 - 20.0 µGy/h")
with r3:
    render_metric_card("Peak SAA Dose Rate", f"{stats['peak_dose_rate_usv_h']:.1f}", "µSv/h", "warning" if stats['peak_dose_rate_usv_h'] >= 50 else "nominal", "SAA Spike: < 70 µSv/h")
with r4:
    render_metric_card("Mission Cumulative", f"{stats['estimated_cumulative_msv']:.2f}", "mSv", "nominal", "Day 42 / 180")
with r5:
    render_metric_card("NCRP 30-Day Pct", f"{stats['pct_30_day_limit']:.1f}", "%", "nominal", "Ref: 100 mSv")
with r6:
    render_metric_card("Career PEL Pct", f"{stats['pct_career_limit']:.1f}", "%", "nominal", "NASA-STD-3001: 600 mSv")

# ============================================================================
# Plotly Charts: Dose Rates & Exposure Gauges
# ============================================================================
col_ts, col_gauge = st.columns([2, 1])

with col_ts:
    st.markdown("#### 📈 Ionizing Radiation Dose Rate Profile")
    timestamps = [r.get("timestamp", "") for r in records]
    eq_rates = [r.get("dose_equivalent_rate_usv_h", 0.0) for r in records]
    ab_rates = [r.get("absorbed_dose_rate_ugy_h", 0.0) for r in records]

    fig_rad = go.Figure()
    fig_rad.add_trace(go.Scatter(
        x=timestamps, y=eq_rates, mode="lines+markers", name="Dose Equivalent Rate (µSv/h)",
        line=dict(color="#f43f5e", width=2.2), marker=dict(size=5)
    ))
    fig_rad.add_trace(go.Scatter(
        x=timestamps, y=ab_rates, mode="lines+markers", name="Absorbed Dose Rate (µGy/h)",
        line=dict(color="#38bdf8", width=1.8), marker=dict(size=5)
    ))
    fig_rad.add_hline(
        y=NASA_RADIATION_STANDARDS["saa_elevation_threshold_usv_h"],
        line_dash="dash",
        line_color="rgba(245, 158, 11, 0.7)",
        annotation_text="Operational SAA Elevation Threshold (50 µSv/h)"
    )
    fig_rad.update_layout(
        title="Orbital Radiation Dose Rates (ISS Flight Trajectory)",
        height=320,
        margin=dict(l=30, r=20, t=40, b=30),
        template="plotly_dark",
        paper_bgcolor="#0f172a",
        plot_bgcolor="#0f172a",
        yaxis=dict(title="Dose Rate"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_rad, use_container_width=True)

with col_gauge:
    st.markdown("#### 🛡️ NASA Career Permissible Exposure Limit (PEL)")
    career_pel = NASA_RADIATION_STANDARDS["career_effective_dose_limit_msv"]
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=stats["estimated_cumulative_msv"],
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Career Dose (mSv)", 'font': {'size': 14, 'color': '#f8fafc'}},
        delta={'reference': career_pel, 'increasing': {'color': "#ef4444"}},
        gauge={
            'axis': {'range': [0, career_pel], 'tickwidth': 1, 'tickcolor': "#64748b"},
            'bar': {'color': "#38bdf8"},
            'bgcolor': "#0b1120",
            'borderwidth': 1,
            'bordercolor': "#1e293b",
            'steps': [
                {'range': [0, 100], 'color': 'rgba(16, 185, 129, 0.25)'},
                {'range': [100, 300], 'color': 'rgba(245, 158, 11, 0.25)'},
                {'range': [300, 600], 'color': 'rgba(239, 68, 68, 0.35)'}
            ],
            'threshold': {
                'line': {'color': "#ef4444", 'width': 3},
                'thickness': 0.85,
                'value': career_pel
            }
        }
    ))
    fig_gauge.update_layout(
        height=320,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="#0f172a"
    )
    st.plotly_chart(fig_gauge, use_container_width=True)

# ============================================================================
# Technical Specifications of Verified NASA Detectors
# ============================================================================
st.markdown("#### 🔬 NASA Space Radiation Instrumentation Specifications")
instruments_info = [
    {
        "Detector": "Liulin-5 Particle Telescope",
        "Sensor Technology": "Silicon Semiconductor Detectors",
        "Location on ISS": "Russian Service Module (Zvezda) / Spherical Tissue Phantom",
        "Primary Target": "GCR and trapped proton energy deposition in human tissue"
    },
    {
        "Detector": "DOSTEL (Dosimetry Telescope)",
        "Sensor Technology": "Silicon Semiconductor Multi-detector Array",
        "Location on ISS": "Columbus Orbital Facility (ESA European Laboratory)",
        "Primary Target": "Linear energy transfer (LET) spectrum and flux dynamics"
    },
    {
        "Detector": "TEPC (Tissue Equivalent Counter)",
        "Sensor Technology": "Low-pressure Tissue-Equivalent Gas Ionization Chamber",
        "Location on ISS": "Destiny Laboratory (US Lab)",
        "Primary Target": "Microdosimetric dose equivalent rate in real time"
    }
]

st.table(instruments_info)
