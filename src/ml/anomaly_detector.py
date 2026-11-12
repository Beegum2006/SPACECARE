"""
SPACECARE Machine Learning - Anomaly Detector
Implements unsupervised multivariate physiological anomaly detection using Scikit-Learn IsolationForest.
Includes missing-value imputation, feature scaling, model persistence with joblib,
and explainable feature deviation attributions.

IMPORTANT & DISCLAIMER:
- This machine learning system is an unsupervised aerospace engineering prototype trained on
  simulated astronaut telemetry for operational decision-support demonstration.
- It does NOT provide clinical diagnoses or replace professional aerospace flight surgeons.
- It is trained strictly on wearable physiological vitals, NOT mixed with omics assays or environmental logs.
"""

import joblib
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer

from src.ml.feature_engineering import FEATURE_NAMES, extract_feature_matrix
from src.simulation.vitals_generator import generate_vitals_series

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MODEL_DIR = PROJECT_ROOT / "data" / "models"
DEFAULT_MODEL_PATH = MODEL_DIR / "isolation_forest.joblib"

# 7 core wearable physiological vitals
VITAL_FEATURES = FEATURE_NAMES

DEFAULT_PHYSIOLOGICAL_BASELINES = {
    "heart_rate": 70.0,
    "blood_pressure_sys": 118.0,
    "blood_pressure_dia": 76.0,
    "spo2": 98.0,
    "core_temperature": 36.8,
    "respiration_rate": 14.0,
    "hrv_rmssd": 55.0
}


