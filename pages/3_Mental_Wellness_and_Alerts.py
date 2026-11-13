"""
SPACECARE Page Router: Mental Wellness, Alerts & Reports
Thin routing wrapper — all logic lives in src/views/wellness_alerts_view.py
"""

import streamlit as st
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

st.set_page_config(
    page_title="SPACECARE | Wellness & Alerts",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

from src.components.sidebar import render_shared_sidebar
from src.views.wellness_alerts_view import render_wellness_alerts_view

selected_astronaut, time_window = render_shared_sidebar()
render_wellness_alerts_view(selected_astronaut, time_window)
