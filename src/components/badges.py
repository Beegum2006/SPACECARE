"""
SPACECARE Data Provenance Badges
Provides visual badges distinguishing real NASA Open Science datasets from simulated mission telemetry.
"""

import streamlit as st


def render_provenance_badge(data_type: str, source_label: str = "", dataset_id: str = "") -> None:
    """
    Renders an unambiguous data provenance badge.
    
    Args:
        data_type: 'real' for authentic NASA datasets, 'simulated' for synthetic telemetry.
        source_label: Human-readable origin (e.g. 'NASA OSDR OSD-166', 'Gaussian Drift Model')
        dataset_id: Identifier or DOI if available.
    """
    if data_type.lower() in ("real", "nasa", "verified"):
        id_part = f" ({dataset_id})" if dataset_id else ""
        label = source_label if source_label else "NASA Open Science Data Repository"
        badge_html = f"""
        <div style="margin: 8px 0 14px 0;">
            <span class="badge-real-nasa">
                🟢 VERIFIED NASA OPEN DATA: {label}{id_part}
            </span>
        </div>
        """
    else:
        label = source_label if source_label else "Physiological Stochastic Simulation Engine"
        badge_html = f"""
        <div style="margin: 8px 0 14px 0;">
            <span class="badge-simulated">
                ⚡ SYNTHETIC / SIMULATED MISSION TELEMETRY ({label})
            </span>
        </div>
        """
    st.markdown(badge_html, unsafe_allow_html=True)


def get_badge_markdown(data_type: str, label: str = "") -> str:
    """Returns markdown string representation for inclusion in tables or report text."""
    if data_type.lower() in ("real", "nasa", "verified"):
        return f"🟢 `[REAL NASA DATA: {label}]`"
    return f"⚡ `[SIMULATED: {label}]`"
