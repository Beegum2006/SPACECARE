
import unittest
import tempfile
from pathlib import Path

from src.mental_health.sleep_tracker import (
    simulate_sleep_profile,
    generate_sleep_history
)
from src.mental_health.tlx_assessment import (
    calculate_raw_tlx,
    calculate_fatigue_risk_index
)
from src.ml.anomaly_detector import AstronautAnomalyDetector


class TestSpacecarePhase4(unittest.TestCase):

    def test_sleep_profile_values(self):
        """Sleep simulation should produce valid values."""
        sleep = simulate_sleep_profile(1)

        self.assertEqual(sleep["is_simulated"], 1)
        self.assertGreaterEqual(sleep["sleep_duration_hours"], 4.5)
        self.assertLessEqual(sleep["sleep_duration_hours"], 9.5)
        self.assertGreaterEqual(sleep["sleep_efficiency_pct"], 60)
        self.assertLessEqual(sleep["sleep_efficiency_pct"], 98)

    def test_sleep_history_generation(self):
        """Sleep history should contain the requested number of days."""
        history = generate_sleep_history(1, days=14)

        self.assertEqual(len(history), 14)
        self.assertEqual(history[0]["astronaut_id"], 1)
        self.assertEqual(history[-1]["astronaut_id"], 1)

    def test_sleep_stages_sum_to_100(self):
        """REM, deep and light sleep percentages should total 100."""
        sleep = simulate_sleep_profile(1)

        total = (
            sleep["rem_percentage"]
            + sleep["deep_sleep_percentage"]
            + sleep["light_sleep_percentage"]
        )

        self.assertAlmostEqual(total, 100.0, places=1)

    def test_raw_tlx_calculation(self):
        """Raw NASA-TLX should calculate the mean of six dimensions."""
        score = calculate_raw_tlx(45, 35, 40, 20, 50, 15)

        self.assertAlmostEqual(score, 34.17, places=2)

    def test_fatigue_risk_low(self):
        """Normal sleep and workload should produce low risk."""
        risk, category = calculate_fatigue_risk_index(
            tlx_score=20,
            sleep_duration_hours=8,
            sleep_efficiency_pct=95,
            circadian_drift_hours=0.2
        )

        self.assertGreaterEqual(risk, 0)
        self.assertLess(risk, 35)
        self.assertEqual(category, "LOW_RISK")

    def test_fatigue_risk_high(self):
        """Severe sleep deficit and workload should produce high risk."""
        risk, category = calculate_fatigue_risk_index(
            tlx_score=80,
            sleep_duration_hours=3,
            sleep_efficiency_pct=50,
            circadian_drift_hours=4
        )

        self.assertGreaterEqual(risk, 65)
        self.assertLessEqual(risk, 100)
        self.assertEqual(category, "HIGH_RISK")

    def test_fatigue_risk_is_bounded(self):
        """Fatigue Risk Index should remain between 0 and 100."""
        risk, category = calculate_fatigue_risk_index(
            tlx_score=100,
            sleep_duration_hours=1,
            sleep_efficiency_pct=0,
            circadian_drift_hours=10
        )

        self.assertGreaterEqual(risk, 0)
        self.assertLessEqual(risk, 100)

    def test_ml_detector_starts_untrained(self):
        """New anomaly detector should not claim to be trained."""
        detector = AstronautAnomalyDetector()

        self.assertFalse(detector.is_trained)
        self.assertEqual(
            detector.training_source,
            "NOT_TRAINED"
        )


if __name__ == "__main__":
    unittest.main()
