"""SPACECARE - Database-backed Isolation Forest anomaly detection dashboard."""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.components.mission_header import render_mission_header, render_crew_selector_sidebar
from src.components.disclaimers import render_medical_disclaimer, render_sidebar_disclaimer
from src.components.badges import render_provenance_badge
from src.ml.service import analyze_astronaut

st.set_page_config(page_title="SPACECARE | ML Anomaly Detection", page_icon="🤖", layout="wide")

render_mission_header("Machine Learning Anomaly Detection Console")
render_medical_disclaimer(compact=True)
selected_astronaut = render_crew_selector_sidebar()
render_sidebar_disclaimer()

st.markdown("### 🤖 Unsupervised Physiological Anomaly Radar")
render_provenance_badge("simulated", "Scikit-Learn Isolation Forest + StandardScaler + Median Imputation")

if selected_astronaut is None:
    st.warning("No astronaut is available. Add a crew member before running ML analysis.")
    st.stop()

try:
    analysis = analyze_astronaut(selected_astronaut)
except Exception as exc:
    st.error(f"ML analysis could not be completed: {exc}")
    st.stop()

prediction = analysis["prediction"]
latest = analysis["latest_reading"]
evaluation = analysis["evaluation"]

st.caption(
    f"Crew member: {selected_astronaut['name']} · "
    f"Training source: {analysis['training_source']} · "
    f"Latest reading: {analysis['latest_source']}"
)

status = prediction["status"]
metric_cols = st.columns(4)
metric_cols[0].metric("Model status", "TRAINED")
metric_cols[1].metric("Latest classification", status)
metric_cols[2].metric("Decision score", f"{prediction['raw_decision_score']:+.4f}")
metric_cols[3].metric("Training samples", analysis["training_samples"])

if prediction["is_anomaly"]:
    st.error("Isolation Forest classified the latest telemetry reading as an anomaly.")
elif status == "SUSPICIOUS":
    st.warning("The reading is near the model's decision boundary. Review the feature deviations.")
else:
    st.success("The latest telemetry reading is classified as nominal by the model.")

st.markdown("#### Latest telemetry")
feature_labels = {
    "heart_rate": "Heart rate (bpm)",
    "blood_pressure_sys": "Systolic BP (mmHg)",
    "blood_pressure_dia": "Diastolic BP (mmHg)",
    "spo2": "SpO2 (%)",
    "core_temperature": "Core temperature (°C)",
    "respiration_rate": "Respiration rate (breaths/min)",
    "hrv_rmssd": "HRV RMSSD (ms)",
}
cols = st.columns(4)
for index, (feature, label) in enumerate(feature_labels.items()):
    value = latest.get(feature)
    display_value = "Missing" if value is None else str(value)
    cols[index % 4].metric(label, display_value)

st.markdown("#### Feature-level explanation")
contributions = prediction.get("feature_contributions", {})
if contributions:
    contribution_rows = []
    for feature, details in contributions.items():
        contribution_rows.append({
            "Feature": feature_labels.get(feature, feature),
            "Reading": details["value"],
            "Baseline mean": details["baseline_mean"],
            "Z-score": details["z_score"],
            "Deviation": details["deviation_severity"],
        })
    st.dataframe(pd.DataFrame(contribution_rows), use_container_width=True, hide_index=True)
    st.info(prediction["explanation"])
else:
    st.info("No feature attribution is available.")

st.markdown("#### Model evaluation")
if evaluation:
    eval_cols = st.columns(3)
    eval_cols[0].metric("Precision", f"{evaluation['precision']:.2%}")
    eval_cols[1].metric("Recall", f"{evaluation['recall']:.2%}")
    eval_cols[2].metric("F1-score", f"{evaluation['f1_score']:.2%}")
    with st.expander("Evaluation details"):
        st.write(f"Training samples: {evaluation['training_samples']}")
        st.write(f"Test samples: {evaluation['test_samples']}")
        st.write(f"Labeled anomalies in test set: {evaluation['test_anomalies']}")
        st.markdown("**Confusion matrix** (rows = actual, columns = predicted)")
        st.dataframe(
            pd.DataFrame(
                [[evaluation["true_negative"], evaluation["false_positive"]],
                 [evaluation["false_negative"], evaluation["true_positive"]]],
                index=["Actual nominal", "Actual anomaly"],
                columns=["Predicted nominal", "Predicted anomaly"],
            ),
            use_container_width=True,
        )
else:
    st.info(
        "Precision, recall and F1-score are shown when the database contains enough "
        "nominal training rows and labeled anomaly examples."
    )

if analysis["history"]:
    st.markdown("#### Recent anomaly trend")
    recent = analysis["detector"].predict_series(analysis["history"][-100:])
    trend = pd.DataFrame([
        {
            "Timestamp": row.get("timestamp", str(index)),
            "Isolation Forest decision score": row["ml_decision_score"],
        }
        for index, row in enumerate(recent)
    ])
    if not trend.empty:
        trend = trend.set_index("Timestamp")
        st.line_chart(trend, use_container_width=True)
else:
    st.info("No stored telemetry history is available yet. A synthetic sample is being used for demonstration.")

st.caption(
    "Prototype limitation: the model is trained on nominal physiological telemetry and detects "
    "statistical outliers. It is not a medical diagnostic system. Evaluation metrics depend on "
    "the available simulated labels and should not be interpreted as clinical accuracy."
)
