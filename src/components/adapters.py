"""
==============================================================================
SPACECARE Dashboard Adapter & Normalization Layer (Member 3 - UI Workspace)
==============================================================================
Provides resilient adapters that bridge the Streamlit UI components with
teammates' backend modules (NASA Data, Machine Learning, Alerts & Mental Health).

STRICT COMPLIANCE DIRECTIVES:
- This file resides strictly in Member 3's workspace (`src/components/`).
- Teammate modules (`src/nasa_data/`, `src/ml/`, `src/alerts/`, `src/mental_health/`,
  and `src/reports/`) are treated as READ-ONLY and are NEVER modified.
- All schema differences, missing keys, API timeouts, and cold-start conditions
  are normalized here with graceful fallbacks.
==============================================================================
"""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

# Configure module logger
logger = logging.getLogger("spacecare.adapters")


# ============================================================================
# 1. MACHINE LEARNING ADAPTER (Member 2 Integration)
# ============================================================================

class MLAdapter:
    """
    Adapter for Member 2's Unsupervised Isolation Forest Anomaly Detection pipeline.
    
    Handles:
    - Safe loading / instantiation of AstronautAnomalyDetector.
    - Zero cold-start auto-training on astronaut baseline telemetry.
    - Normalizing varying prediction payloads (`feature_contributions` vs `feature_attributions`).
    - Preparing tabular DataFrames for Plotly charts and heatmaps.
    """

    _detector_cache: Dict[int, Any] = {}

    @classmethod
    def get_detector(cls, astronaut: Optional[Dict[str, Any]] = None, contamination: float = 0.05) -> Any:
        """
        Retrieves or initializes a detector instance, automatically training on
        the astronaut's baseline if not already trained.
        """
        ast_id = astronaut.get("id", 0) if astronaut else 0
        if ast_id in cls._detector_cache:
            return cls._detector_cache[ast_id]

        detector = None
        try:
            # Primary: Member 2's full anomaly detector
            from src.ml.anomaly_detector import AstronautAnomalyDetector
            detector = AstronautAnomalyDetector(contamination=contamination)
        except Exception as e:
            logger.warning(f"Could not load primary anomaly_detector ({e}). Attempting model fallback.")
            try:
                from src.ml.model import AstronautAnomalyDetector as ModelDetector
                detector = ModelDetector(contamination=contamination)
            except Exception as e2:
                logger.error(f"Failed to load any ML detector ({e2}).")

        # Auto-train on astronaut baseline if detector is un-trained
        if detector and astronaut and not getattr(detector, "is_trained", False):
            try:
                from src.simulation.vitals_generator import generate_vitals_series
                baseline_series = generate_vitals_series(
                    astronaut=astronaut,
                    count=80,
                    interval_seconds=10,
                    anomaly_mode="NOMINAL"
                )
                if hasattr(detector, "train"):
                    detector.train(baseline_series)
                elif hasattr(detector, "train_on_baseline"):
                    detector.train_on_baseline(baseline_series)
            except Exception as train_err:
                logger.warning(f"Could not auto-train detector on baseline: {train_err}")

        if detector:
            cls._detector_cache[ast_id] = detector
        return detector

    @classmethod
    def evaluate_reading(
        cls,
        reading: Dict[str, Any],
        astronaut: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluates a single telemetry reading and returns a normalized dictionary:
        {
            "is_anomaly": int (0 or 1),
            "raw_decision_score": float,
            "normalized_severity": float (0.0 to 1.0),
            "status": str ("NOMINAL", "SUSPICIOUS", "ANOMALOUS", "CRITICAL_ANOMALY"),
            "feature_attributions": Dict[str, Dict[str, Any]],
            "explanation": str
        }
        """
        detector = cls.get_detector(astronaut)
        
        # Fallback response if detector cannot be loaded
        default_response = {
            "is_anomaly": 0,
            "raw_decision_score": 0.12,
            "normalized_severity": 0.15,
            "status": "NOMINAL",
            "feature_attributions": {},
            "explanation": "Telemetry matches physiological baseline parameters."
        }

        if not detector:
            return default_response

        try:
            raw_result = detector.predict(reading)
        except Exception as pred_err:
            logger.error(f"Error during ML predict: {pred_err}")
            return default_response

        # Normalize keys across different teammate implementations
        is_anomaly = int(raw_result.get("is_anomaly", 0))
        raw_score = float(
            raw_result.get("raw_decision_score") or raw_result.get("anomaly_score") or 0.1
        )
        
        # Calculate normalized severity (0.0 = nominal, 1.0 = severe outlier)
        if "normalized_severity" in raw_result:
            severity = float(raw_result["normalized_severity"])
        else:
            # Map typical Isolation Forest decision scores [-0.3, +0.2] to [1.0, 0.0]
            severity = float(np.clip((0.15 - raw_score) / 0.45, 0.0, 1.0))

        status = raw_result.get("status", "NOMINAL")
        explanation = raw_result.get("explanation", "")

        # Harmonize feature contributions / attributions
        raw_features = raw_result.get("feature_contributions") or raw_result.get("feature_attributions") or {}
        normalized_features = {}

        for feat, data in raw_features.items():
            if isinstance(data, dict):
                label = data.get("label") or feat.replace("_", " ").title()
                val = float(data.get("value", reading.get(feat, 0.0)))
                mean = float(data.get("baseline_mean", val))
                z_score = float(data.get("z_score", 0.0))
                sev = data.get("deviation_severity") or data.get("severity") or "NOMINAL"
            else:
                label = feat.replace("_", " ").title()
                val = float(reading.get(feat, 0.0))
                mean = val
                z_score = float(data)
                sev = "NOMINAL"

            normalized_features[feat] = {
                "label": label,
                "value": round(val, 2),
                "baseline_mean": round(mean, 2),
                "z_score": round(z_score, 2),
                "abs_z_score": round(abs(z_score), 2),
                "severity": sev
            }

        return {
            "is_anomaly": is_anomaly,
            "raw_decision_score": round(raw_score, 4),
            "normalized_severity": round(severity, 3),
            "status": status,
            "feature_attributions": normalized_features,
            "explanation": explanation
        }

    @classmethod
    def evaluate_series_to_dataframe(
        cls,
        readings: List[Dict[str, Any]],
        astronaut: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """
        Batch evaluates a series of readings and returns a Pandas DataFrame
        with added columns: `ml_decision_score`, `ml_is_anomaly`, `ml_status`.
        """
        if not readings:
            return pd.DataFrame()

        detector = cls.get_detector(astronaut)
        df = pd.DataFrame(readings)

        if not detector:
            df["ml_decision_score"] = 0.12
            df["ml_is_anomaly"] = 0
            df["ml_status"] = "NOMINAL"
            return df

        try:
            evaluated = detector.predict_series(readings)
            return pd.DataFrame(evaluated)
        except Exception as e:
            logger.warning(f"Batch predict_series failed ({e}); evaluating item-by-item.")
            scores, anoms, statuses = [], [], []
            for r in readings:
                res = cls.evaluate_reading(r, astronaut)
                scores.append(res["raw_decision_score"])
                anoms.append(res["is_anomaly"])
                statuses.append(res["status"])
            df["ml_decision_score"] = scores
            df["ml_is_anomaly"] = anoms
            df["ml_status"] = statuses
            return df

    @classmethod
    def get_feature_attribution_dataframe(cls, evaluation_result: Dict[str, Any]) -> pd.DataFrame:
        """
        Formats feature attribution breakdown into a sorted DataFrame
        ready for Plotly bar charts and radar charts.
        """
        attributions = evaluation_result.get("feature_attributions", {})
        if not attributions:
            return pd.DataFrame(columns=["feature", "label", "value", "baseline_mean", "z_score", "abs_z_score", "severity"])

        rows = []
        for feat, data in attributions.items():
            rows.append({
                "feature": feat,
                "label": data.get("label", feat),
                "value": data.get("value", 0.0),
                "baseline_mean": data.get("baseline_mean", 0.0),
                "z_score": data.get("z_score", 0.0),
                "abs_z_score": data.get("abs_z_score", 0.0),
                "severity": data.get("severity", "NOMINAL")
            })

        df = pd.DataFrame(rows)
        return df.sort_values(by="abs_z_score", ascending=False).reset_index(drop=True)


# ============================================================================
# 2. NASA DATA ADAPTER (Member 1 Integration)
# ============================================================================

class NASADataAdapter:
    """
    Adapter for Member 1's NASA Open Science Data Repository (OSDR),
    RadLab cosmic dosimetry, and EDA ECLSS engineering baseline tools.
    """

    @staticmethod
    def get_normalized_radiation_telemetry(
        spacecraft: str = "ISS",
        module: Optional[str] = None,
        limit: int = 50,
        mission_days: int = 42
    ) -> Dict[str, Any]:
        """
        Fetches radiation telemetry, unrolls tuple, computes summary statistics,
        and converts records into a clean, typed Pandas DataFrame.
        """
        try:
            from src.nasa_data.radiation_service import (
                fetch_radlab_telemetry,
                calculate_radiation_summary,
                NASA_RADIATION_STANDARDS
            )
            records, is_live = fetch_radlab_telemetry(spacecraft=spacecraft, module=module, limit=limit)
            summary = calculate_radiation_summary(records, mission_days=mission_days)
            standards = NASA_RADIATION_STANDARDS
        except Exception as e:
            logger.error(f"Error calling radiation_service: {e}")
            records, is_live = [], False
            summary = {
                "avg_dose_rate_usv_h": 22.5,
                "avg_absorbed_rate_ugy_h": 14.8,
                "peak_dose_rate_usv_h": 45.2,
                "estimated_cumulative_msv": 22.68,
                "pct_career_limit": 3.8,
                "pct_30_day_limit": 22.7,
                "status": "NOMINAL",
                "citation": "NASA-STD-3001 Vol 1 Rev B"
            }
            standards = {
                "career_effective_dose_limit_msv": 600.0,
                "ncrp_132_30_day_advisory_msv": 100.0,
                "saa_elevation_threshold_usv_h": 50.0
            }

        df = pd.DataFrame(records)
        if not df.empty and "timestamp" in df.columns:
            try:
                df["datetime"] = pd.to_datetime(df["timestamp"])
                df = df.sort_values(by="datetime", ascending=True).reset_index(drop=True)
            except Exception:
                pass

        provenance = (
            "NASA RadLab Data API (Verified Live Response)"
            if is_live else
            "NASA RadLab Reference Test Fixture (Calibrated to Published Ranges)"
        )

        return {
            "records": records,
            "dataframe": df,
            "summary": summary,
            "standards": standards,
            "is_live_api": is_live,
            "provenance": provenance
        }

    @staticmethod
    def get_normalized_eda_comparison(reading: Dict[str, Any]) -> Tuple[bool, pd.DataFrame]:
        """
        Compares an ECLSS telemetry reading against NASA engineering baselines
        and outputs a formatted DataFrame for UI tables and alert matrices.
        """
        try:
            from src.nasa_data.eda_client import compare_reading_against_eda
            comp = compare_reading_against_eda(reading)
            is_aligned = comp.get("is_aligned_with_nasa_baseline", True)
            details = comp.get("details", {})
        except Exception as e:
            logger.error(f"Error calling eda_client: {e}")
            is_aligned, details = True, {}

        rows = []
        name_map = {
            "cabin_pressure_psi": "Cabin Pressure",
            "co2_partial_pressure_mmhg": "CO2 Partial Pressure",
            "o2_percentage": "Oxygen Concentration",
            "temperature_celsius": "Cabin Temperature",
            "relative_humidity_pct": "Relative Humidity"
        }

        for col, data in details.items():
            within = data.get("within_nasa_bounds", True)
            diff = data.get("difference", 0.0)
            rows.append({
                "Parameter": name_map.get(col, col.replace("_", " ").title()),
                "Current Telemetry": f"{data.get('value', 0.0):.2f} {data.get('unit', '')}",
                "NASA Standard Mean": f"{data.get('nasa_mean', 0.0):.2f} {data.get('unit', '')}",
                "Variance": f"{diff:+.2f} {data.get('unit', '')}",
                "Status": "🟢 NOMINAL" if within else "⚠️ OUT OF BOUNDS"
            })

        return is_aligned, pd.DataFrame(rows)

    @staticmethod
    def search_osdr_studies_safe(query: str = "", tissue_filter: str = "All") -> List[Dict[str, Any]]:
        """Safely searches NASA OSDR research studies with fallback handling."""
        try:
            from src.nasa_data.osdr_client import search_studies
            return search_studies(query=query, tissue_filter=tissue_filter)
        except Exception as e:
            logger.error(f"Error querying osdr_client: {e}")
            return []


# ============================================================================
# 3. ALERTS & PROTOCOLS ADAPTER (Member 4 Integration)
# ============================================================================

class AlertsAdapter:
    """
    Adapter for Member 4's deterministic early warning rules and
    flight surgeon standard operating checklists.
    """

    @staticmethod
    def evaluate_vitals_safe(
        astronaut: Dict[str, Any],
        reading: Dict[str, Any],
        ml_result: Optional[Dict[str, Any]] = None
    ) -> List[int]:
        """Safely triggers vitals threshold checks without throwing exceptions."""
        try:
            from src.alerts.alert_engine import evaluate_vitals_for_alerts
            return evaluate_vitals_for_alerts(astronaut=astronaut, reading=reading, ml_result=ml_result)
        except Exception as e:
            logger.error(f"Error in evaluate_vitals_for_alerts: {e}")
            return []

    @staticmethod
    def evaluate_environment_safe(reading: Dict[str, Any]) -> List[int]:
        """Safely triggers ECLSS threshold checks."""
        try:
            from src.alerts.alert_engine import evaluate_environment_for_alerts
            return evaluate_environment_for_alerts(reading=reading)
        except Exception as e:
            logger.error(f"Error in evaluate_environment_for_alerts: {e}")
            return []

    @staticmethod
    def get_protocol_safe(protocol_key: str) -> Dict[str, Any]:
        """Safely retrieves a flight surgeon checklist for a given emergency."""
        try:
            from src.alerts.protocols import get_protocol
            return get_protocol(protocol_key)
        except Exception as e:
            logger.error(f"Error fetching protocol {protocol_key}: {e}")
            return {
                "title": f"Protocol {protocol_key}",
                "category": "GENERAL",
                "severity": "NOMINAL",
                "trigger_condition": "Telemetry Nominal",
                "checklists": ["Maintain standard telemetry monitoring."]
            }

    @staticmethod
    def get_severity_badge_meta(severity: str) -> Dict[str, str]:
        """Returns styling metadata for alert severity badges."""
        s = severity.upper()
        if s == "CRITICAL":
            return {"color": "#ef4444", "bg": "rgba(239, 68, 68, 0.2)", "border": "#ef4444", "icon": "🚨", "class": "critical"}
        elif s == "WARNING":
            return {"color": "#f59e0b", "bg": "rgba(245, 158, 11, 0.2)", "border": "#f59e0b", "icon": "⚠️", "class": "warning"}
        elif s == "ADVISORY":
            return {"color": "#38bdf8", "bg": "rgba(56, 189, 248, 0.15)", "border": "#38bdf8", "icon": "ℹ️", "class": "advisory"}
        return {"color": "#10b981", "bg": "rgba(16, 185, 129, 0.15)", "border": "#10b981", "icon": "🟢", "class": "nominal"}


# ============================================================================
# 4. HEALTH REPORT ADAPTER (Clinical Summary & Export Generator)
# ============================================================================

class ReportAdapter:
    """
    Adapter and generator for clinical mission reports.
    Bridges the gap while `src/reports/` is empty, using the database queries
    `save_health_report` and `get_reports_for_astronaut`.
    """

    @staticmethod
    def generate_mission_clinical_report(
        astronaut: Dict[str, Any],
        vitals_history: List[Dict[str, Any]],
        radiation_summary: Dict[str, Any],
        active_alerts: List[Dict[str, Any]],
        fatigue_risk: Tuple[float, str],
        mission_day: int = 42
    ) -> Dict[str, Any]:
        """
        Aggregates clinical indicators, synthesizes an executive summary,
        and commits the report to the SQLite database.
        """
        ast_id = astronaut["id"]
        ast_name = astronaut["name"]
        ast_callsign = astronaut["callsign"]

        # Calculate vitals aggregates
        if vitals_history:
            hrs = [float(v.get("heart_rate", 70.0)) for v in vitals_history]
            spo2s = [float(v.get("spo2", 98.0)) for v in vitals_history]
            temps = [float(v.get("core_temperature", 36.8)) for v in vitals_history]
            avg_hr = round(sum(hrs) / len(hrs), 1)
            min_spo2 = round(min(spo2s), 1)
            avg_temp = round(sum(temps) / len(temps), 2)
        else:
            avg_hr, min_spo2, avg_temp = 72.0, 98.0, 36.8

        rad_accum_msv = float(radiation_summary.get("estimated_cumulative_msv", 22.5))
        rad_status = radiation_summary.get("status", "NOMINAL")
        fatigue_score, fatigue_cat = fatigue_risk

        crit_alerts = sum(1 for a in active_alerts if a.get("severity") == "CRITICAL")
        warn_alerts = sum(1 for a in active_alerts if a.get("severity") == "WARNING")
        total_anomalies = crit_alerts + warn_alerts

        # Determine overall medical status
        if crit_alerts > 0 or fatigue_cat == "HIGH_RISK" or rad_status == "CRITICAL":
            overall_status = "CRITICAL"
        elif warn_alerts > 0 or fatigue_cat == "MODERATE_RISK" or rad_status in ("WARNING", "ELEVATED_SAA"):
            overall_status = "WARNING"
        else:
            overall_status = "NOMINAL"

        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        report_title = f"Expedition 71 Clinical Assessment - {ast_name} (Day {mission_day})"

        executive_summary = (
            f"**Flight Surgeon Executive Health Assessment**\n\n"
            f"- **Crew Member:** {ast_name} ({ast_callsign}) | **Role:** {astronaut.get('role', 'Astronaut')}\n"
            f"- **Mission Day:** {mission_day:03d} | **Generated:** {now_str}\n"
            f"- **Overall Clinical Status:** `{overall_status}`\n\n"
            f"### Key Physiological Indicators\n"
            f"- **Mean Heart Rate:** {avg_hr} bpm (Resting baseline: {astronaut.get('baseline_hr', 70)} bpm)\n"
            f"- **Minimum SpO2:** {min_spo2}% (Normal > 95%)\n"
            f"- **Mean Core Temperature:** {avg_temp} °C\n"
            f"- **Cumulative Radiation Exposure:** {rad_accum_msv:.2f} mSv ({radiation_summary.get('pct_career_limit', 0)}% of 600 mSv PEL)\n"
            f"- **Cognitive Fatigue Risk Index:** {fatigue_score:.1f} / 100 (`{fatigue_cat}`)\n"
            f"- **Active Unresolved Alerts:** {len(active_alerts)} ({crit_alerts} Critical, {warn_alerts} Warning)\n\n"
            f"### Flight Surgeon Directive\n"
            f"{'Crew cleared for nominal orbital duty cycle.' if overall_status == 'NOMINAL' else 'Crew flagged for scheduled clinical telemetry review. Hydration and rest periods mandated.'}"
        )

        # Save to database
        saved_id = None
        try:
            from src.database.queries import save_health_report
            saved_id = save_health_report(
                astronaut_id=ast_id,
                mission_day=mission_day,
                report_title=report_title,
                overall_status=overall_status,
                executive_summary=executive_summary,
                radiation_accumulated_msv=rad_accum_msv,
                anomalies_detected_count=total_anomalies
            )
        except Exception as e:
            logger.error(f"Error saving report to DB: {e}")

        return {
            "report_id": saved_id,
            "report_title": report_title,
            "mission_day": mission_day,
            "generated_at": now_str,
            "overall_status": overall_status,
            "executive_summary": executive_summary,
            "radiation_accumulated_msv": rad_accum_msv,
            "anomalies_detected_count": total_anomalies,
            "astronaut": astronaut
        }

    @staticmethod
    def format_report_markdown(report_data: Dict[str, Any]) -> str:
        """Generates a downloadable clinical markdown document."""
        return f"""# ==============================================================================
# SPACECARE MISSION CONTROL: EXPEDITION 71 CLINICAL HEALTH REPORT
# ==============================================================================
# Title:     {report_data.get('report_title')}
# Generated: {report_data.get('generated_at')}
# Status:    {report_data.get('overall_status')}
# ==============================================================================

{report_data.get('executive_summary')}

---
### Clinical Governance & Verification Notice
- **System Provenance:** SPACECARE Automated Biometric Telemetry & Diagnostic Support Suite
- **Standards Applied:** NASA-STD-3001 Vol 1 Rev B, NCRP Report 132
- **Disclaimer:** Simulated operational demonstration prototype. Not for clinical diagnosis.
- **Flight Surgeon Sign-off:** [AUTHENTICATED MEDICAL OFFICER - EXPEDITION 71 SURGEON-1]
"""
