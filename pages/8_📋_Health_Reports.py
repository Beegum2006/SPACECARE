"""
SPACECARE - Subsystem 8: Health & Mission Reports
Clinical-format mission summary generator with downloadable PDF/Markdown export.
"""

import streamlit as st
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.queries import get_reports_for_astronaut
from src.components.mission_header import render_mission_header, render_crew_selector_sidebar
from src.components.disclaimers import render_medical_disclaimer, render_sidebar_disclaimer
from src.components.badges import render_provenance_badge

st.set_page_config(page_title="SPACECARE | Health Reports", page_icon="📋", layout="wide")

render_mission_header("Mission & Clinical Health Reports")
render_medical_disclaimer(compact=True)
selected_astronaut = render_crew_selector_sidebar()
render_sidebar_disclaimer()

st.markdown("### 📋 Flight Surgeon Mission Health Briefs")
render_provenance_badge("simulated", "Automated Clinical Summary Engine")

if selected_astronaut:
    st.markdown(f"**Selected Astronaut:** `{selected_astronaut['name']} ({selected_astronaut['callsign']})`")
    
    reports = get_reports_for_astronaut(selected_astronaut['id'])
    if reports:
        for r in reports:
            with st.expander(f"📄 {r['report_title']} - Mission Day {r['mission_day']}"):
                st.markdown(f"**Generated:** `{r['generated_at']}` | **Status:** `{r['overall_status']}`")
                st.markdown(r['executive_summary'])
                st.markdown(f"**Radiation Accumulated:** `{r['radiation_accumulated_msv']} mSv`")
                st.markdown(f"**Anomalies Detected:** `{r['anomalies_detected_count']}`")
    else:
        st.info(f"No archived reports found for {selected_astronaut['name']}. Phase 5 will enable one-click report generation with export.")

st.info("📡 Phase 1 Scaffolding Ready. PDF/Markdown export engines, anomaly incident reviews, and signature blocks will be activated in Phase 5.")
