"""
SPACECARE Machine Learning Pipeline - Feature Engineering
Extracts and normalizes multivariate physiological feature vectors from vitals telemetry
for unsupervised anomaly detection with Scikit-Learn Isolation Forest.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional

# Core 7-dimensional biometric feature space
FEATURE_NAMES = [
    "heart_rate",
    "blood_pressure_sys",
    "blood_pressure_dia",
    "spo2",
    "core_temperature",
    "respiration_rate",
    "hrv_rmssd"
]

FEATURE_DISPLAY_LABELS = {
    "heart_rate": "Heart Rate (bpm)",
    "blood_pressure_sys": "Systolic BP (mmHg)",
    "blood_pressure_dia": "Diastolic BP (mmHg)",
    "spo2": "SpO2 (%)",
    "core_temperature": "Core Temp (°C)",
    "respiration_rate": "Respiration (br/min)",
    "hrv_rmssd": "HRV RMSSD (ms)"
}


def extract_feature_vector(reading: Dict[str, Any]) -> np.ndarray:
    """Extracts a 1D feature array of the 7 core vital metrics from a telemetry reading."""
    return np.array([float(reading.get(f, 0.0)) for f in FEATURE_NAMES], dtype=np.float64)


def extract_feature_matrix(readings: List[Dict[str, Any]]) -> np.ndarray:
    """Converts a list of telemetry readings into a 2D feature matrix (N_samples, 7_features)."""
    if not readings:
        return np.empty((0, len(FEATURE_NAMES)))
    return np.array([[float(r.get(f, 0.0)) for f in FEATURE_NAMES] for r in readings], dtype=np.float64)


def compute_feature_deviations(
    current_reading: Dict[str, Any],
    baseline_stats: Dict[str, Dict[str, float]]
) -> Dict[str, Dict[str, Any]]:
    """
    Computes individual feature Z-scores and deviations against healthy astronaut baseline
    to identify which biometric contributes most to an anomalous ML score.
    """
    deviations = {}
    for feat in FEATURE_NAMES:
        val = float(current_reading.get(feat, 0.0))
        stats = baseline_stats.get(feat, {"mean": val, "std": 1.0})
        mean = stats.get("mean", val)
        std = stats.get("std", 1.0)
        std = max(0.1, std)  # Prevent division by zero

        z_score = (val - mean) / std
        abs_z = abs(z_score)

        # Flag severity contribution
        if abs_z > 3.0:
            severity = "CRITICAL"
        elif abs_z > 2.0:
            severity = "WARNING"
        elif abs_z > 1.2:
            severity = "ADVISORY"
        else:
            severity = "NOMINAL"

        deviations[feat] = {
            "label": FEATURE_DISPLAY_LABELS.get(feat, feat),
            "value": round(val, 2),
            "baseline_mean": round(mean, 2),
            "z_score": round(z_score, 2),
            "abs_z_score": round(abs_z, 2),
            "severity": severity
        }

    return deviations
