"""
Unit and Integration Tests for SPACECARE Phase 1
Verifies SQLite schema creation, crew roster seeding, queries, and configurable crew actions using unittest.
"""

import unittest
from pathlib import Path
from src.database.db import init_database, DB_PATH
from src.database.queries import (
    get_astronauts, get_astronaut_by_id, add_astronaut, update_astronaut, delete_astronaut,
    get_active_alerts, create_alert, acknowledge_alert,
    log_vitals, get_latest_vitals,
    log_environment, get_latest_environment
)


class TestSpacecarePhase1(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Ensure database schema is initialized before tests."""
        init_database()

    def test_db_file_exists(self):
        """Check that spacecare.db is successfully created."""
        self.assertTrue(DB_PATH.exists(), f"Database file not found at {DB_PATH}")

    def test_initial_crew_seeded(self):
        """Verify default 4-member ISS crew is seeded."""
        crew = get_astronauts()
        self.assertGreaterEqual(len(crew), 4, f"Expected at least 4 astronauts, found {len(crew)}")
        names = [a["name"] for a in crew]
        self.assertIn("Dr. Elena Vance", names)
        self.assertIn("Marcus 'Orion' Cole", names)
        self.assertIn("Dr. Aisha Patel", names)
        self.assertIn("Kaito 'Nova' Tanaka", names)

    def test_crew_is_configurable_add_update_delete(self):
        """Verify that crew size is dynamically configurable."""
        # 1. Add new astronaut
        new_id = add_astronaut(
            name="Test Commander Shepard",
            callsign="Normandy",
            role="Special Commander",
            agency="NASA",
            baseline_hr=62.0,
            baseline_spo2=99.0
        )
        self.assertGreater(new_id, 0)

        ast = get_astronaut_by_id(new_id)
        self.assertIsNotNone(ast)
        self.assertEqual(ast["name"], "Test Commander Shepard")
        self.assertEqual(ast["baseline_hr"], 62.0)

        # 2. Update astronaut
        updated = update_astronaut(new_id, baseline_hr=65.0, status="EVALUATING")
        self.assertTrue(updated)
        ast_updated = get_astronaut_by_id(new_id)
        self.assertEqual(ast_updated["baseline_hr"], 65.0)
        self.assertEqual(ast_updated["status"], "EVALUATING")

        # 3. Delete astronaut
        deleted = delete_astronaut(new_id)
        self.assertTrue(deleted)
        self.assertIsNone(get_astronaut_by_id(new_id))

    def test_vitals_logging_and_retrieval(self):
        """Verify vitals logging and latest entry retrieval."""
        crew = get_astronauts()
        ast_id = crew[0]["id"]

        log_id = log_vitals(
            astronaut_id=ast_id,
            heart_rate=73.5,
            blood_pressure_sys=119.0,
            blood_pressure_dia=77.0,
            spo2=98.7,
            core_temperature=36.8,
            respiration_rate=14.2,
            hrv_rmssd=54.0,
            is_simulated=1
        )
        self.assertGreater(log_id, 0)

        latest = get_latest_vitals(ast_id)
        self.assertIsNotNone(latest)
        self.assertEqual(latest["heart_rate"], 73.5)
        self.assertEqual(latest["spo2"], 98.7)
        self.assertEqual(latest["is_simulated"], 1)

    def test_environmental_logging(self):
        """Verify ISS ECLSS environmental logging."""
        env_id = log_environment(
            cabin_pressure_psi=14.7,
            co2_partial_pressure_mmhg=2.9,
            o2_percentage=21.2,
            temperature_celsius=22.3,
            relative_humidity_pct=48.5,
            is_simulated=1
        )
        self.assertGreater(env_id, 0)

        latest_env = get_latest_environment()
        self.assertIsNotNone(latest_env)
        self.assertEqual(latest_env["cabin_pressure_psi"], 14.7)
        self.assertEqual(latest_env["is_simulated"], 1)

    def test_alerts_lifecycle(self):
        """Verify creating and acknowledging an alert."""
        crew = get_astronauts()
        ast_id = crew[0]["id"]

        alert_id = create_alert(
            severity="WARNING",
            category="VITALS",
            title="Elevated Heart Rate",
            message="HR exceeded 110 bpm during rest",
            flight_surgeon_protocol="Initiate crew rest protocol and verify hydration",
            astronaut_id=ast_id,
            metric_name="heart_rate",
            metric_value=114.0,
            threshold_limit=100.0
        )
        self.assertGreater(alert_id, 0)

        active_alerts = get_active_alerts()
        alert_ids = [a["id"] for a in active_alerts]
        self.assertIn(alert_id, alert_ids)

        # Acknowledge
        ack = acknowledge_alert(alert_id)
        self.assertTrue(ack)

        # Confirm it is no longer in active alerts
        active_after = get_active_alerts()
        active_after_ids = [a["id"] for a in active_after]
        self.assertNotIn(alert_id, active_after_ids)


if __name__ == "__main__":
    unittest.main()
