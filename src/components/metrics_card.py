"""
SPACECARE Metrics Card Component
Renders high-contrast, status-haloed telemetry display cards.
"""

import streamlit as st
from typing import Optional


def render_metric_card(
    label: str,
    value: str,
    unit: str = "",
    status: str = "nominal",
    normal_range: str = "",
    delta: Optional[str] = None
) -> None:
    """
    Renders an aerospace telemetry card.
    
    Args:
        label: Metric title (e.g., 'Heart Rate', 'Cabin Pressure')
        value: Current formatted value (e.g., '72', '14.7')
        unit: Metric unit (e.g., 'bpm', 'psi', '%')
        status: 'nominal', 'advisory', 'warning', 'critical'
        normal_range: Reference baseline text (e.g., '60 - 100 bpm')
        delta: Optional delta or trend indicator (e.g., '+2 bpm')
    """
    status_lower = status.lower()
    if status_lower not in ("nominal", "advisory", "warning", "critical"):
        status_lower = "nominal"

    delta_html = f"<span style='color: #94a3b8; font-size: 0.8rem; margin-left: 8px;'>({delta})</span>" if delta else ""
    range_html = f"<div class='telemetry-sub'>Baseline: {normal_range}</div>" if normal_range else ""

    card_html = f"""
    <div class="telemetry-card {status_lower}">
        <div class="telemetry-label">{label}</div>
        <div class="telemetry-value">
            {value}<span class="telemetry-unit">{unit}</span>
            {delta_html}
        </div>
        {range_html}
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)
