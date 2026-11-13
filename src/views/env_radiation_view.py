"""
SPACECARE View: ISS Environmental Telemetry & Space Radiation
(Member 3 - UI Workspace | src/views/)

Renders ECLSS cabin life support metrics and cosmic dosimetry exposure
tracking. All data sourced exclusively via data_adapter.py.
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, Any

from src.components.data_adapter import get_iss_environment_data, get_radiation_data
from src.components.mission_header import render_mission_header
from src.components.disclaimers import render_medical_disclaimer
from src.components.metrics_card import render_metric_card
from src.components.badges import render_provenance_badge


def _env_status(val: float, warn_lo: float, warn_hi: float, crit_lo: float, crit_hi: float) -> str:
    """Classifies an environmental reading into a CSS status class."""
    if val < crit_lo or val > crit_hi:
        return "critical"
    if val < warn_lo or val > warn_hi:
        return "warning"
    return "nominal"


def _plot_co2_trend(df) -> go.Figure:
    """Plots CO2 partial pressure with warning threshold."""
    fig = go.Figure()
    fig.add_hline(y=4.0, line_dash="dash", line_color="#ef4444", line_width=1,
                  annotation_text="Warning Threshold (4.0 mmHg)",
                  annotation_font_color="#ef4444", annotation_font_size=10)
    fig.add_hrect(y0=0, y1=3.8, fillcolor="rgba(16, 185, 129, 0.06)", line_width=0)
    fig.add_trace(go.Scatter(
        x=df["timestamp"], y=df["co2_partial_pressure_mmhg"],
        mode="lines+markers", name="CO₂ (mmHg)",
        line=dict(color="#f59e0b", width=2), marker=dict(size=3)
    ))
    fig.update_layout(
        height=300, margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15, 23, 42, 0.5)",
        font=dict(color="#94a3b8", size=11),
        yaxis=dict(title="CO₂ Partial Pressure (mmHg)", gridcolor="rgba(30,41,59,0.5)"),
        xaxis=dict(gridcolor="rgba(30,41,59,0.5)"),
        showlegend=False
    )
    return fig


def _plot_o2_pressure_stability(df) -> go.Figure:
    """Plots O2 partial pressure and total cabin pressure as dual-axis chart."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(
        x=df["timestamp"], y=df["o2_partial_pressure_kpa"],
        mode="lines", name="O₂ Partial Pressure (kPa)",
        line=dict(color="#38bdf8", width=2)
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=df["timestamp"], y=df["cabin_pressure_kpa"],
        mode="lines", name="Cabin Pressure (kPa)",
        line=dict(color="#a78bfa", width=2, dash="dot")
    ), secondary_y=True)
    fig.update_layout(
        height=300, margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15, 23, 42, 0.5)",
        font=dict(color="#94a3b8", size=11),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font_size=10)
    )
    fig.update_yaxes(title_text="O₂ (kPa)", gridcolor="rgba(30,41,59,0.5)", secondary_y=False)
    fig.update_yaxes(title_text="Cabin (kPa)", gridcolor="rgba(30,41,59,0.3)", secondary_y=True)
    fig.update_xaxes(gridcolor="rgba(30,41,59,0.5)")
    return fig


