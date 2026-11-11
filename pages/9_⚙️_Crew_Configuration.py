"""
SPACECARE - Subsystem 9: Crew Configuration
Allows dynamic configuration of the astronaut roster, crew size, and baseline physiological parameters.
"""

import streamlit as st
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.queries import (
    get_astronauts, add_astronaut, update_astronaut, delete_astronaut
)
from src.components.mission_header import render_mission_header, render_crew_selector_sidebar
from src.components.disclaimers import render_medical_disclaimer, render_sidebar_disclaimer
from src.components.badges import render_provenance_badge

st.set_page_config(
    page_title="SPACECARE | Crew Configuration",
    page_icon="⚙️",
    layout="wide"
)

render_mission_header("Crew Configuration & Roster Manager")
render_medical_disclaimer(compact=True)
selected_astronaut = render_crew_selector_sidebar()
render_sidebar_disclaimer()

st.markdown("### 🧑‍🚀 Astronaut Crew Roster & Baseline Parameters")
st.markdown(
    """
    Configure the active mission crew size and calibrate individual physiological baselines.
    Changes made here instantly update the simulated telemetry engine and anomaly detection models.
    """
)

render_provenance_badge("simulated", "Crew Management & Baseline Registry")

tab_roster, tab_add, tab_edit = st.tabs(["📋 Current Crew Roster", "➕ Add New Crew Member", "✏️ Calibrate Baselines"])

# TAB 1: Current Roster
with tab_roster:
    astronauts = get_astronauts()
    st.markdown(f"**Total Registered Crew:** `{len(astronauts)} Astronauts`")

    if astronauts:
        for ast in astronauts:
            with st.container():
                c1, c2, c3, c4, c5 = st.columns([1, 2, 2, 2, 1])
                with c1:
                    st.markdown("### 🧑‍🚀")
                with c2:
                    st.markdown(f"**{ast['name']}**")
                    st.caption(f"Callsign: **{ast['callsign']}** | Age: {ast['age']}")
                with c3:
                    st.markdown(f"**Role:** {ast['role']}")
                    st.caption(f"Agency: {ast['agency']} | Mission: {ast['mission']}")
                with c4:
                    st.markdown(f"**Baselines:** HR: `{ast['baseline_hr']}` bpm | SpO2: `{ast['baseline_spo2']}`%")
                    st.caption(f"BP: `{ast['baseline_bp_sys']}/{ast['baseline_bp_dia']}` mmHg | HRV: `{ast['baseline_hrv']}` ms")
                with c5:
                    if len(astronauts) > 1:
                        if st.button("Remove", key=f"del_{ast['id']}", type="secondary"):
                            delete_astronaut(ast['id'])
                            st.success(f"Removed {ast['name']}.")
                            st.rerun()
                    else:
                        st.caption("Min 1 crew")
                st.divider()
    else:
        st.warning("No astronauts currently registered in the database.")

# TAB 2: Add Astronaut
with tab_add:
    st.markdown("#### Register a New Crew Member")
    with st.form("form_add_astronaut", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        with col_a:
            new_name = st.text_input("Full Name", placeholder="e.g. Dr. Alex Mercer")
            new_callsign = st.text_input("Callsign", placeholder="e.g. Phoenix")
            new_role = st.selectbox("Mission Role", [
                "Commander",
                "Flight Engineer 1",
                "Flight Engineer 2",
                "Science Officer",
                "Medical Officer",
                "Mission Specialist",
                "Payload Specialist"
            ])
            new_agency = st.text_input("Space Agency", value="NASA")
            new_mission = st.text_input("Mission Name", value="Expedition 71 / ISS")
            new_age = st.number_input("Age", min_value=25, max_value=65, value=38)

        with col_b:
            st.markdown("**Personal Baseline Calibration**")
            b_hr = st.slider("Resting Heart Rate (bpm)", 50.0, 95.0, 68.0, step=0.5)
            b_spo2 = st.slider("Resting SpO2 (%)", 94.0, 100.0, 98.5, step=0.1)
            b_sys = st.slider("Systolic Blood Pressure (mmHg)", 100.0, 140.0, 118.0, step=1.0)
            b_dia = st.slider("Diastolic Blood Pressure (mmHg)", 60.0, 90.0, 76.0, step=1.0)
            b_temp = st.slider("Core Temperature (°C)", 36.0, 37.5, 36.8, step=0.1)
            b_rr = st.slider("Respiration Rate (breaths/min)", 10.0, 20.0, 14.0, step=0.5)
            b_hrv = st.slider("HRV RMSSD (ms)", 30.0, 90.0, 55.0, step=1.0)

        submitted = st.form_submit_button("Register Astronaut to Crew", type="primary")
        if submitted:
            if not new_name.strip() or not new_callsign.strip():
                st.error("Please provide both a Name and Callsign.")
            else:
                new_id = add_astronaut(
                    name=new_name.strip(),
                    callsign=new_callsign.strip(),
                    role=new_role,
                    agency=new_agency.strip(),
                    mission=new_mission.strip(),
                    age=int(new_age),
                    baseline_hr=b_hr,
                    baseline_spo2=b_spo2,
                    baseline_bp_sys=b_sys,
                    baseline_bp_dia=b_dia,
                    baseline_temp=b_temp,
                    baseline_rr=b_rr,
                    baseline_hrv=b_hrv
                )
                st.success(f"Astronaut {new_name} registered successfully (ID: {new_id}).")
                st.rerun()

# TAB 3: Calibrate Existing Crew
with tab_edit:
    if astronauts:
        st.markdown("#### Calibrate Baseline Metrics for Existing Crew")
        edit_target = st.selectbox(
            "Select Crew Member to Calibrate:",
            astronauts,
            format_func=lambda x: f"{x['name']} ({x['callsign']}) - {x['role']}"
        )
        if edit_target:
            with st.form(f"form_edit_{edit_target['id']}"):
                ec1, ec2 = st.columns(2)
                with ec1:
                    u_role = st.text_input("Role", value=edit_target['role'])
                    u_hr = st.slider("Resting HR (bpm)", 50.0, 95.0, float(edit_target['baseline_hr']), step=0.5)
                    u_spo2 = st.slider("Resting SpO2 (%)", 94.0, 100.0, float(edit_target['baseline_spo2']), step=0.1)
                    u_temp = st.slider("Core Temp (°C)", 36.0, 37.5, float(edit_target['baseline_temp']), step=0.1)
                with ec2:
                    u_sys = st.slider("Systolic BP (mmHg)", 100.0, 140.0, float(edit_target['baseline_bp_sys']), step=1.0)
                    u_dia = st.slider("Diastolic BP (mmHg)", 60.0, 90.0, float(edit_target['baseline_bp_dia']), step=1.0)
                    u_rr = st.slider("Respiration (breaths/min)", 10.0, 20.0, float(edit_target['baseline_rr']), step=0.5)
                    u_hrv = st.slider("HRV RMSSD (ms)", 30.0, 90.0, float(edit_target['baseline_hrv']), step=1.0)
                
                update_btn = st.form_submit_button("Save Calibration", type="primary")
                if update_btn:
                    update_astronaut(
                        edit_target['id'],
                        role=u_role,
                        baseline_hr=u_hr,
                        baseline_spo2=u_spo2,
                        baseline_bp_sys=u_sys,
                        baseline_bp_dia=u_dia,
                        baseline_temp=u_temp,
                        baseline_rr=u_rr,
                        baseline_hrv=u_hrv
                    )
                    st.success(f"Calibration updated for {edit_target['name']}.")
                    st.rerun()
