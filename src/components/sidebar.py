"""
SPACECARE Shared Sidebar Component (Member 3 - UI Workspace)
Provides a consistent sidebar across all Streamlit multi-page routes:
astronaut selector, telemetry time window, refresh control, and
module integration health indicators.

All data flows exclusively through src/components/data_adapter.py.
"""

import streamlit as st
from datetime import datetime, timezone
from typing import Tuple, Dict, Any

from src.components.data_adapter import get_crew_roster, get_module_integration_health
from src.components.mission_header import inject_custom_css


def _render_integration_status_sidebar() -> None:
    """Renders the module integration health panel in the sidebar."""
    health = get_module_integration_health()
    h_data = health["data"]
    h_summary = health["summary"]

    pct = h_summary.get("system_health_pct", 0.0)
    live = h_summary.get("live_module_count", 0)
    total = h_summary.get("total_modules", 5)
    status = h_summary.get("status", "DEGRADED")

    status_color = "#10b981" if status == "NOMINAL" else ("#f59e0b" if status == "DEGRADED" else "#ef4444")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔌 Module Integration")
    st.sidebar.markdown(
        f"""
        <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid #1e293b;
                    border-radius: 8px; padding: 10px; font-size: 0.78rem;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                <span style="color: #94a3b8;">System Health</span>
                <span style="color: {status_color}; font-weight: 700;">{status} ({live}/{total})</span>
            </div>
            <div style="background: #1e293b; border-radius: 4px; height: 6px; overflow: hidden;">
                <div style="background: {status_color}; width: {pct}%; height: 100%; border-radius: 4px;"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Per-domain status indicators
    domain_icons = {
        "nasa_data": ("🛰️", "NASA Data"),
        "ml": ("🤖", "ML Engine"),
        "alerts": ("⚠️", "Alerts"),
        "mental_health": ("🧠", "Mental Health"),
        "reports": ("📋", "Reports")
    }

    indicators = []
    for domain, (icon, label) in domain_icons.items():
        info = h_data.get(domain, {})
        is_live = info.get("is_live", False)
        dot = "🟢" if is_live else "🟡"
        indicators.append(f"{dot} {icon} {label}")

    st.sidebar.markdown(
        "<div style='font-size: 0.72rem; color: #94a3b8; line-height: 1.6; margin-top: 6px;'>"
        + "<br>".join(indicators)
        + "</div>",
        unsafe_allow_html=True
    )


def render_shared_sidebar() -> Tuple[Dict[str, Any], int]:
    """
    Renders the complete shared SPACECARE sidebar and returns the selected
    astronaut profile and telemetry time window.

    Returns:
        (selected_astronaut_profile_dict, time_window_hours)
    """
    inject_custom_css()

    # Branding and timestamp
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    st.sidebar.markdown(
        f"""
        <div style="text-align: center; padding: 8px 0 4px 0;">
            <div style="font-size: 1.3rem; font-weight: 800; letter-spacing: 0.06em; color: #f8fafc;">
                🚀 SPACECARE
            </div>
            <div style="font-size: 0.7rem; color: #64748b; margin-top: 2px;">
                ISS Expedition 71 • {now_utc}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.sidebar.markdown("---")

    # Crew roster and selection
    roster = get_crew_roster()
    crew_labels = [f"{a['name']} ({a['callsign']}) — {a['role']}" for a in roster]

    # Persist selected astronaut across pages
    if "selected_astronaut_id" not in st.session_state:
        st.session_state["selected_astronaut_id"] = roster[0]["astronaut_id"]

    # Find current index
    current_idx = 0
    for i, a in enumerate(roster):
        if a["astronaut_id"] == st.session_state["selected_astronaut_id"]:
            current_idx = i
            break

    st.sidebar.markdown("### 🧑‍🚀 Crew Telemetry Select")
    selected_label = st.sidebar.selectbox(
        "Active Astronaut:",
        crew_labels,
        index=current_idx,
        key="shared_sidebar_crew_select"
    )

    selected_idx = crew_labels.index(selected_label)
    selected_astronaut = roster[selected_idx]
    st.session_state["selected_astronaut_id"] = selected_astronaut["astronaut_id"]

    # Compact crew profile card
    ast_status = selected_astronaut.get("overall_status", "NOMINAL")
    status_color = "#10b981" if ast_status == "NOMINAL" else ("#f59e0b" if ast_status == "WARNING" else "#ef4444")
    st.sidebar.markdown(
        f"""
        <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid #1e293b;
                    border-radius: 8px; padding: 10px; margin-top: 6px; font-size: 0.8rem;">
            <strong>Crew Member:</strong> {selected_astronaut['name']}<br>
            <strong>Callsign:</strong> <span style="color: #38bdf8;">{selected_astronaut['callsign']}</span><br>
            <strong>Role:</strong> {selected_astronaut['role']}<br>
            <strong>Mission Day:</strong> {selected_astronaut.get('mission_day', 42)} |
            <strong>EVA:</strong> {selected_astronaut.get('eva_hours', 0.0)} hrs<br>
            <strong>Status:</strong> <span style="color: {status_color}; font-weight: 700;">{ast_status}</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.sidebar.markdown("---")

    # Telemetry time window
    if "time_window_hours" not in st.session_state:
        st.session_state["time_window_hours"] = 24

    time_window = st.sidebar.select_slider(
        "📡 Telemetry Time Window (hours):",
        options=[6, 12, 24, 48, 72, 168],
        value=st.session_state["time_window_hours"],
        key="shared_sidebar_time_slider"
    )
    st.session_state["time_window_hours"] = time_window

    # Refresh button
    if st.sidebar.button("🔄 Refresh Telemetry", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    # Module integration health panel
    _render_integration_status_sidebar()

    # Disclaimer
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        """
        <div style="font-size: 0.72rem; color: #94a3b8; line-height: 1.35; padding: 4px 6px;">
            <strong style="color: #f59e0b;">⚠️ Prototype Notice:</strong><br>
            Non-diagnostic research simulation. Not for medical treatment or clinical decision-making.
        </div>
        """,
        unsafe_allow_html=True
    )

    return selected_astronaut, time_window
