"""
SPACECARE Mission Header Component
Renders the top Mission Control header, MET clock, crew selector, and styles.
"""

import streamlit as st
from pathlib import Path
from datetime import datetime, timezone
from src.database.queries import get_astronauts, get_active_alerts

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CSS_PATH = PROJECT_ROOT / "assets" / "css" / "style.css"


def inject_custom_css() -> None:
    """Injects the Mission Control CSS stylesheet into the Streamlit app."""
    if CSS_PATH.exists():
        with open(CSS_PATH, "r", encoding="utf-8") as f:
            css_content = f.read()
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)


def get_mission_elapsed_time(mission_day: int = 42) -> str:
    """Calculates simulated Mission Elapsed Time (MET) based on mission day and current UTC."""
    now = datetime.now(timezone.utc)
    return f"MET {mission_day:03d}d:{now.hour:02d}h:{now.minute:02d}m:{now.second:02d}s"


def render_mission_header(active_page_title: str = "Command Center") -> None:
    """Renders the top Mission Control status banner and telemetry clock."""
    inject_custom_css()
    met = get_mission_elapsed_time()
    
    # Check active alerts for global status
    active_alerts = get_active_alerts(limit=5)
    crit_count = sum(1 for a in active_alerts if a["severity"] == "CRITICAL")
    warn_count = sum(1 for a in active_alerts if a["severity"] == "WARNING")
    
    if crit_count > 0:
        status_text = f"CRITICAL ({crit_count})"
        status_class = "critical"
    elif warn_count > 0:
        status_text = f"WARNING ({warn_count})"
        status_class = "warning"
    else:
        status_text = "NOMINAL"
        status_class = "nominal"

    st.markdown(
        f"""
        <div class="mission-header-bar">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 14px;">
                <div>
                    <h1 class="mission-title">
                        🚀 SPACECARE <span style="font-size: 1.1rem; color: #38bdf8; font-weight: 500;">| {active_page_title}</span>
                    </h1>
                    <p class="mission-subtitle">
                        NASA Astronaut Physiological Monitoring & Early Warning System • ISS Expedition 71
                    </p>
                </div>
                <div style="display: flex; align-items: center; gap: 14px; flex-wrap: wrap;">
                    <div class="met-clock">{met}</div>
                    <span class="status-pill {status_class}">SYSTEM: {status_text}</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_crew_selector_sidebar():
    """
    Renders crew roster selection in the sidebar.
    Returns the selected astronaut dictionary.
    """
    astronauts = get_astronauts()
    if not astronauts:
        st.sidebar.warning("No crew members found in database.")
        return None

    crew_names = [f"{a['name']} ({a['callsign']}) - {a['role']}" for a in astronauts]
    
    # Store selected astronaut in session state for persistence across pages
    default_index = 0
    if "selected_astronaut_id" in st.session_state:
        for i, a in enumerate(astronauts):
            if a["id"] == st.session_state["selected_astronaut_id"]:
                default_index = i
                break

    st.sidebar.markdown("### 🧑‍🚀 Crew Telemetry Select")
    selected_name = st.sidebar.selectbox(
        "Active Astronaut:",
        crew_names,
        index=default_index,
        key="sidebar_crew_select"
    )

    selected_index = crew_names.index(selected_name)
    selected_astronaut = astronauts[selected_index]
    st.session_state["selected_astronaut_id"] = selected_astronaut["id"]
    st.session_state["selected_astronaut"] = selected_astronaut

    # Display mini crew card in sidebar
    st.sidebar.markdown(
        f"""
        <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid #1e293b; border-radius: 8px; padding: 10px; margin-top: 6px; font-size: 0.8rem;">
            <strong>Crew Member:</strong> {selected_astronaut['name']}<br>
            <strong>Callsign:</strong> <span style="color: #38bdf8;">{selected_astronaut['callsign']}</span><br>
            <strong>Role:</strong> {selected_astronaut['role']}<br>
            <strong>Mission:</strong> {selected_astronaut['mission']}
        </div>
        """,
        unsafe_allow_html=True
    )

    return selected_astronaut
