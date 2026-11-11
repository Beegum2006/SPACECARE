"""
==============================================================================
SPACECARE: NASA Astronaut Health Monitoring & Early Warning System
Main Application Entrypoint & Command Center Overview
==============================================================================
"""

import streamlit as st
from pathlib import Path
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.db import init_database
from src.database.queries import get_astronauts, get_active_alerts
from src.components.mission_header import render_mission_header, render_crew_selector_sidebar
from src.components.disclaimers import render_medical_disclaimer, render_sidebar_disclaimer
from src.components.badges import render_provenance_badge

# Page Configuration
st.set_page_config(
    page_title="SPACECARE | Mission Control",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database schema and seed astronauts
init_database()

# Top Header & Disclaimers
render_mission_header("Mission Control Overview")
render_medical_disclaimer()

# Sidebar: Crew selection & persistent notice
selected_astronaut = render_crew_selector_sidebar()
render_sidebar_disclaimer()

# Main Command Center Layout
col_main, col_stats = st.columns([2, 1], gap="medium")

with col_main:
    st.markdown("### 🛰️ Mission Briefing: Expedition 71")
    st.markdown(
        """
        Welcome to **SPACECARE**, an aerospace physiological monitoring and early warning 
        architecture designed for extended orbital and deep-space missions.

        SPACECARE integrates **real NASA Open Science datasets** with **physiologically plausible simulated telemetry**
        to benchmark machine learning anomaly detection and evaluate crew health in real-time.
        """
    )

    render_provenance_badge("simulated", "Real-Time Telemetry Bus & ECLSS Life Support")

    st.markdown("#### 🧑‍🚀 Active Expedition 71 Crew Roster")
    astronauts = get_astronauts()
    
    if astronauts:
        crew_cols = st.columns(min(len(astronauts), 4))
        for idx, ast in enumerate(astronauts):
            with crew_cols[idx % 4]:
                st.markdown(
                    f"""
                    <div class="telemetry-card nominal" style="text-align: center;">
                        <div style="font-size: 1.8rem; margin-bottom: 4px;">🧑‍🚀</div>
                        <div style="font-weight: 700; color: #f8fafc; font-size: 0.95rem;">{ast['name']}</div>
                        <div style="color: #38bdf8; font-size: 0.78rem; font-family: monospace;">Callsign: {ast['callsign']}</div>
                        <div style="color: #94a3b8; font-size: 0.76rem; margin-top: 4px;">{ast['role']}</div>
                        <div style="margin-top: 8px;">
                            <span class="status-pill nominal">{ast['status']}</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    else:
        st.info("No crew members loaded. Head to the Crew Configuration console to register astronauts.")

    st.markdown("---")
    st.markdown("#### 🗺️ Mission Control Subsystems Navigation")
    st.markdown("Use the **left sidebar** to access the specialized operational consoles:")

    subsystems = [
        ("1 🚀 Astronaut Vitals", "Live telemetry streaming (HR, BP, SpO2, Temp, RR, HRV) with anomaly induction triggers."),
        ("2 🛰️ ISS Environment", "ECLSS cabin life support monitoring: cabin pressure, CO2 partial pressure, O2 %, humidity."),
        ("3 🔬 NASA OSDR Research", "Authentic NASA Open Science Data Repository spaceflight omics and physiological studies."),
        ("4 ☢️ Space Radiation", "Genuine NASA cosmic radiation measurements, dosimeter readings, and career exposure tracking."),
        ("5 🧠 Mental Health", "Circadian drift tracking, actigraphy sleep metrics, and NASA Task Load Index (NASA-TLX)."),
        ("6 🤖 ML Anomaly Detection", "Unsupervised machine learning (Isolation Forest) identifying multivariate physiological stress."),
        ("7 ⚠️ Alerts & Early Warning", "Multi-tiered warning hierarchy (Advisory, Warning, Critical) with flight surgeon checklists."),
        ("8 📋 Health Reports", "Clinical & mission summary reporting engine with downloadable medical review logs."),
        ("9 ⚙️ Crew Configuration", "Configure crew roster, add or edit astronauts, and tune physiological baselines.")
    ]

    for title, desc in subsystems:
        st.markdown(f"- **{title}**: {desc}")

with col_stats:
    st.markdown("### 📊 System Status Matrix")
    
    active_alerts = get_active_alerts()
    num_alerts = len(active_alerts)
    num_crew = len(astronauts)
    
    st.metric(label="Active Crew Onboard", value=f"{num_crew} Astronauts", delta="Nominal Roster")
    st.metric(label="Active Early Warnings", value=f"{num_alerts}", delta="0 Critical" if num_alerts == 0 else f"{num_alerts} Active", delta_color="inverse" if num_alerts > 0 else "normal")
    st.metric(label="Local Database", value="SQLite Connected", delta="spacecare.db")
    st.metric(label="Telemetry Bus", value="Online", delta="Ready")

    st.markdown("---")
    st.markdown("### 🔒 Data Integrity Guarantees")
    st.markdown(
        """
        - 🟢 **Real NASA Data**: Verified via official NASA Open Science Data Repository (OSDR) and Radiation portals.
        - ⚡ **Simulated Data**: Explicitly labeled mathematical simulations; never passed off as genuine flight recordings.
        - 🛡️ **Non-Diagnostic**: Prototype for educational and systems demonstration.
        """
    )
