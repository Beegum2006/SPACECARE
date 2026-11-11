"""
Unit and Integration Tests for SPACECARE Phase 2
Verifies Vital Signs simulation, ISS Environmental (ECLSS) simulation,
anomaly triggers, and SQLite persistence.
"""

import unittest
from datetime import datetime
from src.database.db import init_database
from src.database.queries import (
    get_astronauts, log_vitals, get_vitals_history,
    log_environment, get_environment_history
)
from src.simulation.vitals_generator import (
    generate_vitals_snapshot, generate_vitals_series, generate_synthetic_ecg_trace, ANOMALY_MODES
)
from src.simulation.iss_env_generator import (
    generate_env_snapshot, generate_env_series, ENV_ANOMALY_MODES, ISS_MODULES
)


class TestSpacecarePhase2(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_database()
        cls.crew = get_astronauts()
        assert len(cls.crew) > 0, "Crew roster must not be empty"
        cls.astro = cls.crew[0]

    def test_nominal_vitals_generation(self):
        """Test nominal vital signs generation stays within expected resting ranges."""
        v = generate_vitals_snapshot(self.astro, anomaly_mode="NOMINAL")
        self.assertIn("heart_rate", v)
        self.assertIn("spo2", v)
        self.assertIn("blood_pressure_sys", v)
        self.assertIn("blood_pressure_dia", v)
        self.assertIn("core_temperature", v)
        self.assertIn("respiration_rate", v)
        self.assertIn("hrv_rmssd", v)
        self.assertEqual(v["is_simulated"], 1)
        self.assertEqual(v["anomaly_flag"], 0)
        self.assertGreaterEqual(v["spo2"], 95.0)
        self.assertLessEqual(v["heart_rate"], 105.0)

    def test_hypoxia_anomaly(self):
        """Test that Hypoxia anomaly correctly induces SpO2 drop and compensatory hyperventilation."""
        v = generate_vitals_snapshot(self.astro, anomaly_mode="HYPOXIA")
        self.assertLess(v["spo2"], 90.0)
        self.assertGreater(v["respiration_rate"], 18.0)
        self.assertEqual(v["anomaly_flag"], 1)

    def test_tachycardia_anomaly(self):
        """Test that Tachycardia/Arrhythmia induces rapid heart rate and depressed HRV."""
        v = generate_vitals_snapshot(self.astro, anomaly_mode="TACHYCARDIA_ARRHYTHMIA")
        self.assertGreater(v["heart_rate"], 120.0)
        self.assertLess(v["hrv_rmssd"], 30.0)
        self.assertEqual(v["anomaly_flag"], 1)

    def test_heat_stress_anomaly(self):
        """Test that Heat Stress induces elevated core body temperature."""
        v = generate_vitals_snapshot(self.astro, anomaly_mode="HEAT_STRESS")
        self.assertGreater(v["core_temperature"], 38.2)
        self.assertEqual(v["anomaly_flag"], 1)

    def test_vitals_series_generation(self):
        """Verify generation of chronological vitals time series."""
        count = 15
        series = generate_vitals_series(self.astro, count=count, interval_seconds=5, anomaly_mode="NOMINAL")
        self.assertEqual(len(series), count)
        # Verify chronological order
        t0 = datetime.strptime(series[0]["timestamp"], "%Y-%m-%d %H:%M:%S")
        t_last = datetime.strptime(series[-1]["timestamp"], "%Y-%m-%d %H:%M:%S")
        self.assertLess(t0, t_last)

    def test_synthetic_ecg_trace(self):
        """Verify synthetic P-Q-R-S-T ECG waveform output."""
        t, v = generate_synthetic_ecg_trace(heart_rate_bpm=72.0, duration_sec=3.0, sampling_rate=100)
        self.assertEqual(len(t), 300)
        self.assertEqual(len(v), 300)
        # Verify R wave spike reaches at least 0.8 mV
        self.assertGreater(v.max(), 0.8)
        # Verify Q/S wave dip is negative
        self.assertLess(v.min(), -0.1)

    def test_iss_environment_nominal(self):
        """Verify nominal ISS cabin life support parameters."""
        env = generate_env_snapshot(module_name="Destiny Laboratory (US Lab)", anomaly_mode="NOMINAL")
        self.assertAlmostEqual(env["cabin_pressure_psi"], 14.7, delta=0.5)
        self.assertAlmostEqual(env["co2_partial_pressure_mmhg"], 2.8, delta=0.8)
        self.assertAlmostEqual(env["o2_percentage"], 21.0, delta=0.8)
        self.assertEqual(env["is_simulated"], 1)
        self.assertEqual(env["status"], "NOMINAL")

    def test_iss_cdra_scrubber_anomaly(self):
        """Verify CDRA scrubber failure elevates CO2 partial pressure."""
        env = generate_env_snapshot(module_name="Destiny Laboratory (US Lab)", anomaly_mode="CDRA_SCRUBBER_MALFUNCTION")
        self.assertGreater(env["co2_partial_pressure_mmhg"], 4.0)
        self.assertEqual(env["status"], "ECLSS_WARNING")

    def test_iss_depressurization_anomaly(self):
        """Verify cabin depressurization drops pressure below nominal."""
        env = generate_env_snapshot(module_name="Destiny Laboratory (US Lab)", anomaly_mode="CABIN_DEPRESSURIZATION")
        self.assertLess(env["cabin_pressure_psi"], 13.8)
        self.assertEqual(env["status"], "DECOMPRESSION_CRITICAL")

    def test_database_logging_and_retrieval(self):
        """Verify simulated telemetry is properly saved to SQLite and retrieved."""
        v = generate_vitals_snapshot(self.astro, anomaly_mode="NOMINAL")
        vid = log_vitals(
            astronaut_id=self.astro["id"],
            heart_rate=v["heart_rate"],
            blood_pressure_sys=v["blood_pressure_sys"],
            blood_pressure_dia=v["blood_pressure_dia"],
            spo2=v["spo2"],
            core_temperature=v["core_temperature"],
            respiration_rate=v["respiration_rate"],
            hrv_rmssd=v["hrv_rmssd"],
            is_simulated=1
        )
        self.assertGreater(vid, 0)
        history = get_vitals_history(self.astro["id"], limit=5)
        self.assertGreaterEqual(len(history), 1)
        self.assertEqual(history[-1]["is_simulated"], 1)

        # Environmental log test
        e = generate_env_snapshot(anomaly_mode="NOMINAL")
        eid = log_environment(
            cabin_pressure_psi=e["cabin_pressure_psi"],
            co2_partial_pressure_mmhg=e["co2_partial_pressure_mmhg"],
            o2_percentage=e["o2_percentage"],
            temperature_celsius=e["temperature_celsius"],
            relative_humidity_pct=e["relative_humidity_pct"],
            is_simulated=1
        )
        self.assertGreater(eid, 0)
        env_hist = get_environment_history(limit=5)
        self.assertGreaterEqual(len(env_hist), 1)
        self.assertEqual(env_hist[-1]["is_simulated"], 1)


if __name__ == "__main__":
    unittest.main()
