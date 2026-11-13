"""Feature extraction utilities for SPACECARE physiological telemetry."""

from typing import Any, Dict, List
import numpy as np

FEATURE_NAMES = [
    "heart_rate",
    "blood_pressure_sys",
    "blood_pressure_dia",
    "spo2",
    "core_temperature",
    "respiration_rate",
    "hrv_rmssd",
]

FEATURE_DISPLAY_LABELS = {
    "heart_rate": "Heart Rate (bpm)",
    "blood_pressure_sys": "Systolic BP (mmHg)",
    "blood_pressure_dia": "Diastolic BP (mmHg)",
    "spo2": "SpO2 (%)",
    "core_temperature": "Core Temp (°C)",
    "respiration_rate": "Respiration (br/min)",
    "hrv_rmssd": "HRV RMSSD (ms)",
}


def _to_float_or_nan(value: Any) -> float:
    """Convert a telemetry value to float; invalid/missing values become NaN."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return number if np.isfinite(number) else float("nan")


def extract_feature_vector(reading: Dict[str, Any]) -> np.ndarray:
    """Extract one seven-feature vector, preserving missing values as NaN."""
    return np.asarray([_to_float_or_nan(reading.get(name)) for name in FEATURE_NAMES], dtype=np.float64)


def extract_feature_matrix(readings: List[Dict[str, Any]]) -> np.ndarray:
    """Convert telemetry dictionaries into an (N, 7) NumPy matrix."""
    if not readings:
        return np.empty((0, len(FEATURE_NAMES)), dtype=np.float64)
    return np.vstack([extract_feature_vector(reading) for reading in readings])


def compute_feature_deviations(
    current_reading: Dict[str, Any],
    baseline_stats: Dict[str, Dict[str, float]],
) -> Dict[str, Dict[str, Any]]:
    """Calculate per-feature Z-scores to help explain a model prediction."""
    deviations: Dict[str, Dict[str, Any]] = {}
    for feature in FEATURE_NAMES:
        value = _to_float_or_nan(current_reading.get(feature))
        stats = baseline_stats.get(feature, {"mean": 0.0, "std": 1.0})
        mean = float(stats.get("mean", 0.0))
        std = max(0.1, float(stats.get("std", 1.0)))
        if not np.isfinite(value):
            deviations[feature] = {
                "label": FEATURE_DISPLAY_LABELS[feature],
                "value": None,
                "baseline_mean": round(mean, 2),
                "z_score": None,
                "abs_z_score": None,
                "severity": "MISSING",
            }
            continue

        z_score = (value - mean) / std
        abs_z = abs(z_score)
        if abs_z > 3.0:
            severity = "CRITICAL"
        elif abs_z > 2.0:
            severity = "WARNING"
        elif abs_z > 1.2:
            severity = "ADVISORY"
        else:
            severity = "NOMINAL"

        deviations[feature] = {
            "label": FEATURE_DISPLAY_LABELS[feature],
            "value": round(value, 2),
            "baseline_mean": round(mean, 2),
            "z_score": round(z_score, 2),
            "abs_z_score": round(abs_z, 2),
            "severity": severity,
        }
    return deviations
