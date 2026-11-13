"""Unit tests for SPACECARE Phase 4 ML anomaly detection."""

import tempfile
import unittest
from pathlib import Path

import numpy as np

from src.ml.anomaly_detector import AstronautAnomalyDetector
from src.ml.feature_engineering import extract_feature_matrix, extract_feature_vector
from src.ml.model import AstronautAnomalyDetector as CompatibilityDetector
from src.ml.service import analyze_astronaut, evaluate_detector
from src.simulation.vitals_generator import generate_vitals_series


TEST_ASTRONAUT = {
    "id": 999,
    "baseline_hr": 70.0,
    "baseline_spo2": 98.0,
    "baseline_bp_sys": 118.0,
    "baseline_bp_dia": 76.0,
    "baseline_temp": 36.8,
    "baseline_rr": 14.0,
    "baseline_hrv": 55.0,
}


class TestPhase4ML(unittest.TestCase):
    def setUp(self):
        np.random.seed(42)
        self.nominal = generate_vitals_series(
            TEST_ASTRONAUT, count=80, anomaly_mode="NOMINAL"
        )
        self.hypoxia = generate_vitals_series(
            TEST_ASTRONAUT, count=20, anomaly_mode="HYPOXIA"
        )
        for row in self.nominal:
            row["anomaly_flag"] = 0
        for row in self.hypoxia:
            row["anomaly_flag"] = 1

    def test_feature_extraction_returns_seven_features(self):
        self.assertEqual(extract_feature_vector(self.nominal[0]).shape, (7,))
        self.assertEqual(extract_feature_matrix(self.nominal[:5]).shape, (5, 7))

    def test_missing_values_are_preserved_for_imputation(self):
        reading = dict(self.nominal[0])
        reading["spo2"] = None
        vector = extract_feature_vector(reading)
        self.assertTrue(np.isnan(vector[3]))

    def test_model_trains_and_returns_prediction_fields(self):
        detector = AstronautAnomalyDetector(random_state=42)
        self.assertTrue(detector.train(self.nominal))
        result = detector.predict(self.hypoxia[0])
        self.assertIn(result["is_anomaly"], (0, 1))
        self.assertIn(result["status"], ("NOMINAL", "SUSPICIOUS", "ANOMALOUS"))
        self.assertIn("normalized_severity", result)
        self.assertEqual(len(result["feature_contributions"]), 7)

    def test_training_rejects_insufficient_data(self):
        detector = AstronautAnomalyDetector()
        self.assertFalse(detector.train(self.nominal[:5]))

    def test_model_save_and_load(self):
        detector = AstronautAnomalyDetector(random_state=42)
        self.assertTrue(detector.train(self.nominal))
        with tempfile.TemporaryDirectory() as temp_dir:
            model_path = Path(temp_dir) / "astronaut_model.joblib"
            detector.save_model(model_path)
            loaded = AstronautAnomalyDetector.load_model(model_path)
            self.assertTrue(loaded.is_trained)
            self.assertEqual(loaded.training_sample_count, len(self.nominal))
            self.assertEqual(
                detector.predict(self.hypoxia[0])["is_anomaly"],
                loaded.predict(self.hypoxia[0])["is_anomaly"],
            )

    def test_compatibility_import_points_to_same_class(self):
        self.assertIs(CompatibilityDetector, AstronautAnomalyDetector)

    def test_evaluation_uses_nominal_and_labeled_anomaly_rows(self):
        result = evaluate_detector(self.nominal + self.hypoxia, random_state=42)
        self.assertIsNotNone(result)
        self.assertEqual(result["training_samples"], 56)
        self.assertEqual(result["test_samples"], 44)
        self.assertEqual(result["test_anomalies"], 20)
        for metric in ("precision", "recall", "f1_score"):
            self.assertGreaterEqual(result[metric], 0.0)
            self.assertLessEqual(result[metric], 1.0)

    def test_astronaut_analysis_trains_and_predicts_latest_reading(self):
        history = self.nominal[:30] + self.hypoxia[:5]
        result = analyze_astronaut(TEST_ASTRONAUT, history=history)
        self.assertTrue(result["detector"].is_trained)
        self.assertEqual(result["training_samples"], 30)
        self.assertEqual(result["latest_reading"], history[-1])
        self.assertEqual(result["latest_source"], "SQLite telemetry")
        self.assertIn("status", result["prediction"])


if __name__ == "__main__":
    unittest.main()
