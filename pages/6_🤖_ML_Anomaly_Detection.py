"""
SPACECARE - Subsystem 6: Machine Learning Anomaly Detection
Unsupervised multivariate physiological anomaly detection using Scikit-Learn Isolation Forest.
"""

import streamlit as st
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.components.mission_header import render_mission_header, render_crew_selector_sidebar
from src.components.disclaimers import render_medical_disclaimer, render_sidebar_disclaimer
from src.components.badges import render_provenance_badge
from src.components.metrics_card import render_metric_card

st.set_page_config(page_title="SPACECARE | ML Anomaly Detection", page_icon="🤖", layout="wide")

render_mission_header("Machine Learning Anomaly Detection Console")
render_medical_disclaimer(compact=True)
selected_astronaut = render_crew_selector_sidebar()
render_sidebar_disclaimer()

st.markdown("### 🤖 Unsupervised Physiological Anomaly Radar")
render_provenance_badge("simulated", "Scikit-Learn IsolationForest & StandardScaler Pipeline")

ml1, ml2, ml3, ml4 = st.columns(4)
with ml1:
    render_metric_card("Model Status", "TRAINED", "", "nominal", "Online Isolation Forest")
with ml2:
    render_metric_card("Contamination Rate", "0.05", "", "nominal", "5% Outlier Prior")
with ml3:
    render_metric_card("Current Anomaly Score", "+0.28", "", "nominal", "> 0.0 Nominal")
with ml4:
    render_metric_card("Telemetry Features", "7", "vitals", "nominal", "HR, SpO2, BP, Temp, RR, HRV")

st.info("📡 Phase 1 Scaffolding Ready. Multi-variate outlier heatmaps, live anomaly scoring, and sensitivity sliders will be activated in Phase 4.")
