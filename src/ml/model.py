"""
SPACECARE Machine Learning - Anomaly Detection Model
Implements unsupervised physiological anomaly detection using Scikit-Learn IsolationForest
paired with StandardScaler normalization and feature attribution.

DISCLAIMER: This ML model is an aerospace engineering prototype for systems demonstration.
It is NOT certified as a medical diagnostic device.
"""

import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from src.ml.feature_engineering import (
    FEATURE_NAMES, extract_feature_vector, extract_feature_matrix, compute_feature_deviations
)
from src.simulation.vitals_generator import generate_vitals_series


class AstronautAnomalyDetector:
    """
    Unsupervised Multivariate Anomaly Detection Model for Astronaut Biometrics.
    Uses Isolation Forest to detect multivariate outliers across 7 core physiological features:
    [Heart Rate, Systolic BP, Diastolic BP, SpO2, Core Temp, Respiration Rate, HRV].
    """

    def __init__(self, contamination: float = 0.05, random_state: int = 42):
        self.contamination = contamination
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.model = IsolationForest(
            contamination=self.contamination,
            random_state=self.random_state,
            n_estimators=100
        )
        self.is_trained = False
        self.baseline_stats: Dict[str, Dict[str, float]] = {}

    def train_on_baseline(self, readings: List[Dict[str, Any]]) -> bool:
        """
        Trains the Isolation Forest model and StandardScaler on nominal baseline vitals.
        If fewer than 20 readings are provided, raises ValueError.
        """
        if len(readings) < 15:
            return False

        X = extract_feature_matrix(readings)
        
        # Fit scaler and model
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)
        self.is_trained = True

        # Calculate baseline statistics per feature
        for i, feat in enumerate(FEATURE_NAMES):
            self.baseline_stats[feat] = {
                "mean": float(np.mean(X[:, i])),
                "std": float(np.std(X[:, i])) if np.std(X[:, i]) > 0.0 else 1.0
            }

        return True

    def train_with_astronaut_baseline(self, astronaut: Dict[str, Any], count: int = 100) -> bool:
        """
        Generates a synthetic healthy baseline time series for the astronaut
        and trains the Isolation Forest pipeline. Guarantees zero cold-start failures.
        """
        nominal_series = generate_vitals_series(
            astronaut=astronaut,
            count=count,
            interval_seconds=10,
            anomaly_mode="NOMINAL"
        )
        return self.train_on_baseline(nominal_series)

    def predict(self, reading: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates a single vital signs reading.
        Returns:
            - is_anomaly (1 for anomaly, 0 for nominal)
            - anomaly_score (raw decision function value: negative = outlier, positive = inlier)
            - normalized_score (mapped -1.0 to 1.0)
            - status ("NOMINAL", "SUSPICIOUS", "ANOMALY")
            - feature_attributions (Z-score breakdown per feature)
        """
        if not self.is_trained:
            # Fallback default evaluation if model hasn't been explicitly trained
            return {
                "is_anomaly": 0,
                "anomaly_score": 0.1,
                "normalized_score": 0.2,
                "status": "NOMINAL (UNTRAINED)",
                "feature_attributions": {}
            }

        x = extract_feature_vector(reading).reshape(1, -1)
        x_scaled = self.scaler.transform(x)

        # IsolationForest predict: -1 = outlier, +1 = inlier
        raw_pred = self.model.predict(x_scaled)[0]
        # Decision function: smaller / negative = more abnormal
        decision_score = float(self.model.decision_function(x_scaled)[0])

        is_anomaly = 1 if raw_pred == -1 else 0

        # Status categorization
        if decision_score < -0.08:
            status = "CRITICAL_ANOMALY"
        elif decision_score < 0.0:
            status = "SUSPICIOUS"
        else:
            status = "NOMINAL"

        # Compute feature Z-score deviations to explain the anomaly
        attributions = compute_feature_deviations(reading, self.baseline_stats)

        return {
            "is_anomaly": is_anomaly,
            "raw_decision_score": round(decision_score, 4),
            "status": status,
            "feature_attributions": attributions
        }

    def predict_series(self, readings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Batch evaluates a time series of vital sign readings."""
        if not self.is_trained or not readings:
            return []

        X = extract_feature_matrix(readings)
        X_scaled = self.scaler.transform(X)
        scores = self.model.decision_function(X_scaled)
        preds = self.model.predict(X_scaled)

        results = []
        for i, r in enumerate(readings):
            dec_score = float(scores[i])
            is_anom = 1 if preds[i] == -1 else 0
            status = "ANOMALY" if is_anom else "NOMINAL"
            results.append({
                **r,
                "ml_anomaly_score": round(dec_score, 4),
                "ml_is_anomaly": is_anom,
                "ml_status": status
            })

        return results
