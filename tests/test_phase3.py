"""
Unit and Integration Tests for SPACECARE Phase 3
Verifies authentic NASA OSDR, RadLab, and EDA client integrations,
metadata schema validation, offline resilience, and database persistence.
"""

import unittest
from src.database.db import init_database, get_db_connection
from src.nasa_data.osdr_client import (
    get_curated_human_studies, search_studies, fetch_live_study_metadata
)
from src.nasa_data.radiation_service import (
    load_local_radlab_records, fetch_radlab_telemetry,
    calculate_radiation_summary, sync_radlab_records_to_db, NASA_RADIATION_STANDARDS
)
from src.nasa_data.eda_client import (
    load_eda_benchmarks, get_eda_statistical_summary, compare_reading_against_eda
)


class TestSpacecarePhase3(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_database()

    # ========================================================================
    # NASA OSDR Client Tests
    # ========================================================================
    def test_osdr_curated_studies_loaded(self):
        """Verify that authentic NASA human spaceflight studies are correctly loaded."""
        studies = get_curated_human_studies()
        self.assertGreaterEqual(len(studies), 5)

        study_ids = [s["study_id"] for s in studies]
        self.assertIn("OSD-140", study_ids)
        self.assertIn("OSD-316", study_ids)
        self.assertIn("OSD-174", study_ids)
        self.assertIn("OSD-816", study_ids)
        self.assertIn("OSD-943", study_ids)

        for s in studies:
            self.assertEqual(s["organism"], "Homo sapiens")
            self.assertEqual(s["verification_status"], "VERIFIED")
            self.assertIn("NASA", s["provenance"])
            self.assertGreater(len(s.get("key_findings", [])), 0)

    def test_osdr_search_and_filters(self):
        """Verify keyword and tissue filtering across NASA OSDR studies."""
        # Keyword search
        sans_studies = search_studies(query="SANS")
        self.assertGreaterEqual(len(sans_studies), 1)
        self.assertEqual(sans_studies[0]["study_id"], "OSD-816")

        mars_studies = search_studies(query="Mars500")
        self.assertGreaterEqual(len(mars_studies), 1)
        self.assertEqual(mars_studies[0]["study_id"], "OSD-140")

        # Tissue filter
        hair_studies = search_studies(tissue_filter="Hair")
        self.assertGreaterEqual(len(hair_studies), 1)
        self.assertEqual(hair_studies[0]["study_id"], "OSD-174")

    def test_osdr_fallback_metadata_lookup(self):
        """Verify metadata lookup resolves for known studies."""
        meta = fetch_live_study_metadata("OSD-140", timeout_sec=2)
        self.assertIsNotNone(meta)
        self.assertEqual(meta["study_id"], "OSD-140")

    # ========================================================================
    # NASA RadLab Radiation Tests
    # ========================================================================
    def test_radlab_records_loaded(self):
        """Verify RadLab radiation records and parameters."""
        records, _ = fetch_radlab_telemetry(spacecraft="ISS", limit=10, timeout_sec=2)
        self.assertGreaterEqual(len(records), 5)

        for r in records:
            self.assertEqual(r["spacecraft"], "ISS")
            self.assertGreater(r["absorbed_dose_rate_ugy_h"], 5.0)
            self.assertGreater(r["dose_equivalent_rate_usv_h"], 10.0)
            self.assertGreater(r["flux_cm2_sr_s"], 0.5)

    def test_radiation_summary_and_limits(self):
        """Verify dosimetry statistics and NASA-STD-3001 exposure limit evaluation."""
        records, _ = fetch_radlab_telemetry(spacecraft="ISS", limit=10, timeout_sec=2)
        summary = calculate_radiation_summary(records, mission_days=42)

        self.assertGreater(summary["avg_dose_rate_usv_h"], 10.0)
        self.assertGreater(summary["peak_dose_rate_usv_h"], 30.0)  # SAA peak
        self.assertGreater(summary["estimated_cumulative_msv"], 0.0)
        self.assertLess(summary["estimated_cumulative_msv"], NASA_RADIATION_STANDARDS["career_effective_dose_limit_msv"])
        self.assertIn(summary["status"], ["NOMINAL", "ELEVATED_SAA", "WARNING", "CRITICAL"])
        self.assertIn("NASA-STD-3001", summary["citation"])

    def test_radlab_database_persistence(self):
        """Verify provenance preservation during database insertion."""
        # 1. Local reference fixture should be saved with is_simulated = 1
        fixture_records = load_local_radlab_records()[:3]
        inserted = sync_radlab_records_to_db(fixture_records)
        self.assertEqual(inserted, 3)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM radiation_logs WHERE is_simulated = 1;")
        fixture_rows = cursor.fetchall()
        self.assertGreaterEqual(len(fixture_rows), 3)

        # 2. Simulated live API record with is_real_nasa_data = True should get is_simulated = 0
        live_record = [{
            "timestamp": "2024-04-12T12:00:00Z",
            "instrument": "Liulin-5 (Live API)",
            "module": "US Lab",
            "dose_equivalent_rate_usv_h": 22.0,
            "is_real_nasa_data": True,
            "provenance": "NASA RadLab Data API (Verified Live Response)"
        }]
        sync_radlab_records_to_db(live_record)

        cursor.execute("SELECT * FROM radiation_logs WHERE is_simulated = 0;")
        live_rows = cursor.fetchall()
        conn.close()

        self.assertGreaterEqual(len(live_rows), 1)

    # ========================================================================
    # NASA EDA Environmental Tests
    # ========================================================================
    def test_eda_benchmarks_loading(self):
        """Verify NASA EDA reference baseline environmental logs load properly."""
        df = load_eda_benchmarks()
        self.assertFalse(df.empty)
        self.assertIn("cabin_pressure_psi", df.columns)
        self.assertIn("co2_partial_pressure_mmhg", df.columns)
        self.assertIn("o2_percentage", df.columns)
        self.assertIn("temperature_celsius", df.columns)
        self.assertIn("relative_humidity_pct", df.columns)

    def test_eda_statistical_summary(self):
        """Verify computed reference distributions align with ISS physical baselines."""
        stats = get_eda_statistical_summary()
        self.assertIn("cabin_pressure_psi", stats)
        self.assertAlmostEqual(stats["cabin_pressure_psi"]["mean"], 14.7, delta=0.2)
        self.assertAlmostEqual(stats["co2_partial_pressure_mmhg"]["mean"], 2.8, delta=0.5)
        self.assertAlmostEqual(stats["temperature_celsius"]["mean"], 22.3, delta=1.5)

    def test_eda_comparison_with_nominal_reading(self):
        """Verify that nominal simulated reading correctly aligns with reference baseline."""
        nominal_reading = {
            "cabin_pressure_psi": 14.70,
            "co2_partial_pressure_mmhg": 2.80,
            "o2_percentage": 21.05,
            "temperature_celsius": 22.20,
            "relative_humidity_pct": 46.50
        }
        res = compare_reading_against_eda(nominal_reading)
        self.assertTrue(res["is_aligned_with_nasa_baseline"])


if __name__ == "__main__":
    unittest.main()
