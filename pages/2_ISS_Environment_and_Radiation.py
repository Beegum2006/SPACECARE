"""
SPACECARE Page Router: ISS Environment & Space Radiation
Thin routing wrapper — all logic lives in src/views/env_radiation_view.py
"""

import streamlit as st
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

st.set_page_config(
    page_title="SPACECARE | ISS Environment & Radiation",
    page_icon="☢️",
    layout="wide",
    initial_sidebar_state="expanded",
)

from src.components.sidebar import render_shared_sidebar
from src.views.env_radiation_view import render_env_radiation_view

selected_astronaut, time_window = render_shared_sidebar()
render_env_radiation_view(selected_astronaut, time_window)
