
"""
SPACECARE Machine Learning - Anomaly Detector

Unsupervised multivariate physiological anomaly detection
using Scikit-Learn Isolation Forest.

IMPORTANT:
- Training accepts only explicitly simulated telemetry.
- Training uses only nominal simulated readings.
- This is an engineering prototype, not a diagnostic system.
"""

import joblib
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MODEL_DIR = PROJECT_ROOT / "data" / "models"
DEFAULT_MODEL_PATH = MODEL_DIR / "isolation_forest.joblib"

VITAL_FEATURES = [
    "heart_rate",
    "blood_pressure_sys",
    "blood_pressure_dia",
    "spo2",
    "core_temperature",
    "respiration_rate",
    "hrv_rmssd"
]

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
    """Isolation Forest detector for simulated astronaut vital signs."""

    def __init__(
        self,
        contamination: float = 0.05,
        random_state: int = 42,
        n_estimators: int = 100
    ):
        if not 0.0 < contamination <= 0.5:
            raise ValueError("Contamination must be greater than 0 and at most 0.5.")

        self.contamination = contamination
        self.random_state = random_state
        self.n_estimators = n_estimators

        self.imputer = SimpleImputer(strategy="median")
        self.scaler = StandardScaler()

        self.model = IsolationForest(
            contamination=contamination,
            random_state=random_state,
            n_estimators=n_estimators
        )

        self.is_trained = False
        self.feature_names = list(VITAL_FEATURES)
        self.baseline_stats = {}
        self.training_sample_count = 0
        self.training_source = "NOT_TRAINED"

    def _prepare_matrix(self, readings: List[Dict[str, Any]]) -> np.ndarray:
        """Convert telemetry dictionaries into a validated numeric matrix."""

        if not readings:
            return np.empty((0, len(self.feature_names)), dtype=np.float64)

        matrix = []

        for reading in readings:
            row = []

            for feature in self.feature_names:
                value = reading.get(feature)

                try:
                    numeric_value = float(value)
                    if not np.isfinite(numeric_value):
                        numeric_value = np.nan
                except (ValueError, TypeError):
                    numeric_value = np.nan

                row.append(numeric_value)

            matrix.append(row)

        return np.asarray(matrix, dtype=np.float64)

    def _validate_training_readings(
        self,
        readings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Keep only explicitly simulated, nominal telemetry."""

        valid_readings = []

        for reading in readings:
            if str(reading.get("is_simulated", "")) not in ("1", "True", "true"):
                continue

            anomaly_flag = reading.get("anomaly_flag", 0)

            try:
                if int(anomaly_flag or 0) != 0:
                    continue
            except (ValueError, TypeError):
                continue

            valid_readings.append(reading)

        return valid_readings

    def train(self, training_readings: List[Dict[str, Any]]) -> bool:
        """
        Train only on nominal simulated telemetry.

        At least 10 valid readings are required.
        Returns False if there is insufficient usable data.
        """

        valid_readings = self._validate_training_readings(training_readings)

        if len(valid_readings) < 10:
            return False

        X = self._prepare_matrix(valid_readings)

        # Reject features with no valid observations.
        if np.any(np.all(np.isnan(X), axis=0)):
            return False

        # Fit preprocessing pipeline.
        X_imputed = self.imputer.fit_transform(X)
        X_scaled = self.scaler.fit_transform(X_imputed)

        # Fit Isolation Forest.
        self.model.fit(X_scaled)

        self.is_trained = True
        self.training_sample_count = len(valid_readings)
        self.training_source = "NOMINAL_SIMULATED_TELEMETRY"

        # Store descriptive baseline statistics.
        self.baseline_stats = {}

        for index, feature in enumerate(self.feature_names):
            values = X_imputed[:, index]
            std = float(np.std(values))

            self.baseline_stats[feature] = {
                "mean": float(np.mean(values)),
                "std": std if std > 0 else 1.0,
                "min": float(np.min(values)),
                "max": float(np.max(values))
            }

        return True

    def predict(self, reading: Dict[str, Any]) -> Dict[str, Any]:
        """Predict whether one explicitly simulated reading is anomalous."""

        if str(reading.get("is_simulated", "")) not in ("1", "True", "true"):
            return {
                "is_anomaly": 0,
                "raw_decision_score": None,
                "normalized_severity": None,
                "status": "REJECTED_NON_SIMULATED",
                "feature_contributions": {},
                "explanation": "ML detector accepts simulated telemetry only."
            }

        if not self.is_trained:
            return {
                "is_anomaly": 0,
                "raw_decision_score": None,
                "normalized_severity": None,
                "status": "UNTRAINED",
                "feature_contributions": {},
                "explanation": "Train the model using nominal simulated telemetry first."
            }

        X = self._prepare_matrix([reading])

        if np.all(np.isnan(X)):
            return {
                "is_anomaly": 0,
                "raw_decision_score": None,
                "normalized_severity": None,
                "status": "INVALID_INPUT",
                "feature_contributions": {},
                "explanation": "No valid physiological feature values were supplied."
            }

        X_imputed = self.imputer.transform(X)
        X_scaled = self.scaler.transform(X_imputed)

        prediction = int(self.model.predict(X_scaled)[0])
        raw_score = float(self.model.decision_function(X_scaled)[0])

        is_anomaly = 1 if prediction == -1 else 0

        normalized_severity = float(
            np.clip((0.15 - raw_score) / 0.45, 0.0, 1.0)
        )

        if is_anomaly:
            status = "ANOMALOUS"
        elif raw_score < 0.03:
            status = "SUSPICIOUS"
        else:
            status = "NOMINAL"

        # Descriptive baseline deviations, not model feature attribution.
        contributions = {}

        for index, feature in enumerate(self.feature_names):
            value = float(X_imputed[0, index])
            stats = self.baseline_stats[feature]

            mean = stats["mean"]
            std = stats["std"]
            z_score = (value - mean) / std

            if abs(z_score) >= 2.0:
                deviation = "HIGH"
            elif abs(z_score) >= 1.2:
                deviation = "MODERATE"
            else:
                deviation = "NOMINAL"

            contributions[feature] = {
                "value": round(value, 2),
                "baseline_mean": round(mean, 2),
                "z_score": round(z_score, 2),
                "deviation_severity": deviation
            }

        deviating_features = [
            feature
            for feature, details in contributions.items()
            if details["deviation_severity"] != "NOMINAL"
        ]

        explanation = (
            "Baseline deviations detected in: "
            + ", ".join(deviating_features)
            if deviating_features
            else "No significant individual baseline deviations detected."
        )

        return {
            "is_anomaly": is_anomaly,
            "raw_decision_score": round(raw_score, 4),
            "normalized_severity": round(normalized_severity, 3),
            "status": status,
            "feature_contributions": contributions,
            "explanation": explanation
        }

    def predict_series(
        self,
        readings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Evaluate a sequence of simulated readings."""

        if not self.is_trained or not readings:
            return []

        results = []

        for reading in readings:
            result = self.predict(reading)

            results.append({
                **reading,
                "ml_decision_score": result["raw_decision_score"],
                "ml_anomaly_score": result["normalized_severity"],
                "ml_is_anomaly": result["is_anomaly"],
                "ml_status": result["status"]
            })

        return results

    def save_model(self, file_path: Optional[Path] = None) -> Path:
        """Save the trained detector."""

        if not self.is_trained:
            raise RuntimeError("Cannot save an untrained model.")

        if file_path is None:
            file_path = DEFAULT_MODEL_PATH

        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "contamination": self.contamination,
            "random_state": self.random_state,
            "n_estimators": self.n_estimators,
            "feature_names": self.feature_names,
            "imputer": self.imputer,
            "scaler": self.scaler,
            "model": self.model,
            "is_trained": self.is_trained,
            "baseline_stats": self.baseline_stats,
            "training_sample_count": self.training_sample_count,
            "training_source": self.training_source
        }

        joblib.dump(payload, str(file_path))
        return file_path

    @classmethod
    def load_model(
        cls,
        file_path: Optional[Path] = None
    ) -> "AstronautAnomalyDetector":
        """Load a previously saved detector."""

        if file_path is None:
            file_path = DEFAULT_MODEL_PATH

        file_path = Path(file_path)

        if not file_path.exists():
            return cls()

        payload = joblib.load(str(file_path))

        instance = cls(
            contamination=payload.get("contamination", 0.05),
            random_state=payload.get("random_state", 42),
            n_estimators=payload.get("n_estimators", 100)
        )

        instance.feature_names = payload.get("feature_names", list(VITAL_FEATURES))
        instance.imputer = payload["imputer"]
        instance.scaler = payload["scaler"]
        instance.model = payload["model"]
        instance.is_trained = payload.get("is_trained", False)
        instance.baseline_stats = payload.get("baseline_stats", {})
        instance.training_sample_count = payload.get("training_sample_count", 0)
        instance.training_source = payload.get("training_source", "UNKNOWN")

        return instance
