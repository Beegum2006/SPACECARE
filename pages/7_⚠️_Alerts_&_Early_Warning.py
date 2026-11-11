"""
SPACECARE - Subsystem 7: Alerts & Early Warning System
Multi-tiered alert matrix (Advisory, Warning, Critical) with Flight Surgeon intervention checklists.
"""

import streamlit as st
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.queries import get_active_alerts, acknowledge_alert
from src.components.mission_header import render_mission_header, render_crew_selector_sidebar
from src.components.disclaimers import render_medical_disclaimer, render_sidebar_disclaimer
from src.components.badges import render_provenance_badge

st.set_page_config(page_title="SPACECARE | Early Warning Alerts", page_icon="⚠️", layout="wide")

render_mission_header("Early Warning & Flight Surgeon Protocols")
render_medical_disclaimer(compact=True)
selected_astronaut = render_crew_selector_sidebar()
render_sidebar_disclaimer()

st.markdown("### ⚠️ Mission Alerts & Response Protocols")
render_provenance_badge("simulated", "Tiered Alert Escalation & Action Protocol Engine")

alerts = get_active_alerts()

if alerts:
    st.markdown(f"**Active Alerts Pending Review:** `{len(alerts)}`")
    for a in alerts:
        sev = a['severity']
        color = "#ef4444" if sev == "CRITICAL" else ("#f59e0b" if sev == "WARNING" else "#38bdf8")
        st.markdown(
            f"""
            <div class="telemetry-card {sev.lower()}">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-weight: 700; color: {color}; font-size: 0.95rem;">
                        [{sev}] {a['title']}
                    </span>
                    <span style="font-size: 0.75rem; color: #94a3b8;">{a['timestamp']}</span>
                </div>
                <div style="color: #cbd5e1; font-size: 0.85rem; margin: 6px 0;">{a['message']}</div>
                <div style="background: rgba(0,0,0,0.3); border-radius: 4px; padding: 8px; font-size: 0.78rem; color: #94a3b8;">
                    <strong style="color: #38bdf8;">Standard Protocol:</strong> {a['flight_surgeon_protocol']}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Acknowledge Alert", key=f"ack_{a['id']}"):
            acknowledge_alert(a['id'])
            st.success("Alert acknowledged.")
            st.rerun()
else:
    st.markdown(
        """
        <div class="telemetry-card nominal">
            <span style="color: #10b981; font-weight: 700;">🟢 ALL SUBSYSTEMS NOMINAL</span>
            <div style="color: #94a3b8; font-size: 0.85rem; margin-top: 4px;">
                No active critical, warning, or advisory alerts detected across crew telemetry or life support.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.info("📡 Phase 1 Scaffolding Ready. Real-time threshold rule evaluators and emergency protocol triggers will be activated in Phase 4.")
