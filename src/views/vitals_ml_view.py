"""
SPACECARE View: Astronaut Vital Signs & ML Anomaly Detection
(Member 3 - UI Workspace | src/views/)

Renders physiological telemetry charts, KPI cards, and Isolation Forest
anomaly diagnostics. All data sourced exclusively via data_adapter.py.
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, Any

from src.components.data_adapter import get_vitals_and_anomalies
from src.components.mission_header import render_mission_header
from src.components.disclaimers import render_medical_disclaimer
from src.components.metrics_card import render_metric_card
from src.components.badges import render_provenance_badge


def _status_for_value(val: float, low: float, high: float) -> str:
    """Returns CSS status class based on whether value falls in normal range."""
    if low <= val <= high:
        return "nominal"
    elif val < low * 0.9 or val > high * 1.1:
        return "critical"
    return "warning"


def _plot_vital_with_band(
    df, col: str, label: str, unit: str,
    band_low: float, band_high: float,
    anomaly_col: str = "is_anomaly"
) -> go.Figure:
    """Builds a Plotly line chart with a normal band and red anomaly markers."""
    fig = go.Figure()

    # Normal band
    fig.add_hrect(
        y0=band_low, y1=band_high,
        fillcolor="rgba(16, 185, 129, 0.08)",
        line_width=0,
        annotation_text="Normal Range",
        annotation_position="top left",
        annotation_font_size=10,
        annotation_font_color="#64748b"
    )

    # Main trace
    fig.add_trace(go.Scatter(
        x=df["timestamp"], y=df[col],
        mode="lines+markers",
        name=label,
        line=dict(color="#38bdf8", width=2),
        marker=dict(size=4, color="#38bdf8"),
        hovertemplate=f"{label}: %{{y:.1f}} {unit}<br>%{{x}}<extra></extra>"
    ))

    # Anomaly markers
    anom_df = df[df[anomaly_col] == True]
    if not anom_df.empty:
        fig.add_trace(go.Scatter(
            x=anom_df["timestamp"], y=anom_df[col],
            mode="markers",
            name="Anomaly",
            marker=dict(size=10, color="#ef4444", symbol="x", line=dict(width=2, color="#fca5a5")),
            hovertemplate=f"🚨 ANOMALY<br>{label}: %{{y:.1f}} {unit}<br>%{{x}}<extra></extra>"
        ))

    fig.update_layout(
        height=280,
        margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15, 23, 42, 0.5)",
        font=dict(color="#94a3b8", size=11),
        xaxis=dict(gridcolor="rgba(30, 41, 59, 0.5)", showgrid=True),
        yaxis=dict(title=f"{label} ({unit})", gridcolor="rgba(30, 41, 59, 0.5)", showgrid=True),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font_size=10),
        showlegend=True
    )
    return fig


def _plot_anomaly_score_timeline(df) -> go.Figure:
    """Plots the Isolation Forest decision score over time with threshold line."""
    fig = go.Figure()

    # Threshold line at 0.0
    fig.add_hline(y=0.0, line_dash="dash", line_color="#ef4444", line_width=1,
                  annotation_text="Anomaly Threshold", annotation_font_color="#ef4444",
                  annotation_font_size=10, annotation_position="bottom right")

    # Color-coded scatter: green above threshold, red below
    nominal = df[df["anomaly_score"] >= 0.0]
    anomalous = df[df["anomaly_score"] < 0.0]

    if not nominal.empty:
        fig.add_trace(go.Scatter(
            x=nominal["timestamp"], y=nominal["anomaly_score"],
            mode="lines+markers", name="Nominal",
            line=dict(color="#10b981", width=2),
            marker=dict(size=4, color="#10b981")
        ))
    if not anomalous.empty:
        fig.add_trace(go.Scatter(
            x=anomalous["timestamp"], y=anomalous["anomaly_score"],
            mode="markers", name="Anomaly Detected",
            marker=dict(size=9, color="#ef4444", symbol="diamond",
                        line=dict(width=1, color="#fca5a5"))
        ))

    fig.update_layout(
        height=300,
        margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15, 23, 42, 0.5)",
        font=dict(color="#94a3b8", size=11),
        yaxis=dict(title="Decision Score", gridcolor="rgba(30, 41, 59, 0.5)"),
        xaxis=dict(gridcolor="rgba(30, 41, 59, 0.5)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font_size=10)
    )
    return fig


def render_vitals_ml_view(astronaut_profile: Dict[str, Any], time_window_hours: int) -> None:
    """Main rendering entry point for the Vitals & ML Anomaly Detection view."""

    render_mission_header("Astronaut Vital Signs & ML Anomaly Detection")
    render_medical_disclaimer(compact=True)

    ast_id = astronaut_profile["astronaut_id"]
    vitals_res = get_vitals_and_anomalies(astronaut_id=ast_id, hours=time_window_hours)
    df = vitals_res["data"]
    summary = vitals_res["summary"]
    source = vitals_res["source"]

    # Source provenance badge
    if source == "live":
        render_provenance_badge("real", f"Live Module — {vitals_res['status_note']}")
    else:
        render_provenance_badge("simulated", f"Simulated Fallback — {vitals_res['status_note']}")

    # ── Row 1: 5 Physiological KPI Cards ──
    st.markdown("#### 📊 Physiological Telemetry Summary")
    c1, c2, c3, c4, c5 = st.columns(5)

    hr = summary.get("latest_heart_rate", 70.0)
    spo2 = summary.get("latest_spo2", 98.0)
    bp_str = summary.get("latest_blood_pressure", "118/76 mmHg")
    temp = summary.get("latest_body_temp", 36.8)
    anom_count = summary.get("anomaly_count_24h", 0)

    with c1:
        render_metric_card("Heart Rate", f"{hr:.1f}", "bpm",
                           _status_for_value(hr, 55, 95), "55 – 95 bpm",
                           f"{summary.get('delta_hr_24h', 0):+.1f}")
    with c2:
        render_metric_card("Blood Oxygen SpO₂", f"{spo2:.1f}", "%",
                           _status_for_value(spo2, 95, 100), "95 – 100 %",
                           f"{summary.get('delta_spo2_24h', 0):+.1f}")
    with c3:
        render_metric_card("Blood Pressure", bp_str, "",
                           "nominal", "110/70 – 128/84 mmHg")
    with c4:
        render_metric_card("Core Body Temp", f"{temp:.2f}", "°C",
                           _status_for_value(temp, 36.4, 37.4), "36.4 – 37.4 °C")
    with c5:
        anom_status = "critical" if anom_count > 2 else ("warning" if anom_count > 0 else "nominal")
        render_metric_card("ML Anomalies", str(anom_count), f"in {time_window_hours}h",
                           anom_status, "Isolation Forest Detection")

    st.markdown("---")

    # ── Row 2: Interactive Telemetry & Anomaly Charts ──
    st.markdown("#### 📈 Physiological Telemetry & Anomaly Waveforms")

    if df.empty:
        st.info("No telemetry data available for the selected time window.")
        return

    tab_hr, tab_spo2, tab_bp, tab_temp = st.tabs(["❤️ Heart Rate", "🫁 SpO₂", "🩸 Blood Pressure", "🌡️ Temp & Respiration"])

    with tab_hr:
        st.plotly_chart(_plot_vital_with_band(df, "heart_rate_bpm", "Heart Rate", "bpm", 55, 95),
                        use_container_width=True)
    with tab_spo2:
        st.plotly_chart(_plot_vital_with_band(df, "spo2_pct", "SpO₂", "%", 95, 100),
                        use_container_width=True)
    with tab_bp:
        fig_bp = go.Figure()
        fig_bp.add_hrect(y0=110, y1=128, fillcolor="rgba(16, 185, 129, 0.06)", line_width=0)
        fig_bp.add_trace(go.Scatter(x=df["timestamp"], y=df["systolic_bp"], mode="lines",
                                    name="Systolic", line=dict(color="#f59e0b", width=2)))
        fig_bp.add_trace(go.Scatter(x=df["timestamp"], y=df["diastolic_bp"], mode="lines",
                                    name="Diastolic", line=dict(color="#38bdf8", width=2)))
        anom_bp = df[df["is_anomaly"] == True]
        if not anom_bp.empty:
            fig_bp.add_trace(go.Scatter(x=anom_bp["timestamp"], y=anom_bp["systolic_bp"],
                                        mode="markers", name="Anomaly",
                                        marker=dict(size=10, color="#ef4444", symbol="x")))
        fig_bp.update_layout(height=280, margin=dict(l=10, r=10, t=30, b=10),
                             paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15, 23, 42, 0.5)",
                             font=dict(color="#94a3b8"), yaxis_title="mmHg",
                             xaxis=dict(gridcolor="rgba(30,41,59,0.5)"),
                             yaxis=dict(gridcolor="rgba(30,41,59,0.5)"),
                             legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_bp, use_container_width=True)
    with tab_temp:
        fig_tr = make_subplots(rows=1, cols=2, subplot_titles=("Core Temperature (°C)", "Respiration Rate (br/min)"))
        fig_tr.add_trace(go.Scatter(x=df["timestamp"], y=df["body_temp_c"], mode="lines",
                                    line=dict(color="#f59e0b", width=2), name="Temp"), row=1, col=1)
        fig_tr.add_trace(go.Scatter(x=df["timestamp"], y=df["respiration_rate"], mode="lines",
                                    line=dict(color="#a78bfa", width=2), name="Resp Rate"), row=1, col=2)
        fig_tr.update_layout(height=280, margin=dict(l=10, r=10, t=40, b=10),
                             paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15, 23, 42, 0.5)",
                             font=dict(color="#94a3b8"), showlegend=False)
        fig_tr.update_xaxes(gridcolor="rgba(30,41,59,0.5)")
        fig_tr.update_yaxes(gridcolor="rgba(30,41,59,0.5)")
        st.plotly_chart(fig_tr, use_container_width=True)

    st.markdown("---")

    # ── Row 3: Isolation Forest ML Diagnostics ──
    st.markdown("#### 🤖 Isolation Forest ML Anomaly Diagnostics")
    col_score, col_log = st.columns([3, 2])

    with col_score:
        st.markdown("##### Decision Score Timeline")
        st.plotly_chart(_plot_anomaly_score_timeline(df), use_container_width=True)

    with col_log:
        st.markdown("##### Detected Anomaly Log")
        anom_rows = df[df["is_anomaly"] == True][["timestamp", "heart_rate_bpm", "spo2_pct", "systolic_bp", "anomaly_score"]]
        if not anom_rows.empty:
            st.dataframe(
                anom_rows.style.format({
                    "heart_rate_bpm": "{:.1f}",
                    "spo2_pct": "{:.1f}",
                    "systolic_bp": "{:.0f}",
                    "anomaly_score": "{:+.4f}"
                }),
                use_container_width=True,
                height=300
            )
        else:
            st.markdown(
                """
                <div class="telemetry-card nominal" style="text-align: center; padding: 30px;">
                    <span style="color: #10b981; font-weight: 700; font-size: 1.1rem;">
                        🟢 No physiological anomalies detected in selected window
                    </span>
                    <div style="color: #94a3b8; font-size: 0.85rem; margin-top: 8px;">
                        All biometric parameters within expected multidimensional bounds.
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
