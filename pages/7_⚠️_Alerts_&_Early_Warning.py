
"""
SPACECARE - Subsystem 7: Alerts & Early Warning System
Rule-based and ML-assisted prototype alert monitoring.
"""

import streamlit as st
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.queries import (
    get_active_alerts,
    acknowledge_alert,
    get_latest_vitals
)
from src.components.mission_header import (
    render_mission_header,
    render_crew_selector_sidebar
)
from src.components.disclaimers import (
    render_medical_disclaimer,
    render_sidebar_disclaimer
)
from src.components.badges import render_provenance_badge
from src.alerts.alert_engine import evaluate_vitals_for_alerts
from src.ml.anomaly_detector import AstronautAnomalyDetector


st.set_page_config(
    page_title="SPACECARE | Early Warning Alerts",
    page_icon="⚠️",
    layout="wide"
)

render_mission_header("Early Warning & Flight Surgeon Protocols")
render_medical_disclaimer(compact=True)

selected_astronaut = render_crew_selector_sidebar()
render_sidebar_disclaimer()

st.title("⚠️ Mission Alerts & Early Warning")
render_provenance_badge(
    "simulated",
    "Rule-based and ML-assisted prototype alert system"
)

st.info(
    "This is an educational engineering prototype. "
    "Alert thresholds and response checklists are illustrative, "
    "not NASA-approved procedures or medical advice."
)

if selected_astronaut is None:
    st.warning("No astronaut selected. Configure the crew first.")
    st.stop()

astronaut_id = selected_astronaut["id"]
astronaut_name = selected_astronaut.get("name", "Selected Astronaut")

st.subheader(f"Monitoring: {astronaut_name}")

latest_reading = get_latest_vitals(astronaut_id)

if latest_reading is None:
    st.warning("No telemetry readings available for this astronaut.")
else:
    st.write("Latest telemetry is available for alert evaluation.")

    if st.button("Evaluate Latest Telemetry", type="primary"):
        ml_result = None

        try:
            detector = AstronautAnomalyDetector.load_model()

            if detector.is_trained:
                ml_result = detector.predict(latest_reading)

        except Exception as error:
            st.warning(f"ML model unavailable: {error}")

        try:
            evaluate_vitals_for_alerts(
                selected_astronaut,
                latest_reading,
                ml_result
            )
            st.success("Telemetry evaluation completed.")
            st.rerun()

        except Exception as error:
            st.error(f"Alert evaluation failed: {error}")

st.divider()
st.subheader("Active Alerts")

alerts = get_active_alerts()
alerts = [
    alert for alert in alerts
    if alert.get("astronaut_id") == astronaut_id
]

if alerts:
    st.markdown(f"**Active alerts pending review:** {len(alerts)}")

    for alert in alerts:
        severity = alert["severity"]

        color = (
            "#ef4444" if severity == "CRITICAL"
            else "#f59e0b" if severity == "WARNING"
            else "#38bdf8"
        )

        st.markdown(
            f"""
            <div class="telemetry-card {severity.lower()}">
                <div style="display:flex; justify-content:space-between;">
                    <span style="font-weight:700; color:{color};">
                        [{severity}] {alert['title']}
                    </span>
                    <span style="font-size:0.75rem; color:#94a3b8;">
                        {alert['timestamp']}
                    </span>
                </div>
                <div style="color:#cbd5e1; margin:6px 0;">
                    {alert['message']}
                </div>
                <div style="background:rgba(0,0,0,0.3);
                            border-radius:4px; padding:8px;
                            font-size:0.78rem; color:#94a3b8;">
                    <strong>Prototype response checklist:</strong>
                    {alert['flight_surgeon_protocol']}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button(
            "Acknowledge Alert",
            key=f"ack_{alert['id']}"
        ):
            acknowledge_alert(alert["id"])
            st.success("Alert acknowledged.")
            st.rerun()

else:
    st.success("No active alerts are currently recorded.")
    st.caption(
        "This does not guarantee that all astronaut or life-support "
        "conditions are safe."
    )

st.divider()

st.caption(
    "SPACECARE | Rule-based + Isolation Forest monitoring | "
    "Prototype only, not for clinical decision-making."
)