class AstronautAnomalyDetector:
    """
    Unsupervised Isolation Forest anomaly detector for astronaut wearable telemetry.
    """

    def __init__(
        self,
        contamination: float = 0.05,
        random_state: int = 42,
        n_estimators: int = 100
    ):
        self.contamination = contamination
        self.random_state = random_state
        self.n_estimators = n_estimators
        
        self.imputer = SimpleImputer(strategy="median")
        self.scaler = StandardScaler()
        self.model = IsolationForest(
            contamination=self.contamination,
            random_state=self.random_state,
            n_estimators=self.n_estimators
        )
        self.is_trained = False
        self.feature_names = VITAL_FEATURES
        self.baseline_stats: Dict[str, Dict[str, float]] = {}
        self.training_sample_count = 0

    def _prepare_matrix(self, readings: List[Dict[str, Any]]) -> np.ndarray:
        """Extract the shared seven-feature matrix; missing values remain NaN for imputation."""
        return extract_feature_matrix(readings)

    def train_on_baseline(self, readings: List[Dict[str, Any]]) -> bool:
        """Compatibility alias used by the original model.py implementation."""
        return self.train(readings)

    def train_with_astronaut_baseline(
        self, astronaut: Dict[str, Any], count: int = 100
    ) -> bool:
        """Train from a generated nominal baseline when database history is unavailable."""
        nominal_readings = generate_vitals_series(
            astronaut=astronaut,
            count=count,
            interval_seconds=10,
            anomaly_mode="NOMINAL",
        )
        return self.train(nominal_readings)

    def train(self, training_readings: List[Dict[str, Any]]) -> bool:
        """
        Trains the Isolation Forest pipeline on simulated astronaut vitals.
        Handles missing values, fits StandardScaler, and records baseline statistics.
        """
        if not training_readings or len(training_readings) < 10:
            return False

        X = self._prepare_matrix(training_readings)
        if np.all(np.isnan(X), axis=0).any():
            return False

        # Fit imputer and scaler
        X_imputed = self.imputer.fit_transform(X)
        X_scaled = self.scaler.fit_transform(X_imputed)

        # Fit Isolation Forest
        self.model.fit(X_scaled)
        self.is_trained = True
        self.training_sample_count = len(training_readings)

        # Store baseline distributions for explainability
        for idx, feat in enumerate(self.feature_names):
            vals = X_imputed[:, idx]
            self.baseline_stats[feat] = {
                "mean": float(np.mean(vals)),
                "std": float(np.std(vals)) if np.std(vals) > 0.0 else 1.0,
                "min": float(np.min(vals)),
                "max": float(np.max(vals))
            }

        return True

    def predict(self, reading: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates a single telemetry reading.
        Returns anomaly classification, decision score, and explainable feature contributions.
        """
        if not self.is_trained:
            return {
                "is_anomaly": 0,
                "raw_decision_score": 0.1,
                "anomaly_score_normalized": 0.5,
                "status": "NOMINAL (UNTRAINED)",
                "feature_contributions": {},
                "explanation": "Model is not yet trained. Run training using baseline telemetry."
            }

        x = self._prepare_matrix([reading])
        x_imputed = self.imputer.transform(x)
        x_scaled = self.scaler.transform(x_imputed)

        # Raw prediction: -1 = anomaly, +1 = nominal
        raw_pred = int(self.model.predict(x_scaled)[0])
        # Raw decision score: negative = outlier, positive = inlier
        raw_score = float(self.model.decision_function(x_scaled)[0])
        is_anomaly = 1 if raw_pred == -1 else 0

        # Normalized anomaly severity (0.0 = completely nominal, 1.0 = extreme anomaly)
        # Decision scores typically range from -0.3 to +0.25
        normalized_severity = float(np.clip((0.15 - raw_score) / 0.45, 0.0, 1.0))

        # Categorize status
        if is_anomaly == 1:
            status = "ANOMALOUS"
        elif raw_score < 0.03:
            status = "SUSPICIOUS"
        else:
            status = "NOMINAL"

        # Compute explainable feature deviations
        contributions = {}
        deviating_features = []
        for idx, feat in enumerate(self.feature_names):
            val = float(x_imputed[0, idx])
            stats = self.baseline_stats.get(feat, {"mean": val, "std": 1.0})
            mean = stats.get("mean", val)
            std = stats.get("std", 1.0)
            z = (val - mean) / std

            if abs(z) >= 2.0:
                severity = "HIGH"
                deviating_features.append(f"{feat} (Z={z:+.1f})")
            elif abs(z) >= 1.2:
                severity = "MODERATE"
                deviating_features.append(f"{feat} (Z={z:+.1f})")
            else:
                severity = "NOMINAL"

            contributions[feat] = {
                "value": round(val, 2),
                "baseline_mean": round(mean, 2),
                "z_score": round(z, 2),
                "deviation_severity": severity
            }

        explanation = (
            f"Isolation Forest flagged multivariate divergence driven by: {', '.join(deviating_features)}"
            if deviating_features else "All biometric parameters are within expected multidimensional bounds."
        )

        return {
            "is_anomaly": is_anomaly,
            "raw_decision_score": round(raw_score, 4),
            "normalized_severity": round(normalized_severity, 3),
            "status": status,
            "feature_contributions": contributions,
            "explanation": explanation
        }

    def predict_series(self, readings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Batch evaluates a time-series sequence of telemetry readings."""
        if not self.is_trained or not readings:
            return []

        X = self._prepare_matrix(readings)
        X_imputed = self.imputer.transform(X)
        X_scaled = self.scaler.transform(X_imputed)

        scores = self.model.decision_function(X_scaled)
        preds = self.model.predict(X_scaled)

        results = []
        for i, r in enumerate(readings):
            sc = float(scores[i])
            is_anom = 1 if preds[i] == -1 else 0
            results.append({
                **r,
                "ml_decision_score": round(sc, 4),
                "ml_is_anomaly": is_anom,
                "ml_status": "ANOMALY" if is_anom else "NOMINAL"
            })

        return results

    def save_model(self, file_path: Optional[Path] = None) -> Path:
        """Persists the trained model and scaler to disk using joblib."""
        if file_path is None:
            file_path = DEFAULT_MODEL_PATH

        file_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "contamination": self.contamination,
            "random_state": self.random_state,
            "n_estimators": self.n_estimators,
            "imputer": self.imputer,
            "scaler": self.scaler,
            "model": self.model,
            "is_trained": self.is_trained,
            "baseline_stats": self.baseline_stats,
            "training_sample_count": self.training_sample_count
        }
        joblib.dump(payload, str(file_path))
        return file_path

    @classmethod
    def load_model(cls, file_path: Optional[Path] = None) -> "AstronautAnomalyDetector":
        """Loads a persisted model from disk using joblib."""
        if file_path is None:
            file_path = DEFAULT_MODEL_PATH

        if not file_path.exists():
            instance = cls()
            return instance

        payload = joblib.load(str(file_path))
        instance = cls(
            contamination=payload.get("contamination", 0.05),
            random_state=payload.get("random_state", 42),
            n_estimators=payload.get("n_estimators", 100)
        )
        instance.imputer = payload.get("imputer", instance.imputer)
        instance.scaler = payload.get("scaler", instance.scaler)
        instance.model = payload.get("model", instance.model)
        instance.is_trained = payload.get("is_trained", False)
        instance.baseline_stats = payload.get("baseline_stats", {})
        instance.training_sample_count = payload.get("training_sample_count", 0)
        return instance