def _plot_radiation_exposure(df, summary: Dict) -> go.Figure:
    """Plots 30-day GCR + SPE stacked bars, cumulative dose curve, and SAA markers."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # GCR bars
    fig.add_trace(go.Bar(
        x=df["timestamp"], y=df["galactic_cosmic_ray_msv"],
        name="GCR (mSv/day)", marker_color="rgba(56, 189, 248, 0.7)"
    ), secondary_y=False)

    # SPE bars stacked on top
    fig.add_trace(go.Bar(
        x=df["timestamp"], y=df["solar_particle_event_msv"],
        name="SPE (mSv/day)", marker_color="rgba(239, 68, 68, 0.7)"
    ), secondary_y=False)

    # Cumulative dose curve
    fig.add_trace(go.Scatter(
        x=df["timestamp"], y=df["cumulative_mission_dose_msv"],
        mode="lines+markers", name="Cumulative Dose (mSv)",
        line=dict(color="#f59e0b", width=2.5), marker=dict(size=3)
    ), secondary_y=True)

    # SAA passage markers
    saa_df = df[df["saa_passage_flag"] == True]
    if not saa_df.empty:
        fig.add_trace(go.Scatter(
            x=saa_df["timestamp"], y=saa_df["total_daily_dose_msv"],
            mode="markers", name="SAA Passage",
            marker=dict(size=12, color="#a78bfa", symbol="star", line=dict(width=1, color="#c084fc"))
        ), secondary_y=False)

    fig.update_layout(
        barmode="stack",
        height=350, margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15, 23, 42, 0.5)",
        font=dict(color="#94a3b8", size=11),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font_size=10)
    )
    fig.update_yaxes(title_text="Daily Dose (mSv)", gridcolor="rgba(30,41,59,0.5)", secondary_y=False)
    fig.update_yaxes(title_text="Cumulative (mSv)", gridcolor="rgba(30,41,59,0.3)", secondary_y=True)
    fig.update_xaxes(gridcolor="rgba(30,41,59,0.5)")
    return fig


def render_env_radiation_view(astronaut_profile: Dict[str, Any], time_window_hours: int) -> None:
    """Main rendering entry point for the ISS Environment & Radiation view."""

    render_mission_header("ISS Environmental Telemetry & Space Radiation (NASA OSDR / RadLab)")
    render_medical_disclaimer(compact=True)

    # ══════════════════════════════════════════════════════════════
    # SECTION A: ISS Cabin Environment Telemetry
    # ══════════════════════════════════════════════════════════════
    env_res = get_iss_environment_data(hours=time_window_hours)
    env_df = env_res["data"]
    env_sum = env_res["summary"]

    st.markdown("### 🛰️ ISS ECLSS Cabin Environment Telemetry")
    if env_res["source"] == "live":
        render_provenance_badge("real", f"Live Module — {env_res['status_note']}")
    else:
        render_provenance_badge("simulated", f"Simulated Fallback — {env_res['status_note']}")

    # KPI Row
    e1, e2, e3, e4, e5 = st.columns(5)
    co2 = env_sum.get("co2_partial_pressure_mmhg", 2.8)
    o2 = env_sum.get("o2_partial_pressure_kpa", 21.3)
    press = env_sum.get("cabin_pressure_kpa", 101.3)
    temp = env_sum.get("temperature_c", 21.5)
    hum = env_sum.get("humidity_pct", 45.0)

    with e1:
        render_metric_card("CO₂ Partial Pressure", f"{co2:.2f}", "mmHg",
                           _env_status(co2, 0, 3.8, 0, 4.5), "< 3.8 mmHg nominal")
    with e2:
        render_metric_card("O₂ Partial Pressure", f"{o2:.1f}", "kPa",
                           _env_status(o2, 19.5, 23.0, 18.0, 24.0), "~21.0 kPa nominal")
    with e3:
        render_metric_card("Cabin Pressure", f"{press:.1f}", "kPa",
                           _env_status(press, 98.0, 104.0, 94.0, 106.0), "~101.3 kPa nominal")
    with e4:
        render_metric_card("Cabin Temperature", f"{temp:.1f}", "°C",
                           _env_status(temp, 18.3, 26.7, 16.0, 28.0), "18.3 – 26.7 °C")
    with e5:
        render_metric_card("Relative Humidity", f"{hum:.1f}", "%",
                           _env_status(hum, 30.0, 70.0, 25.0, 75.0), "30 – 70 %")

    # Charts
    if not env_df.empty:
        ch1, ch2 = st.columns(2)
        with ch1:
            st.markdown("##### CO₂ Partial Pressure Trend")
            st.plotly_chart(_plot_co2_trend(env_df), use_container_width=True)
        with ch2:
            st.markdown("##### O₂ & Cabin Pressure Stability")
            st.plotly_chart(_plot_o2_pressure_stability(env_df), use_container_width=True)

    # NASA Dataset Provenance Card
    st.markdown(
        f"""
        <div class="telemetry-card nominal" style="margin-top: 12px;">
            <div class="telemetry-label">NASA ECLSS DATASET PROVENANCE</div>
            <div style="font-size: 0.85rem; color: #cbd5e1; margin-top: 6px;">
                <strong>Dataset ID:</strong> <code>{env_sum.get('dataset_id', 'OSD-542')}</code> &nbsp;|&nbsp;
                <strong>Standard:</strong> {env_sum.get('source', 'NASA-STD-3001')} &nbsp;|&nbsp;
                <strong>DOI:</strong> <code>{env_sum.get('doi', '10.26030/iss-eclss-spec')}</code> &nbsp;|&nbsp;
                <strong>Connection:</strong> <span style="color: {'#10b981' if env_res['source'] == 'live' else '#f59e0b'};">
                    {'🟢 LIVE' if env_res['source'] == 'live' else '🟡 FALLBACK'}
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

    # ══════════════════════════════════════════════════════════════
    # SECTION B: Space Radiation Exposure (NASA RadLab)
    # ══════════════════════════════════════════════════════════════
    rad_res = get_radiation_data(days=30)
    rad_df = rad_res["data"]
    rad_sum = rad_res["summary"]

    st.markdown("### ☢️ Space Radiation Exposure (NASA RadLab)")
    if rad_res["source"] == "live":
        render_provenance_badge("real", f"Live Module — {rad_res['status_note']}")
    else:
        render_provenance_badge("simulated", f"Simulated Fallback — {rad_res['status_note']}")

    # KPI Row
    r1, r2, r3, r4 = st.columns(4)
    daily_dose = rad_sum.get("current_dose_rate_msv_day", 0.45)
    cum_dose = rad_sum.get("cumulative_dose_msv", 13.5)
    pct_30d = rad_sum.get("pct_30d_limit", 5.4)
    solar_alert = rad_sum.get("solar_storm_alert", False)
    saa_active = rad_sum.get("saa_active", False)

    with r1:
        render_metric_card("Current Daily Dose", f"{daily_dose:.3f}", "mSv/day",
                           "warning" if daily_dose > 0.8 else "nominal",
                           "LEO baseline ~0.4 – 0.6 mSv/day")
    with r2:
        render_metric_card("Cumulative Mission Dose", f"{cum_dose:.2f}", "mSv",
                           "warning" if pct_30d > 50 else "nominal",
                           f"{pct_30d:.1f}% of 250 mSv 30-day limit")
    with r3:
        render_metric_card("NASA Career Limit", "600.0", "mSv",
                           "nominal",
                           f"{rad_sum.get('pct_career_limit', 2.3):.1f}% utilized (NASA-STD-3001)")
    with r4:
        if solar_alert:
            render_metric_card("Solar / SAA Status", "SPE ACTIVE", "",
                               "critical", "🚨 Solar Particle Event Detected")
        elif saa_active:
            render_metric_card("Solar / SAA Status", "SAA TRANSIT", "",
                               "warning", "⚠️ South Atlantic Anomaly Passage")
        else:
            render_metric_card("Solar / SAA Status", "QUIET SUN", "",
                               "nominal", "🟢 Nominal Heliospheric Conditions")

    # Radiation chart
    if not rad_df.empty:
        st.markdown("##### 30-Day Radiation Exposure Profile")
        st.plotly_chart(_plot_radiation_exposure(rad_df, rad_sum), use_container_width=True)
