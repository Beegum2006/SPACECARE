
"""
SPACECARE - Subsystem 6: Machine Learning Anomaly Detection
Isolation Forest based simulated astronaut telemetry monitoring.
Engineering prototype only - not a diagnostic system.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.components.mission_header import (
    render_mission_header,
    render_crew_selector_sidebar
)
from src.components.disclaimers import (
    render_medical_disclaimer,
    render_sidebar_disclaimer
)
from src.database.queries import (
    get_vitals_history,
    get_latest_vitals
)
from src.ml.anomaly_detector import AstronautAnomalyDetector


st.set_page_config(
    page_title="SPACECARE | ML Anomaly Detection",
    page_icon="🤖",
    layout="wide"
)

render_mission_header("Machine Learning Anomaly Detection Console")
render_medical_disclaimer(compact=True)

selected_astronaut = render_crew_selector_sidebar()
render_sidebar_disclaimer()

st.title("🤖 Unsupervised Physiological Anomaly Detection")
st.caption(
    "Isolation Forest | Seven physiological features | "
    "Simulated telemetry only"
)

st.info(
    "This is an engineering prototype. ML results are not medical "
    "diagnoses or NASA-certified clinical alerts."
)

if selected_astronaut is None:
    st.warning("No astronaut selected. Please configure the crew first.")
    st.stop()

astronaut_id = selected_astronaut["id"]
astronaut_name = selected_astronaut.get("name", "Selected Astronaut")

st.subheader(f"Astronaut: {astronaut_name}")

# Load the saved model once per Streamlit session.
if "spacecare_ml_detector" not in st.session_state:
    try:
        st.session_state["spacecare_ml_detector"] = (
            AstronautAnomalyDetector.load_model()
        )
    except Exception as error:
        st.error(f"Could not load saved ML model: {error}")
        st.session_state["spacecare_ml_detector"] = (
            AstronautAnomalyDetector()
        )

detector = st.session_state["spacecare_ml_detector"]

# Retrieve telemetry from the existing database.
history = get_vitals_history(astronaut_id, limit=500)
latest_reading = get_latest_vitals(astronaut_id)

st.subheader("1. Model Training")

st.write(
    "The model is trained only on nominal simulated readings. "
    "At least 10 valid readings are required."
)

if st.button("Train / Retrain Isolation Forest", type="primary"):
    if not history:
        st.error("No telemetry history found for this astronaut.")
    else:
        new_detector = AstronautAnomalyDetector()

        with st.spinner("Training Isolation Forest..."):
            trained = new_detector.train(history)

        if trained:
            try:
                saved_path = new_detector.save_model()
                st.session_state["spacecare_ml_detector"] = new_detector
                detector = new_detector
                st.success(
                    f"Training successful! "
                    f"{new_detector.training_sample_count} nominal "
                    f"simulated readings used."
                )
                st.caption(f"Model saved at: {saved_path}")
            except Exception as error:
                st.error(f"Model trained but could not be saved: {error}")
        else:
            st.error(
                "Training failed. Need at least 10 valid nominal "
                "simulated readings with usable feature values."
            )

st.divider()
st.subheader("2. Model Status")

status_col1, status_col2, status_col3 = st.columns(3)

with status_col1:
    st.metric(
        "Model Status",
        "TRAINED" if detector.is_trained else "NOT TRAINED"
    )

with status_col2:
    st.metric(
        "Training Samples",
        detector.training_sample_count if detector.is_trained else 0
    )

with status_col3:
    st.metric(
        "Features",
        len(detector.feature_names)
    )

if detector.is_trained:
    st.success(f"Training source: {detector.training_source}")
    st.caption(f"Contamination rate: {detector.contamination}")
else:
    st.warning("Train the model to enable anomaly prediction.")

st.divider()
st.subheader("3. Latest Telemetry Prediction")

if latest_reading is None:
    st.warning("No vital readings available for this astronaut.")
elif not detector.is_trained:
    st.info("Train the model first to analyse the latest reading.")
else:
    result = detector.predict(latest_reading)

    if result["status"] in (
        "REJECTED_NON_SIMULATED",
        "INVALID_INPUT",
        "UNTRAINED"
    ):
        st.warning(result["explanation"])
    else:
        score_col1, score_col2, score_col3 = st.columns(3)

        with score_col1:
            st.metric("Prediction", result["status"])

        with score_col2:
            st.metric(
                "Anomaly Score",
                (
                    f"{result['normalized_severity'] * 100:.1f}%"
                    if result["normalized_severity"] is not None
                    else "N/A"
                )
            )

        with score_col3:
            st.metric(
                "Decision Score",
                (
                    result["raw_decision_score"]
                    if result["raw_decision_score"] is not None
                    else "N/A"
                )
            )

        if result["is_anomaly"] == 1:
            st.error("ML model detected an anomalous telemetry pattern.")
        elif result["status"] == "SUSPICIOUS":
            st.warning("Unusual pattern detected. Further monitoring suggested.")
        else:
            st.success("No Isolation Forest anomaly detected.")

        st.write("**Model explanation:**", result["explanation"])

        st.caption(
            "Anomaly score is a prototype-normalized model score, "
            "not a probability of illness."
        )

        st.divider()
        st.subheader("4. Feature-wise Baseline Deviations")

        contributions = result["feature_contributions"]

        if contributions:
            feature_rows = []

            for feature, details in contributions.items():
                feature_rows.append({
                    "Feature": feature,
                    "Current Value": details["value"],
                    "Baseline Mean": details["baseline_mean"],
                    "Z-score": details["z_score"],
                    "Deviation": details["deviation_severity"]
                })

            feature_df = pd.DataFrame(feature_rows)
            st.dataframe(feature_df, use_container_width=True)

            st.caption(
                "Z-scores show deviation from the training baseline. "
                "They are descriptive deviations, not true model feature "
                "attributions or clinical thresholds."
            )

st.divider()
st.subheader("5. Telemetry History")

if history:
    history_df = pd.DataFrame(history)

    if "is_simulated" in history_df.columns:
        simulated_df = history_df[
            history_df["is_simulated"].astype(str).isin(["1", "True", "true"])
        ].copy()
    else:
        simulated_df = pd.DataFrame()

    if not simulated_df.empty and detector.is_trained:
        predictions = detector.predict_series(
            simulated_df.to_dict("records")
        )

        prediction_df = pd.DataFrame(predictions)

        st.write("Historical ML predictions (simulated readings only)")

        if "timestamp" in prediction_df.columns:
           chart = px.line(
    prediction_df,
    x="timestamp",
    y="ml_decision_score",
    title="Historical ML Decision Score",
    labels={
        "timestamp": "Time",
        "ml_decision_score": "Isolation Forest decision score"
    }
)
        st.plotly_chart(chart, use_container_width=True)
   
        display_columns = [
            col for col in [
                "timestamp",
                "heart_rate",
                "spo2",
                "core_temperature",
                "ml_status",
                "ml_anomaly_score"
            ]
            if col in prediction_df.columns
        ]

        st.dataframe(
            prediction_df[display_columns].tail(50),
            use_container_width=True
        )
    else:
        st.info(
            "Simulated telemetry history is available, but train the "
            "model to view historical predictions."
        )
else:
    st.info("No telemetry history is available yet.")

st.divider()
st.caption(
    "SPACECARE ML subsystem | Isolation Forest | "
    "Simulated telemetry prototype | Not for clinical decision-making"
)
