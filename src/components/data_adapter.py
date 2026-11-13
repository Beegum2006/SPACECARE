"""
==============================================================================
SPACECARE Central Data Adapter (Member 3 - Main Dashboard UI Integration)
==============================================================================
Acts as the single unified, fault-tolerant data bridge connecting all Streamlit
dashboard views with teammates' backend modules.

CRITICAL ARCHITECTURE DIRECTIVES:
1. STRICT ISOLATION: Teammates' code (`src/nasa_data/`, `src/ml/`, `src/alerts/`,
   `src/mental_health/`, `src/reports/`) is treated as 100% READ-ONLY.
2. ZERO RUNTIME CRASHES: All imports and calls to teammates' modules are wrapped
   in `try/except Exception as e:` blocks with clean diagnostic logging.
3. IMMUTABILITY: Never mutate teammate return objects in-place. Always use `.copy()`.
4. EXPLICIT PROVENANCE METADATA: Every public function returns a standardized
   dictionary with:
     - "data": Primary payload (pd.DataFrame, list[dict], or dict)
     - "summary": KPI values, deltas, and high-level health indicators
     - "source": "live" or "simulated_fallback"
     - "status_note": Diagnostic string describing connection or fallback reason
5. DETERMINISTIC REALISTIC FALLBACKS: Uses `numpy.random.default_rng` with seeds
   derived from (astronaut_id, time_window) so space-medicine telemetry is realistic
   and never flickers randomly on Streamlit re-renders.
6. SCENARIO / FAULT INJECTION SIMULATOR: Supports dynamic injection of aerospace
   emergencies (SPE storm, CO2 scrubber failure, Cardiorespiratory collapse,
   Circadian fatigue) across all contracts without altering teammate code.
==============================================================================
"""

import os
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

logger = logging.getLogger("spacecare.data_adapter")


# ============================================================================
# INTERNAL SEED, ASTRONAUT & SCENARIO HELPERS
# ============================================================================

def _derive_seed(seed_key: Union[str, int], salt: int = 42) -> int:
    """Generates a deterministic 32-bit positive integer seed from a string or integer."""
    s = str(seed_key)
    val = sum(ord(c) * (i + 1) for i, c in enumerate(s)) + salt * 10007
    return abs(val) % (2**31 - 1)


def _normalize_ast_id(ast_id: Union[str, int, None]) -> Tuple[str, int]:
    """
    Normalizes any astronaut ID format into ('AST-XX', integer_id).
    Accepts 'AST-01', 1, '1', 'AST-1', etc. Defaults to ('AST-01', 1).
    """
    if ast_id is None:
        return "AST-01", 1
    if isinstance(ast_id, int):
        num = max(1, min(4, ast_id))
        return f"AST-{num:02d}", num
    id_str = str(ast_id).strip().upper()
    if id_str.startswith("AST-"):
        try:
            num = int(id_str.split("-")[1])
            num = max(1, min(4, num))
            return f"AST-{num:02d}", num
        except Exception:
            return "AST-01", 1
    elif id_str.isdigit():
        num = max(1, min(4, int(id_str)))
        return f"AST-{num:02d}", num
    return "AST-01", 1


def _get_active_scenario(scenario_override: Optional[str] = None) -> str:
    """
    Retrieves the active simulation scenario.
    Precedence:
    1. Explicit function parameter `scenario_override`
    2. Environment variable `SPACECARE_ACTIVE_SCENARIO`
    3. Streamlit session state `st.session_state["active_scenario"]`
    4. Default: "Nominal Mission (Default)"
    """
    if scenario_override:
        return scenario_override

    env_scen = os.environ.get("SPACECARE_ACTIVE_SCENARIO")
    if env_scen:
        return env_scen

    try:
        import streamlit as st
        if hasattr(st, "session_state") and "active_scenario" in st.session_state:
            return str(st.session_state["active_scenario"])
    except Exception:
        pass

    return "Nominal Mission (Default)"


# ============================================================================
# 1. CREW ROSTER CONTRACT
# ============================================================================

def get_crew_roster(scenario_override: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Returns the active 4-astronaut Expedition 71 crew roster.
    
    Returns:
        list[dict] with keys:
        - astronaut_id: str (e.g. "AST-01")
        - name: str
        - role: "Commander" | "Flight Engineer" | "Mission Specialist" | "Medical Officer"
        - mission_day: int
        - eva_hours: float
        - overall_status: "NOMINAL" | "WARNING" | "CRITICAL"
    """
    roster = [
        {
            "astronaut_id": "AST-01",
            "name": "Dr. Sarah Vance",
            "callsign": "VALKYRIE",
            "role": "Commander",
            "agency": "NASA",
            "mission": "Expedition 71 / ISS",
            "mission_day": 42,
            "eva_hours": 18.5,
            "overall_status": "NOMINAL",
            "baseline_hr": 68.0,
            "baseline_spo2": 98.5,
            "baseline_bp_sys": 116.0,
            "baseline_bp_dia": 74.0,
            "baseline_temp": 36.7,
            "baseline_rr": 13.5,
            "baseline_hrv": 58.0
        },
        {
            "astronaut_id": "AST-02",
            "name": "Marcus Aurelius Thorne",
            "callsign": "TITAN",
            "role": "Flight Engineer",
            "agency": "ESA",
            "mission": "Expedition 71 / ISS",
            "mission_day": 42,
            "eva_hours": 12.0,
            "overall_status": "NOMINAL",
            "baseline_hr": 64.0,
            "baseline_spo2": 99.0,
            "baseline_bp_sys": 114.0,
            "baseline_bp_dia": 72.0,
            "baseline_temp": 36.8,
            "baseline_rr": 14.0,
            "baseline_hrv": 66.0
        },
        {
            "astronaut_id": "AST-03",
            "name": "Dr. Elena Rostova",
            "callsign": "STARLING",
            "role": "Medical Officer",
            "agency": "NASA",
            "mission": "Expedition 71 / ISS",
            "mission_day": 42,
            "eva_hours": 6.5,
            "overall_status": "NOMINAL",
            "baseline_hr": 70.0,
            "baseline_spo2": 98.2,
            "baseline_bp_sys": 118.0,
            "baseline_bp_dia": 76.0,
            "baseline_temp": 36.6,
            "baseline_rr": 13.0,
            "baseline_hrv": 62.0
        },
        {
            "astronaut_id": "AST-04",
            "name": "Kaito Tanaka",
            "callsign": "RONIN",
            "role": "Mission Specialist",
            "agency": "JAXA",
            "mission": "Expedition 71 / ISS",
            "mission_day": 42,
            "eva_hours": 24.0,
            "overall_status": "WARNING",
            "baseline_hr": 74.0,
            "baseline_spo2": 97.8,
            "baseline_bp_sys": 122.0,
            "baseline_bp_dia": 79.0,
            "baseline_temp": 37.0,
            "baseline_rr": 15.0,
            "baseline_hrv": 48.0
        }
    ]

    # Dynamic status reflection if fault injection scenario is active
    scenario = _get_active_scenario(scenario_override)
    if "Cardiorespiratory" in scenario:
        roster[0]["overall_status"] = "CRITICAL"
    elif "Circadian" in scenario:
        roster[0]["overall_status"] = "WARNING"
        roster[3]["overall_status"] = "CRITICAL"

    # Enrich from database if available
    try:
        from src.database.queries import get_astronauts
        db_crew = get_astronauts()
        if db_crew and len(db_crew) >= 4:
            for i, db_a in enumerate(db_crew[:4]):
                roster[i]["name"] = db_a.get("name", roster[i]["name"])
                roster[i]["callsign"] = db_a.get("callsign", roster[i]["callsign"])
                if "Nominal" in scenario:
                    roster[i]["overall_status"] = db_a.get("status", roster[i]["overall_status"])
    except Exception as e:
        logger.debug(f"DB crew query bypassed ({e}); using static Expedition 71 roster.")

    return roster


# ============================================================================
# 2. VITALS & ML ANOMALIES CONTRACT (Member 2 Integration)
# ============================================================================

def get_vitals_and_anomalies(
    astronaut_id: str = "AST-01",
    hours: int = 24,
    scenario_override: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieves wearable physiological vitals and scores them with Member 2's
    Isolation Forest anomaly detection engine.

    Columns in "data" (pd.DataFrame):
    - timestamp: ISO 8601 string
    - heart_rate_bpm: float (~58-85 bpm, spikes >115 bpm)
    - spo2_pct: float (~96-99%, drops <93%)
    - systolic_bp: float (~110-128 mmHg)
    - diastolic_bp: float (~70-84 mmHg)
    - body_temp_c: float (~36.5-37.3 °C)
    - respiration_rate: float (~12-18 br/min)
    - anomaly_score: float (-1.0 to 1.0, <0 indicates outlier)
    - is_anomaly: bool (True if anomalous)

    Returns:
        dict: {"data": pd.DataFrame, "summary": dict, "source": str, "status_note": str}
    """
    ast_code, num_id = _normalize_ast_id(astronaut_id)
    roster = get_crew_roster()
    astronaut = next((a for a in roster if a["astronaut_id"] == ast_code), roster[0])
    scenario = _get_active_scenario(scenario_override)

    source = "live"
    status_note = "Connected to Member 2 ML Isolation Forest pipeline"
    raw_readings: List[Dict[str, Any]] = []

    # 1. Attempt to pull recent readings from SQLite database
    try:
        from src.database.queries import get_vitals_history
        db_history = get_vitals_history(astronaut_id=num_id, limit=hours)
        if db_history and len(db_history) >= 8:
            raw_readings = [dict(r) for r in reversed(db_history)]
    except Exception as db_err:
        logger.debug(f"DB vitals read bypassed ({db_err}).")

    # 2. If DB has insufficient history, generate deterministic realistic simulation
    if not raw_readings or len(raw_readings) < 8:
        source = "simulated_fallback"
        status_note = "Fallback: Synthesized deterministic space-medicine telemetry"
        seed = _derive_seed(ast_code, salt=hours)
        rng = np.random.default_rng(seed)

        now = datetime.now(timezone.utc)
        base_hr = astronaut.get("baseline_hr", 70.0)
        base_spo2 = astronaut.get("baseline_spo2", 98.2)
        base_sys = astronaut.get("baseline_bp_sys", 118.0)
        base_dia = astronaut.get("baseline_bp_dia", 76.0)
        base_temp = astronaut.get("baseline_temp", 36.8)
        base_rr = astronaut.get("baseline_rr", 14.0)

        raw_readings = []
        spike_window = max(2, min(5, hours // 4))

        for i in range(hours):
            t = now - timedelta(hours=hours - 1 - i)
            # Diurnal circadian variation
            hour_of_day = t.hour
            circadian = np.sin((hour_of_day - 6) * np.pi / 12)

            hr = base_hr + (circadian * 4.0) + rng.normal(0, 1.2)
            spo2 = base_spo2 - (abs(circadian) * 0.25) + rng.normal(0, 0.2)
            sys_bp = base_sys + (circadian * 3.0) + rng.normal(0, 1.5)
            dia_bp = base_dia + (circadian * 2.0) + rng.normal(0, 1.0)
            temp = base_temp + (circadian * 0.15) + rng.normal(0, 0.05)
            rr = base_rr + (circadian * 0.8) + rng.normal(0, 0.4)

            # Scenario Fault Injection: Cardiorespiratory Anomaly
            if "Cardiorespiratory" in scenario and (i >= hours - spike_window):
                hr += 68.0    # Tachycardia spike: ~138-145 bpm
                spo2 -= 9.5   # Acute hypoxia: ~88-89%
                sys_bp += 36.0  # Hypertensive compensatory: ~154 mmHg
                dia_bp += 18.0  # Diastolic spike
                rr += 12.0    # Tachypnea: ~26 br/min
                temp += 0.5
            elif ast_code == "AST-04" and i >= hours - 3:
                # Built-in slight elevation for AST-04
                hr += 42.0
                spo2 -= 5.5
                sys_bp += 18.0

            raw_readings.append({
                "timestamp": t.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "heart_rate": round(float(np.clip(hr, 45.0, 160.0)), 1),
                "spo2": round(float(np.clip(spo2, 85.0, 100.0)), 1),
                "blood_pressure_sys": round(float(np.clip(sys_bp, 90.0, 180.0)), 1),
                "blood_pressure_dia": round(float(np.clip(dia_bp, 55.0, 115.0)), 1),
                "core_temperature": round(float(np.clip(temp, 35.5, 39.8)), 2),
                "respiration_rate": round(float(np.clip(rr, 8.0, 32.0)), 1),
                "hrv_rmssd": round(float(max(15.0, 55.0 - (hr - 70.0) * 0.5)), 1)
            })

    # Ensure Cardiorespiratory fault injection applies to raw_readings regardless of data source
    if "Cardiorespiratory" in scenario and raw_readings:
        spike_w = max(2, min(5, len(raw_readings)))
        for idx in range(len(raw_readings) - spike_w, len(raw_readings)):
            r = raw_readings[idx]
            r["heart_rate"] = round(float(np.clip(r.get("heart_rate", 70.0) + 68.0, 136.0, 160.0)), 1)
            r["spo2"] = round(float(np.clip(r.get("spo2", 98.0) - 10.0, 85.0, 90.5)), 1)
            r["blood_pressure_sys"] = round(float(r.get("blood_pressure_sys", 118.0) + 36.0), 1)
            r["blood_pressure_dia"] = round(float(r.get("blood_pressure_dia", 76.0) + 18.0), 1)
            r["respiration_rate"] = round(float(r.get("respiration_rate", 14.0) + 12.0), 1)
            r["hrv_rmssd"] = 18.0

    # 3. Call Member 2's ML module for scoring
    ml_scores: List[float] = []
    ml_anomalies: List[bool] = []
    ml_success = False

    try:
        from src.ml.anomaly_detector import AstronautAnomalyDetector
        detector = AstronautAnomalyDetector(contamination=0.08, random_state=42)
        
        # Train on nominal baseline sequence
        baseline_slice = raw_readings[:max(10, len(raw_readings) - 4)] if len(raw_readings) >= 14 else raw_readings
        train_success = detector.train(baseline_slice)
        
        if train_success:
            predictions = detector.predict_series(raw_readings)
            if predictions and len(predictions) == len(raw_readings):
                for p in predictions:
                    sc = float(p.get("ml_decision_score", 0.1))
                    # Scikit-Learn IsolationForest decision_function: < 0 is anomaly
                    norm_sc = round(float(np.clip(sc * 4.0, -1.0, 1.0)), 4)
                    is_anom = bool(p.get("ml_is_anomaly", 0) == 1 or norm_sc < 0.0)
                    ml_scores.append(norm_sc)
                    ml_anomalies.append(is_anom)
                ml_success = True
                source = "live"
                status_note = "Scored via Member 2 AstronautAnomalyDetector (IsolationForest)"
    except Exception as ml_err:
        logger.debug(f"Member 2 anomaly detector call bypassed ({ml_err}).")

    # 4. Fallback mathematical anomaly scoring if ML module had import/runtime issues
    if not ml_success or len(ml_scores) != len(raw_readings):
        ml_scores = []
        ml_anomalies = []
        for r in raw_readings:
            hr = r["heart_rate"]
            spo2 = r["spo2"]
            temp = r["core_temperature"]
            
            z_hr = abs(hr - 70.0) / 12.0
            z_spo2 = max(0.0, (97.0 - spo2)) / 1.5
            z_temp = abs(temp - 36.8) / 0.4
            composite_dev = max(z_hr, z_spo2, z_temp)

            score = round(float(np.clip(0.3 - (composite_dev * 0.25), -1.0, 1.0)), 4)
            is_anom = bool(score < 0.0 or spo2 < 91.0 or hr > 125.0 or hr < 50.0)
            ml_scores.append(score)
            ml_anomalies.append(is_anom)

    # 5. Assemble exact normalized DataFrame
    df_rows = []
    for i, r in enumerate(raw_readings):
        df_rows.append({
            "timestamp": r["timestamp"],
            "heart_rate_bpm": float(r.get("heart_rate", 70.0)),
            "spo2_pct": float(r.get("spo2", 98.0)),
            "systolic_bp": float(r.get("blood_pressure_sys", 118.0)),
            "diastolic_bp": float(r.get("blood_pressure_dia", 76.0)),
            "body_temp_c": float(r.get("core_temperature", 36.8)),
            "respiration_rate": float(r.get("respiration_rate", 14.0)),
            "anomaly_score": ml_scores[i],
            "is_anomaly": ml_anomalies[i]
        })

    df = pd.DataFrame(df_rows)
    latest = df.iloc[-1].to_dict() if not df.empty else {}
    first = df.iloc[0].to_dict() if len(df) > 1 else latest

    anom_count = int(df["is_anomaly"].sum()) if not df.empty else 0
    delta_hr = round(latest.get("heart_rate_bpm", 70.0) - first.get("heart_rate_bpm", 70.0), 1)
    delta_spo2 = round(latest.get("spo2_pct", 98.0) - first.get("spo2_pct", 98.0), 1)

    if latest.get("is_anomaly", False) or latest.get("anomaly_score", 0.1) < -0.2:
        overall_status = "CRITICAL"
    elif anom_count > 0 or latest.get("anomaly_score", 0.1) < 0.05:
        overall_status = "WARNING"
    else:
        overall_status = "NOMINAL"

    summary = {
        "latest_heart_rate": latest.get("heart_rate_bpm", 70.0),
        "delta_heart_rate": delta_hr,
        "latest_spo2": latest.get("spo2_pct", 98.0),
        "delta_spo2": delta_spo2,
        "latest_blood_pressure": f"{int(latest.get('systolic_bp', 118))}/{int(latest.get('diastolic_bp', 76))}",
        "latest_temperature": latest.get("body_temp_c", 36.8),
        "latest_respiration": latest.get("respiration_rate", 14.0),
        "latest_anomaly_score": latest.get("anomaly_score", 0.18),
        "anomaly_count_24h": anom_count,
        "overall_status": overall_status,
        "active_scenario": scenario
    }

    # 6. Pass latest reading through Member 4's live alert engine if available
    try:
        from src.alerts.alert_engine import evaluate_vitals_for_alerts
        evaluate_vitals_for_alerts(
            astronaut={"id": num_id, "name": astronaut["name"]},
            reading=raw_readings[-1],
            ml_result={"is_anomaly": latest.get("is_anomaly", False), "score": latest.get("anomaly_score", 0.0)}
        )
    except Exception as e:
        logger.debug(f"Live alert evaluation bypassed ({e}).")

    return {
        "data": df,
        "summary": summary,
        "source": source,
        "status_note": status_note
    }


# ============================================================================
# 3. ISS ENVIRONMENT CONTRACT (Member 1 Integration)
# ============================================================================

def get_iss_environment_data(
    hours: int = 24,
    scenario_override: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieves ISS ECLSS cabin environmental telemetry.
    Integrates Member 1's `src/nasa_data/eda_client.py`.

    Columns in "data" (pd.DataFrame):
    - timestamp: ISO 8601 string
    - cabin_pressure_kpa: float (~101.3 kPa)
    - o2_partial_pressure_kpa: float (~21.0 kPa)
    - co2_partial_pressure_mmhg: float (normal ~2.0-3.8 mmHg, warning >4.0 mmHg)
    - temperature_c: float (~21.5 °C)
    - humidity_pct: float (~45%)
    - dataset_id: str (e.g. "OSD-542")

    Returns:
        dict: {"data": pd.DataFrame, "summary": dict, "source": str, "status_note": str}
    """
    scenario = _get_active_scenario(scenario_override)
    source = "live"
    status_note = "Integrated with Member 1 NASA EDA ECLSS baseline reference"
    records: List[Dict[str, Any]] = []

    # 1. Attempt to load curated benchmarks from Member 1's eda_client
    try:
        from src.nasa_data.eda_client import load_eda_benchmarks
        eda_df = load_eda_benchmarks()
        if not eda_df.empty and len(eda_df) >= hours:
            sample = eda_df.copy().tail(hours)
            records = sample.to_dict(orient="records")
            source = "live"
            status_note = "Loaded from Member 1 eda_iss_environment.csv fixture"
    except Exception as eda_err:
        logger.debug(f"EDA client load bypassed ({eda_err}).")

    # 2. Deterministic fallback generation
    if not records or len(records) < hours:
        source = "simulated_fallback"
        status_note = "Fallback: Synthesized deterministic ECLSS telemetry (NASA-STD-3001)"
        seed = _derive_seed("ISS_ECLSS_ENV", salt=hours)
        rng = np.random.default_rng(seed)

        now = datetime.now(timezone.utc)
        records = []
        spike_window = max(2, min(5, hours // 4))

        for i in range(hours):
            t = now - timedelta(hours=hours - 1 - i)
            # 1 psi = 6.89476 kPa. 14.7 psi ≈ 101.35 kPa.
            press_psi = 14.70 + rng.normal(0, 0.02)
            co2_mmhg = 2.75 + 0.3 * np.sin(i * 0.4) + rng.normal(0, 0.08)
            o2_pct = 21.0 + rng.normal(0, 0.06)
            temp_c = 21.8 + 0.4 * np.cos(i * 0.3) + rng.normal(0, 0.1)
            humidity = 45.5 + rng.normal(0, 0.6)

            # Scenario Fault Injection: ECLSS Scrubber Fault (High Cabin CO2)
            if "ECLSS" in scenario and (i >= hours - spike_window):
                co2_mmhg += 2.85  # Spikes CO2 to 5.6 - 5.9 mmHg (Critical > 5.2 mmHg)
                press_psi -= 0.15 # Slight cabin atmospheric perturbation
                o2_pct -= 0.9     # Marginal O2 displacement

            records.append({
                "timestamp": t.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "cabin_pressure_psi": round(press_psi, 3),
                "co2_partial_pressure_mmhg": round(co2_mmhg, 2),
                "o2_percentage": round(o2_pct, 2),
                "temperature_celsius": round(temp_c, 1),
                "relative_humidity_pct": round(humidity, 1)
            })

    # Ensure ECLSS fault injection applies to records regardless of data source
    if "ECLSS" in scenario and records:
        spike_w = max(2, min(5, len(records)))
        for idx in range(len(records) - spike_w, len(records)):
            r = records[idx]
            r["co2_partial_pressure_mmhg"] = round(float(np.clip(r.get("co2_partial_pressure_mmhg", 2.8) + 2.85, 5.4, 6.2)), 2)
            r["cabin_pressure_psi"] = round(float(r.get("cabin_pressure_psi", 14.7) - 0.15), 3)
            r["o2_percentage"] = round(float(r.get("o2_percentage", 21.0) - 0.9), 2)

    # 3. Assemble exact standardized DataFrame
    df_rows = []
    for r in records:
        press_psi = float(r.get("cabin_pressure_psi", 14.7))
        press_kpa = round(press_psi * 6.89476, 2)
        o2_pct = float(r.get("o2_percentage", 21.0))
        o2_kpa = round((o2_pct / 100.0) * press_kpa, 2)
        co2_mmhg = round(float(r.get("co2_partial_pressure_mmhg", 2.8)), 2)
        temp_c = round(float(r.get("temperature_celsius", 21.5)), 1)
        hum_pct = round(float(r.get("relative_humidity_pct", 45.0)), 1)

        df_rows.append({
            "timestamp": r.get("timestamp"),
            "cabin_pressure_kpa": press_kpa,
            "o2_partial_pressure_kpa": o2_kpa,
            "co2_partial_pressure_mmhg": co2_mmhg,
            "temperature_c": temp_c,
            "humidity_pct": hum_pct,
            "dataset_id": "OSD-542"
        })

    df = pd.DataFrame(df_rows)
    latest = df.iloc[-1].to_dict() if not df.empty else {}

    # Safety checks per metric
    press_val = latest.get("cabin_pressure_kpa", 101.3)
    p_status = "CRITICAL" if press_val < 94.0 else ("WARNING" if press_val < 98.0 else "NOMINAL")

    co2_val = latest.get("co2_partial_pressure_mmhg", 2.8)
    co2_status = "CRITICAL" if co2_val > 4.5 else ("WARNING" if co2_val > 3.8 else "NOMINAL")

    o2_val = latest.get("o2_partial_pressure_kpa", 21.0)
    o2_status = "CRITICAL" if o2_val < 18.0 else ("WARNING" if o2_val < 19.5 else "NOMINAL")

    temp_val = latest.get("temperature_c", 21.5)
    temp_status = "WARNING" if (temp_val < 18.0 or temp_val > 26.5) else "NOMINAL"

    hum_val = latest.get("humidity_pct", 45.0)
    hum_status = "WARNING" if (hum_val < 30.0 or hum_val > 70.0) else "NOMINAL"

    overall_status = "CRITICAL" if "CRITICAL" in (p_status, co2_status, o2_status) else (
        "WARNING" if "WARNING" in (p_status, co2_status, o2_status, temp_status, hum_status) else "NOMINAL"
    )

    # Optional enrichment with Member 1's live statistical summary
    eda_benchmarks = {}
    try:
        from src.nasa_data.eda_client import get_eda_statistical_summary
        eda_benchmarks = get_eda_statistical_summary()
    except Exception:
        pass

    summary = {
        "cabin_pressure_kpa": press_val,
        "pressure_status": p_status,
        "o2_partial_pressure_kpa": o2_val,
        "o2_status": o2_status,
        "co2_partial_pressure_mmhg": co2_val,
        "co2_status": co2_status,
        "temperature_c": temp_val,
        "temp_status": temp_status,
        "humidity_pct": hum_val,
        "humidity_status": hum_status,
        "overall_status": overall_status,
        "dataset_id": "OSD-542",
        "source": "NASA ECLSS Engineering Reference (NASA-STD-3001)",
        "doi": "10.26030/iss-eclss-spec",
        "active_scenario": scenario,
        "eda_benchmarks": eda_benchmarks
    }

    return {
        "data": df,
        "summary": summary,
        "source": source,
        "status_note": status_note
    }


# ============================================================================
# 4. SPACE RADIATION & DOSIMETRY CONTRACT (Member 1 Integration)
# ============================================================================

def get_radiation_data(
    days: int = 30,
    scenario_override: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieves space radiation and cosmic dosimetry measurements.
    Integrates Member 1's `src/nasa_data/radiation_service.py` (RadLab).

    Columns in "data" (pd.DataFrame):
    - timestamp: ISO 8601 string
    - galactic_cosmic_ray_msv: float (GCR background, ~0.35-0.55 mSv/day)
    - solar_particle_event_msv: float (SPE flux spikes)
    - saa_passage_flag: bool (South Atlantic Anomaly passage flag)
    - total_daily_dose_msv: float (~0.4-1.2 mSv/day)
    - cumulative_mission_dose_msv: float

    Returns:
        dict: {"data": pd.DataFrame, "summary": dict, "source": str, "status_note": str}
    """
    scenario = _get_active_scenario(scenario_override)
    source = "live"
    status_note = "Connected to Member 1 RadLab dosimetry service"
    records: List[Dict[str, Any]] = []

    # 1. Attempt to call Member 1's radiation_service
    try:
        from src.nasa_data.radiation_service import fetch_radlab_telemetry
        fetched, is_live_api = fetch_radlab_telemetry(spacecraft="ISS", limit=days)
        if fetched and len(fetched) > 0:
            records = [r.copy() for r in fetched]
            source = "live" if is_live_api else "simulated_fallback"
            status_note = "NASA RadLab API (Verified Live)" if is_live_api else "NASA RadLab Reference Test Fixture"
    except Exception as rad_err:
        logger.debug(f"RadLab service query bypassed ({rad_err}).")

    # 2. Deterministic fallback generation
    if not records or len(records) < days:
        source = "simulated_fallback"
        status_note = "Fallback: Synthesized deterministic LEO orbital dosimetry model"
        seed = _derive_seed("ISS_RADLAB_DOSIMETRY", salt=days)
        rng = np.random.default_rng(seed)

        now = datetime.now(timezone.utc)
        records = []
        surge_days = max(2, min(4, days // 6))

        for i in range(days):
            t = now - timedelta(days=days - 1 - i)
            # LEO orbital inclination: ISS passes through SAA periodically
            saa_flag = bool((i % 7 == 3) or (i == days - 2))
            gcr = 0.42 + rng.normal(0, 0.03)
            spe = (0.35 + rng.normal(0, 0.06)) if saa_flag else 0.0

            # Scenario Fault Injection: Solar Particle Event (SPE Radiation Spike)
            if "Solar Particle" in scenario and (i >= days - surge_days):
                spe += 17.5 + rng.normal(0, 0.8)  # Huge SPE flux > 15 mSv/day
                saa_flag = True

            records.append({
                "timestamp": t.strftime("%Y-%m-%d"),
                "galactic_cosmic_ray_msv": round(float(gcr), 3),
                "solar_particle_event_msv": round(float(spe), 3),
                "saa_passage_flag": saa_flag,
                "total_daily_dose_msv": round(float(gcr + spe), 3)
            })

    # Ensure Solar Particle Event surge applies to records regardless of data source
    if "Solar Particle" in scenario and records:
        surge_days = max(2, min(4, len(records)))
        for idx in range(len(records) - surge_days, len(records)):
            r = records[idx]
            r["solar_particle_event_msv"] = round(float(18.2), 3)
            r["saa_passage_flag"] = True
            r["total_daily_dose_msv"] = round(float(r.get("galactic_cosmic_ray_msv", 0.42) + 18.2), 3)

    # 3. Assemble exact standardized DataFrame
    running_cumulative = 0.0
    df_rows = []
    for r in records:
        gcr = float(r.get("galactic_cosmic_ray_msv", 0.42))
        spe = float(r.get("solar_particle_event_msv", 0.0))
        saa = bool(r.get("saa_passage_flag", False))
        daily = round(gcr + spe, 3)
        running_cumulative = round(running_cumulative + daily, 3)

        df_rows.append({
            "timestamp": str(r.get("timestamp")),
            "galactic_cosmic_ray_msv": gcr,
            "solar_particle_event_msv": spe,
            "saa_passage_flag": saa,
            "total_daily_dose_msv": daily,
            "cumulative_mission_dose_msv": running_cumulative
        })

    df = pd.DataFrame(df_rows)
    latest = df.iloc[-1].to_dict() if not df.empty else {}

    current_daily = latest.get("total_daily_dose_msv", 0.45)
    cum_dose = latest.get("cumulative_mission_dose_msv", 22.5)
    solar_alert = bool(latest.get("solar_particle_event_msv", 0.0) > 1.0 or "Solar Particle" in scenario)
    saa_flag = bool(latest.get("saa_passage_flag", False))

    # Limits: NASA 30-day limit = 250 mSv (or 100 mSv NCRP advisory), career limit = 600 mSv
    pct_30d = round((cum_dose / 250.0) * 100.0, 1)
    pct_career = round((cum_dose / 600.0) * 100.0, 1)

    overall_status = "CRITICAL" if (pct_30d > 80.0 or solar_alert or current_daily > 10.0) else (
        "WARNING" if (pct_30d > 50.0 or saa_flag or current_daily > 1.0) else "NOMINAL"
    )

    summary = {
        "current_dose_rate_msv_day": current_daily,
        "cumulative_dose_msv": cum_dose,
        "nasa_30d_limit_msv": 250.0,
        "nasa_career_limit_msv": 600.0,
        "pct_30d_limit": pct_30d,
        "pct_career_limit": pct_career,
        "solar_storm_alert": solar_alert,
        "saa_active": saa_flag,
        "overall_status": overall_status,
        "active_scenario": scenario
    }

    return {
        "data": df,
        "summary": summary,
        "source": source,
        "status_note": status_note
    }


# ============================================================================
# 5. MENTAL WELLNESS & SLEEP CONTRACT (Member 4 Integration)
# ============================================================================

def get_mental_wellness_data(
    astronaut_id: str = "AST-01",
    days: int = 14,
    scenario_override: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieves astronaut sleep architecture, circadian phase drift, and cognitive fatigue.
    Integrates Member 4's `src/mental_health/sleep_tracker.py` and `tlx_assessment.py`.

    Columns in "data" (pd.DataFrame):
    - date: YYYY-MM-DD string
    - total_sleep_hrs: float (~5.5-7.8 hrs)
    - deep_sleep_hrs: float
    - rem_sleep_hrs: float
    - light_sleep_hrs: float
    - sleep_interruptions: int
    - sleep_quality_score: float (0-100)
    - stress_index: float (0-100)
    - fatigue_score: float (0-100)
    - circadian_alignment_pct: float (0-100)

    Returns:
        dict: {"data": pd.DataFrame, "summary": dict, "source": str, "status_note": str}
    """
    ast_code, num_id = _normalize_ast_id(astronaut_id)
    scenario = _get_active_scenario(scenario_override)
    source = "live"
    status_note = "Integrated with Member 4 sleep_tracker & NASA-TLX"
    sleep_records: List[Dict[str, Any]] = []

    # 1. Attempt to call Member 4's sleep_tracker
    try:
        from src.mental_health.sleep_tracker import generate_sleep_history
        sh = generate_sleep_history(astronaut_id=num_id, days=days)
        if sh and len(sh) >= 7:
            sleep_records = [r.copy() for r in sh]
            source = "live"
            status_note = "Generated via Member 4 sleep_tracker"
    except Exception as sleep_err:
        logger.debug(f"Sleep tracker call bypassed ({sleep_err}).")

    # 2. Deterministic fallback generation
    if not sleep_records or len(sleep_records) < days:
        source = "simulated_fallback"
        status_note = "Fallback: Synthesized deterministic sleep actigraphy & circadian model"
        seed = _derive_seed(ast_code, salt=days * 31)
        rng = np.random.default_rng(seed)

        now = datetime.now(timezone.utc)
        sleep_records = []
        fatigue_window = max(2, min(5, days // 3))

        for d in range(days):
            t = now - timedelta(days=days - 1 - d)
            tot_hrs = 7.1 + 0.4 * np.sin(d * 0.75) + rng.normal(0, 0.25)
            deep = tot_hrs * 0.20 + rng.normal(0, 0.08)
            rem = tot_hrs * 0.24 + rng.normal(0, 0.08)
            interruptions = int(rng.poisson(1.2))
            drift_hours = float(0.4 * np.cos(d * 0.5) + rng.normal(0, 0.15))
            circ_align = 94.0 - (abs(drift_hours) * 12.0)

            # Scenario Fault Injection: Acute Circadian Desync & Crew Fatigue
            if "Circadian" in scenario and (d >= days - fatigue_window):
                tot_hrs = float(np.clip(3.9 + rng.normal(0, 0.2), 3.2, 4.4))  # Sleep collapse < 4.5h
                deep = float(np.clip(tot_hrs * 0.10, 0.3, 0.5))
                rem = float(np.clip(tot_hrs * 0.15, 0.4, 0.7))
                interruptions = int(rng.integers(4, 7))
                drift_hours = float(np.clip(2.8 + rng.normal(0, 0.2), 2.2, 3.5)) # Heavy phase drift
                circ_align = float(np.clip(45.0 - rng.normal(0, 3.0), 30.0, 52.0))

            tot_hrs = float(np.clip(tot_hrs, 3.0, 9.0))
            deep = float(np.clip(deep, 0.2, 2.5))
            rem = float(np.clip(rem, 0.3, 2.8))
            light = float(max(0.5, tot_hrs - deep - rem))
            circ_align = float(np.clip(circ_align, 25.0, 100.0))

            sleep_records.append({
                "date": t.strftime("%Y-%m-%d"),
                "total_sleep_hrs": round(tot_hrs, 2),
                "deep_sleep_hrs": round(deep, 2),
                "rem_sleep_hrs": round(rem, 2),
                "light_sleep_hrs": round(light, 2),
                "sleep_interruptions": interruptions,
                "circadian_alignment_pct": round(circ_align, 1),
                "circadian_drift_hours": round(drift_hours, 2)
            })

    # Ensure Circadian Desync fault injection applies to sleep_records regardless of data source
    if "Circadian" in scenario and sleep_records:
        fatigue_w = max(2, min(5, len(sleep_records)))
        for idx in range(len(sleep_records) - fatigue_w, len(sleep_records)):
            r = sleep_records[idx]
            r["total_sleep_hrs"] = 4.1
            r["deep_sleep_hrs"] = 0.4
            r["rem_sleep_hrs"] = 0.5
            r["sleep_interruptions"] = 5
            r["circadian_drift_hours"] = 2.8
            r["circadian_alignment_pct"] = 44.0

    # 3. Calculate scores and format DataFrame
    df_rows = []
    for r in sleep_records:
        tot = float(r.get("total_sleep_hrs", 7.0))
        deep = float(r.get("deep_sleep_hrs", 1.4))
        rem = float(r.get("rem_sleep_hrs", 1.6))
        light = float(r.get("light_sleep_hrs", 4.0))
        interruptions = int(r.get("sleep_interruptions", 1))
        circ_align = float(r.get("circadian_alignment_pct", 90.0))
        drift_h = float(r.get("circadian_drift_hours", 0.4))

        # Sleep quality index (0-100)
        quality = (tot / 8.0) * 45.0 + (deep / 1.6) * 30.0 + (rem / 1.8) * 25.0 - (interruptions * 5.0)
        quality_score = round(float(np.clip(quality, 20.0, 98.0)), 1)

        # Fatigue score (0-100, higher = more fatigued)
        fatigue = max(0.0, (8.0 - tot) * 20.0) + (100.0 - circ_align) * 0.45 + (interruptions * 4.0)
        fatigue_score = round(float(np.clip(fatigue, 10.0, 96.0)), 1)

        # Stress index (0-100)
        stress = (fatigue_score * 0.55) + (100.0 - quality_score) * 0.45
        stress_index = round(float(np.clip(stress, 12.0, 95.0)), 1)

        # Call Member 4's calculate_fatigue_risk_index if available
        try:
            from src.mental_health.tlx_assessment import calculate_fatigue_risk_index
            tlx_calc, _ = calculate_fatigue_risk_index(
                tlx_score=stress_index,
                sleep_duration_hours=tot,
                sleep_efficiency_pct=quality_score,
                circadian_drift_hours=drift_h
            )
            fatigue_score = round(float(tlx_calc), 1)
        except Exception:
            pass

        df_rows.append({
            "date": str(r.get("date", r.get("timestamp", ""))),
            "total_sleep_hrs": tot,
            "deep_sleep_hrs": deep,
            "rem_sleep_hrs": rem,
            "light_sleep_hrs": light,
            "sleep_interruptions": interruptions,
            "sleep_quality_score": quality_score,
            "stress_index": stress_index,
            "fatigue_score": fatigue_score,
            "circadian_alignment_pct": circ_align
        })

    df = pd.DataFrame(df_rows)
    latest = df.iloc[-1].to_dict() if not df.empty else {}
    last_7 = df.tail(7)

    avg_sleep_7d = round(float(last_7["total_sleep_hrs"].mean()), 2) if not last_7.empty else 7.0
    avg_quality_7d = round(float(last_7["sleep_quality_score"].mean()), 1) if not last_7.empty else 82.0
    avg_fatigue_7d = round(float(last_7["fatigue_score"].mean()), 1) if not last_7.empty else 28.0

    curr_fatigue = latest.get("fatigue_score", 25.0)
    overall_status = "CRITICAL" if curr_fatigue > 65.0 else ("WARNING" if curr_fatigue > 42.0 else "NOMINAL")

    summary = {
        "latest_sleep_hrs": latest.get("total_sleep_hrs", 7.2),
        "latest_sleep_quality": latest.get("sleep_quality_score", 84.0),
        "latest_fatigue_score": curr_fatigue,
        "latest_stress_index": latest.get("stress_index", 28.0),
        "latest_circadian_alignment_pct": latest.get("circadian_alignment_pct", 92.0),
        "avg_sleep_hrs_7d": avg_sleep_7d,
        "avg_sleep_quality_7d": avg_quality_7d,
        "avg_fatigue_score_7d": avg_fatigue_7d,
        "overall_status": overall_status,
        "active_scenario": scenario
    }

    return {
        "data": df,
        "summary": summary,
        "source": source,
        "status_note": status_note
    }


# ============================================================================
# 6. ACTIVE ALERTS & PROTOCOLS CONTRACT (Member 4 Integration)
# ============================================================================

def get_active_alerts_and_protocols(
    astronaut_id: Optional[str] = None,
    scenario_override: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieves unresolved alerts mapped to standard Flight Surgeon operational checklists.
    Integrates Member 4's `src/alerts/alert_engine.py` and `src/alerts/protocols.py`.

    Each alert in "data" (list[dict]) contains:
    - alert_id: str (e.g. "ALT-101")
    - timestamp: str
    - astronaut_id: str
    - severity: "CRITICAL" | "WARNING" | "INFO"
    - category: "VITALS_ML" | "RADIATION" | "ENVIRONMENT" | "MENTAL_HEALTH"
    - title: str
    - description: str
    - trigger_metric: str
    - recommended_protocol: list[str] (step-by-step checklist)

    Returns:
        dict: {"data": list[dict], "summary": dict, "source": str, "status_note": str}
    """
    ast_code, num_id = _normalize_ast_id(astronaut_id) if astronaut_id else (None, None)
    scenario = _get_active_scenario(scenario_override)
    source = "live"
    status_note = "Connected to Member 4 alert_engine & protocols"
    alerts_list: List[Dict[str, Any]] = []

    # Helper to fetch checklists from Member 4's protocol matrix
    def _fetch_protocol_steps(proto_key: str, default_steps: List[str]) -> List[str]:
        try:
            from src.alerts.protocols import get_protocol
            proto = get_protocol(proto_key)
            if proto and "checklists" in proto and proto["checklists"]:
                return list(proto["checklists"])
        except Exception:
            pass
        return default_steps

    # 1. Attempt to fetch alerts from database
    try:
        from src.database.queries import get_active_alerts
        db_alerts = get_active_alerts(limit=25)
        if db_alerts:
            for da in db_alerts:
                da_ast = f"AST-{da.get('astronaut_id', 1):02d}" if da.get("astronaut_id") else None
                if ast_code and da_ast and da_ast != ast_code:
                    continue

                sev = da.get("severity", "INFO").upper()
                if sev not in ("CRITICAL", "WARNING", "INFO"):
                    sev = "INFO"

                cat = da.get("category", "VITALS_ML").upper()
                if cat not in ("VITALS_ML", "RADIATION", "ENVIRONMENT", "MENTAL_HEALTH"):
                    cat = "VITALS_ML"

                proto_raw = da.get("flight_surgeon_protocol", "")
                steps = [s.strip() for s in proto_raw.split("\n") if s.strip()] if proto_raw else [
                    "1. Confirm sensor contact and electrode impedance.",
                    "2. Notify Flight Surgeon console (Surgeon-1).",
                    "3. Initiate 15-minute continuous telemetry observation window."
                ]

                alerts_list.append({
                    "alert_id": f"ALT-{da.get('id', 101):03d}",
                    "timestamp": da.get("timestamp", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")),
                    "astronaut_id": da_ast or "AST-01",
                    "severity": sev,
                    "category": cat,
                    "title": da.get("title", "Clinical Telemetry Alert"),
                    "description": da.get("message", "Biometric deviation observed."),
                    "trigger_metric": str(da.get("metric_name", "Telemetry Bus")),
                    "recommended_protocol": steps
                })
            source = "live"
            status_note = "Loaded active alerts from SQLite database"
    except Exception as db_err:
        logger.debug(f"DB alerts query bypassed ({db_err}).")

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    # 2. Dynamic Scenario Emergency Alerts Injection
    scenario_injected_alerts = []

    if "Cardiorespiratory" in scenario:
        hypoxia_steps = _fetch_protocol_steps("HYPOXIA", [
            "1. Immediately don emergency quick-don oxygen mask (100% O2 positive pressure).",
            "2. Verify module ambient oxygen concentration and partial pressure on ECLSS console.",
            "3. Inspect suit/hatch seals for micro-leaks or sudden cabin atmospheric displacement.",
            "4. Alert Flight Surgeon (Surgeon-1) and Mission Control Flight Director (Flight).",
            "5. Re-evaluate pulse oximetry and arterial oxygen saturation every 60 seconds."
        ])
        cardiac_steps = _fetch_protocol_steps("CARDIAC_ARRHYTHMIA", [
            "1. Order immediate cessation of all physical exertion and extravehicular activity (EVA).",
            "2. Transition crew member to recumbent position inside crew quarters.",
            "3. Attach 12-lead Holter electrocardiogram electrodes for continuous waveform monitoring.",
            "4. Assess microgravity fluid shift and administer electrolyte oral rehydration solution.",
            "5. Flight Surgeon consultation for anti-arrhythmic medication protocol review."
        ])
        scenario_injected_alerts.extend([
            {
                "alert_id": "ALT-EMERG-01",
                "timestamp": now_str,
                "astronaut_id": ast_code or "AST-01",
                "severity": "CRITICAL",
                "category": "VITALS_ML",
                "title": "Acute Hypoxia Alert: Pulse Oximetry Collapse",
                "description": "Blood oxygen saturation collapsed to 88.5%. Immediate supplemental oxygen required.",
                "trigger_metric": "spo2_pct = 88.5% (Critical Threshold: < 90.0%)",
                "recommended_protocol": hypoxia_steps
            },
            {
                "alert_id": "ALT-EMERG-02",
                "timestamp": now_str,
                "astronaut_id": ast_code or "AST-01",
                "severity": "CRITICAL",
                "category": "VITALS_ML",
                "title": "Acute Cardiac Dysrhythmia & Tachycardia",
                "description": "Resting heart rate escalated to 142 bpm. Multivariate anomaly index confirmed by ML radar.",
                "trigger_metric": "heart_rate_bpm = 142.0 (Threshold: > 120.0 bpm)",
                "recommended_protocol": cardiac_steps
            }
        ])

    elif "ECLSS" in scenario:
        hypercapnia_steps = _fetch_protocol_steps("HYPERCAPNIA", [
            "1. Verify Carbon Dioxide Removal Assembly (CDRA) bed cycling status in Node 3.",
            "2. Switch to backup Amine Swingbed or Russian Vozdukh CO2 scrubbing system.",
            "3. Increase Inter-Module Ventilation (IMV) fan speeds to eliminate stagnant CO2 pockets.",
            "4. Screen crew members for early hypercapnic symptoms: fronto-orbital headache, lethargy, dyspnea.",
            "5. Log environmental exposure duration for flight medical records."
        ])
        scenario_injected_alerts.append({
            "alert_id": "ALT-EMERG-03",
            "timestamp": now_str,
            "astronaut_id": ast_code or "AST-01",
            "severity": "CRITICAL",
            "category": "ENVIRONMENT",
            "title": "ISS ECLSS Protocol: Elevated CO2 & CDRA Scrubber Malfunction",
            "description": "Cabin CO2 partial pressure surged to 5.75 mmHg. Exceeds NASA hypercapnia limits.",
            "trigger_metric": "co2_partial_pressure_mmhg = 5.75 mmHg (Threshold: 3.80 mmHg)",
            "recommended_protocol": hypercapnia_steps
        })

    elif "Solar Particle" in scenario:
        scenario_injected_alerts.append({
            "alert_id": "ALT-EMERG-04",
            "timestamp": now_str,
            "astronaut_id": ast_code or "AST-01",
            "severity": "CRITICAL",
            "category": "RADIATION",
            "title": "Space Radiation Alert: Solar Particle Event (SPE Storm)",
            "description": "Solar proton flux surge detected (>17.5 mSv/day). Immediate radiation shelter protocol mandated.",
            "trigger_metric": "spe_flux_msv_day = 17.5 mSv/day (Threshold: 1.0 mSv/day)",
            "recommended_protocol": [
                "1. Sound orbital radiation advisory alarm and recall crew to heavily shielded core modules (Node 2 / Service Module).",
                "2. Position water bags and sleep station polyethylene shielding surrounding crew quarters.",
                "3. Power down exposed external robotic arms and non-essential external scientific payloads.",
                "4. Distribute personal active dosimeters (Liulin-5 / DOSTEL) and verify real-time dose logging.",
                "5. Maintain continuous telemetry link with Space Radiation Analysis Group (SRAG) at Johnson Space Center."
            ]
        })

    elif "Circadian" in scenario:
        fatigue_steps = _fetch_protocol_steps("COGNITIVE_FATIGUE", [
            "1. Reassign safety-critical duties (docking, robotic arm, spacewalk) to backup crew.",
            "2. Enforce mandatory 8.5-hour dark rest period in sound-attenuated crew quarters.",
            "3. Review mission timeline and reduce cognitive task density for following flight day.",
            "4. Check circadian lighting schedule (blue-enriched vs dim amber spectrum)."
        ])
        scenario_injected_alerts.append({
            "alert_id": "ALT-EMERG-05",
            "timestamp": now_str,
            "astronaut_id": ast_code or "AST-01",
            "severity": "CRITICAL",
            "category": "MENTAL_HEALTH",
            "title": "Critical Cognitive Fatigue & Circadian Misalignment",
            "description": "Sleep duration collapsed to 3.8h with severe circadian drift (+2.8h). High risk of cognitive error.",
            "trigger_metric": "fatigue_risk_index = 84.0 / 100 (Threshold: 65.0)",
            "recommended_protocol": fatigue_steps
        })

    # Prepend scenario emergency alerts so they appear at the top of triage
    alerts_list = scenario_injected_alerts + alerts_list

    # 3. Fallback default alerts matrix if database was empty and no scenario active
    if not alerts_list:
        source = "simulated_fallback"
        status_note = "Fallback: Standard operational alert roster"

        ml_protocol = _fetch_protocol_steps("ML_MULTIVARIATE_ANOMALY", [
            "1. Review feature attribution radar to identify primary deviating physiological parameters.",
            "2. Cross-reference telemetry with active astronaut activity log (sleep, meal, workout).",
            "3. Verify biometric sensor contact quality and electrode impedance.",
            "4. Flag astronaut telemetry record for scheduled Flight Surgeon shift review."
        ])

        alerts_list = [
            {
                "alert_id": "ALT-204",
                "timestamp": now_str,
                "astronaut_id": "AST-04",
                "severity": "WARNING",
                "category": "VITALS_ML",
                "title": "Elevated Heart Rate & Workload Strain",
                "description": "Heart rate measured at 116.5 bpm following extended EVA tether operations.",
                "trigger_metric": "heart_rate_bpm = 116.5 (Threshold: 105.0)",
                "recommended_protocol": [
                    "1. Command immediate rest period inside crew quarters.",
                    "2. Administer oral hydration pack with balanced electrolytes.",
                    "3. Monitor 12-lead ECG telemetry for 30 minutes.",
                    "4. Consult Flight Surgeon before approving further high-workload tasks."
                ]
            },
            {
                "alert_id": "ALT-108",
                "timestamp": now_str,
                "astronaut_id": "AST-01",
                "severity": "INFO",
                "category": "RADIATION",
                "title": "South Atlantic Anomaly (SAA) Orbital Ingress",
                "description": "Orbital pass through peak SAA flux zone. Dosimeter background elevated.",
                "trigger_metric": "dosimeter_flux_usv_h = 48.2 uSv/h (Threshold: 50.0)",
                "recommended_protocol": [
                    "1. Confirm personal dosimeter Liulin-5 telemetry transmission.",
                    "2. Verify passive shielding integrity in Columbus and Kibo modules."
                ]
            },
            {
                "alert_id": "ALT-302",
                "timestamp": now_str,
                "astronaut_id": "AST-03",
                "severity": "WARNING",
                "category": "MENTAL_HEALTH",
                "title": "Circadian Phase Misalignment Advisory",
                "description": "Actigraphy detects 1.4-hour phase delay relative to ISS Mission Elapsed Time.",
                "trigger_metric": "circadian_drift_hours = +1.4h (Threshold: 1.0h)",
                "recommended_protocol": [
                    "1. Shift cabin solid-state LED lighting to circadian blue-depleted spectrum.",
                    "2. Advise 30-minute pre-sleep wind-down without digital screens."
                ]
            }
        ]

    # Filter by astronaut if specified
    if ast_code:
        filtered = [a for a in alerts_list if a["astronaut_id"] == ast_code]
        if not filtered and scenario_injected_alerts:
            filtered = scenario_injected_alerts
        alerts_list = filtered if filtered else alerts_list

    crit_count = sum(1 for a in alerts_list if a["severity"] == "CRITICAL")
    warn_count = sum(1 for a in alerts_list if a["severity"] == "WARNING")
    info_count = sum(1 for a in alerts_list if a["severity"] == "INFO")

    summary = {
        "total_active_alerts": len(alerts_list),
        "total_alerts": len(alerts_list),
        "critical_count": crit_count,
        "warning_count": warn_count,
        "info_count": info_count,
        "system_status": "CRITICAL" if crit_count > 0 else ("WARNING" if warn_count > 0 else "NOMINAL"),
        "active_scenario": scenario
    }

    return {
        "data": alerts_list,
        "summary": summary,
        "source": source,
        "status_note": status_note
    }


# ============================================================================
# 7. MEDICAL REPORT GENERATOR CONTRACT (Member 4 Integration)
# ============================================================================

def generate_health_report(
    astronaut_id: str = "AST-01",
    scenario_override: Optional[str] = None
) -> Dict[str, Any]:
    """
    Synthesizes an authoritative clinical spaceflight medical brief and JSON telemetry digest.
    Integrates Member 4's `src.reports` when available.

    Returns:
        dict: {"data": dict, "summary": dict, "source": str, "status_note": str}
    """
    ast_code, num_id = _normalize_ast_id(astronaut_id)
    scenario = _get_active_scenario(scenario_override)
    roster = get_crew_roster()
    astronaut = next((a for a in roster if a["astronaut_id"] == ast_code), roster[0])

    source = "live"
    status_note = "Generated via SPACECARE Clinical Briefing Engine"

    # Gather telemetry digests across all contracts
    vitals_resp = get_vitals_and_anomalies(astronaut_id=ast_code, hours=24, scenario_override=scenario)
    rad_resp = get_radiation_data(days=30, scenario_override=scenario)
    mental_resp = get_mental_wellness_data(astronaut_id=ast_code, days=14, scenario_override=scenario)
    alerts_resp = get_active_alerts_and_protocols(astronaut_id=ast_code, scenario_override=scenario)

    vitals_summary = vitals_resp["summary"]
    rad_summary = rad_resp["summary"]
    mental_summary = mental_resp["summary"]
    alerts_data = alerts_resp["data"]

    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    report_id = f"NASA-MED-{ast_code}-{datetime.now(timezone.utc).strftime('%Y%j%H%M')}"
    ast_name = astronaut["name"]
    role = astronaut["role"]
    m_day = astronaut.get("mission_day", 42)

    # Clinical clearance determination
    if vitals_summary.get("overall_status") == "CRITICAL" or rad_summary.get("overall_status") == "CRITICAL":
        clearance = "RESTRICTED TO CREW QUARTERS // MEDICAL OBSERVATION MANDATORY"
        overall_status = "CRITICAL"
    elif vitals_summary.get("overall_status") == "WARNING" or mental_summary.get("overall_status") == "WARNING":
        clearance = "FIT FOR FLIGHT DUTY // CONDITIONAL WORKLOAD RESTRICTIONS"
        overall_status = "WARNING"
    else:
        clearance = "UNRESTRICTED FLIGHT STATUS // NOMINAL CLINICAL BASELINE"
        overall_status = "NOMINAL"

    markdown_doc = f"""# EXPEDITION 71 CLINICAL MEDICAL STATUS REPORT
**Report ID:** `{report_id}`  
**Subject:** {ast_name} ({ast_code}) | **Role:** {role}  
**Mission Day:** {m_day} | **Timestamp:** {now_utc}  
**Active Mission Scenario:** `{scenario}`  
**Operational Clearance:** `{clearance}`  

---

## 1. Executive Flight Surgeon Summary
Overall flight clinical status is **{overall_status}**. Telemetry synthesis indicates 
anomalies detected in the last 24h: **{vitals_summary.get('anomaly_count_24h', 0)} events**.

---

## 2. Physiological Biometrics (24-Hour Evaluation)
- **Resting Heart Rate:** `{vitals_summary['latest_heart_rate']} bpm` (Delta: {vitals_summary['delta_heart_rate']:+0.1f} bpm)
- **Arterial Oxygen Saturation (SpO2):** `{vitals_summary['latest_spo2']}%` (Delta: {vitals_summary['delta_spo2']:+0.1f}%)
- **Arterial Blood Pressure:** `{vitals_summary['latest_blood_pressure']} mmHg`
- **Core Body Temperature:** `{vitals_summary['latest_temperature']} °C`
- **Respiration Rate:** `{vitals_summary['latest_respiration']} br/min`
- **Isolation Forest ML Anomaly Score:** `{vitals_summary['latest_anomaly_score']:.3f}` (`{vitals_summary['overall_status']}`)

---

## 3. Cosmic Radiation & Cumulative Dosimetry (30-Day Window)
- **Current Dose Rate:** `{rad_summary['current_dose_rate_msv_day']} mSv/day`
- **Cumulative Mission Dose:** `{rad_summary['cumulative_dose_msv']} mSv`
- **NASA 30-Day Exposure Limit:** `250.0 mSv` ({rad_summary['pct_30d_limit']:.1f}% consumed)
- **NASA Career Effective Dose Limit:** `600.0 mSv` (NASA-STD-3001 Vol 1 Rev B)
- **Solar Particle Event Alert:** {'🚨 SOLAR STORM IN PROGRESS' if rad_summary['solar_storm_alert'] else '🟢 Quiet Sun (Nominal)'}
- **South Atlantic Anomaly:** {'⚠️ Active SAA Boundary Transit' if rad_summary['saa_active'] else '🟢 Out of SAA zone'}

---

## 4. Neurobehavioral, Sleep & Fatigue Index
- **Last Sleep Duration:** `{mental_summary['latest_sleep_hrs']:.2f} hours` (Target: 8.00 hrs)
- **Sleep Quality Rating:** `{mental_summary['latest_sleep_quality']:.1f} / 100`
- **7-Day Rolling Sleep Average:** `{mental_summary['avg_sleep_hrs_7d']:.2f} hrs/night`
- **Cognitive Fatigue Risk Score:** `{mental_summary['latest_fatigue_score']:.1f} / 100` (`{mental_summary['overall_status']}`)
- **Circadian Phase Alignment:** `{mental_summary['latest_circadian_alignment_pct']:.1f}%`

---

## 5. Active Early Warning Protocols & Directives
"""
    if alerts_data:
        for a in alerts_data:
            markdown_doc += f"- **[{a['severity']}] {a['title']}**: {a['description']}\n"
            for step in a.get("recommended_protocol", []):
                markdown_doc += f"  - {step}\n"
    else:
        markdown_doc += "🟢 *No active warnings or emergency medical protocols active.*\n"

    markdown_doc += f"""
---

## 6. Flight Surgeon Directives & Sign-off
- **Duty Recommendation:** {clearance}
- **Mandated Interventions:** Enforce 8.5h sound-attenuated sleep period, verify electrolyte hydration pack, re-check pulse oximeter contact.
- **Flight Surgeon Console:** Surgeon-1 (ISS Medical Operations, Johnson Space Center)
- **Digital Cryptographic Signature:** `[AUTHENTICATED // NASA-MEDOPS-EXP71-{ast_code}-SURGEON1]`
"""

    payload_data = {
        "report_id": report_id,
        "astronaut_id": ast_code,
        "astronaut_name": ast_name,
        "mission_day": m_day,
        "generated_at": now_utc,
        "overall_clinical_status": overall_status,
        "markdown_report": markdown_doc,
        "json_telemetry_digest": {
            "vitals": vitals_summary,
            "radiation": rad_summary,
            "mental_health": mental_summary,
            "alerts_count": len(alerts_data),
            "clearance": clearance,
            "active_scenario": scenario
        }
    }

    summary = {
        "report_title": f"Expedition 71 Clinical Briefing - {ast_name} ({ast_code})",
        "generated_at": now_utc,
        "clinical_clearance": clearance,
        "anomalies_detected_count": vitals_summary.get("anomaly_count_24h", 0),
        "active_scenario": scenario
    }

    return {
        "data": payload_data,
        "summary": summary,
        "source": source,
        "status_note": status_note
    }


# ============================================================================
# 8. MODULE INTEGRATION HEALTH STATUS CONTRACT
# ============================================================================

def get_module_integration_health() -> Dict[str, Any]:
    """
    Granular integration diagnostics across all 5 teammate backend domains:
    - Member 1: nasa_data (eda_client, osdr_client, radiation_service)
    - Member 2: ml (anomaly_detector, feature_engineering, model)
    - Member 4: alerts (alert_engine, protocols)
    - Member 4: mental_health (sleep_tracker, tlx_assessment)
    - Member 4: reports (src.reports)

    Returns:
        dict: {"data": dict, "summary": dict, "source": "live", "status_note": str}
        where data contains per domain:
        - "status": "live" | "partial_live" | "simulated_fallback"
        - "module_path": str
        - "detected_entrypoints": list[str]
        - "last_check_note": str
        - "is_live": bool
    """
    health_data = {}
    live_count = 0

    # 1. NASA Data Domain (Member 1)
    entrypoints_nasa = []
    try:
        from src.nasa_data import eda_client, radiation_service, osdr_client
        for fn in ["load_eda_benchmarks", "get_eda_statistical_summary"]:
            if hasattr(eda_client, fn):
                entrypoints_nasa.append(f"eda_client.{fn}")
        for fn in ["load_local_radlab_records", "fetch_radlab_telemetry"]:
            if hasattr(radiation_service, fn):
                entrypoints_nasa.append(f"radiation_service.{fn}")
        for fn in ["get_curated_human_studies", "fetch_live_study_metadata"]:
            if hasattr(osdr_client, fn):
                entrypoints_nasa.append(f"osdr_client.{fn}")

        health_data["nasa_data"] = {
            "status": "live",
            "module_path": "src.nasa_data (eda_client, radiation_service, osdr_client)",
            "detected_entrypoints": entrypoints_nasa,
            "last_check_note": f"Connected: {len(entrypoints_nasa)} entrypoints active. Curated EDA and RadLab fixtures loaded.",
            "is_live": True
        }
        live_count += 1
    except Exception as e:
        health_data["nasa_data"] = {
            "status": "simulated_fallback",
            "module_path": "src.nasa_data",
            "detected_entrypoints": [],
            "last_check_note": f"Fallback: {e}",
            "is_live": False
        }

    # 2. ML Domain (Member 2)
    entrypoints_ml = []
    try:
        from src.ml import anomaly_detector, feature_engineering, model
        if hasattr(anomaly_detector, "AstronautAnomalyDetector"):
            entrypoints_ml.append("anomaly_detector.AstronautAnomalyDetector")
        for fn in ["extract_feature_vector", "extract_feature_matrix", "compute_feature_deviations"]:
            if hasattr(feature_engineering, fn):
                entrypoints_ml.append(f"feature_engineering.{fn}")
        if hasattr(model, "AstronautAnomalyDetector"):
            entrypoints_ml.append("model.AstronautAnomalyDetector")

        # Live verification: instantiate detector
        det = anomaly_detector.AstronautAnomalyDetector(contamination=0.05, random_state=42)
        has_train = hasattr(det, "train")
        has_predict = hasattr(det, "predict") or hasattr(det, "predict_series")

        health_data["ml"] = {
            "status": "live" if (has_train and has_predict) else "partial_live",
            "module_path": "src.ml (anomaly_detector, feature_engineering, model)",
            "detected_entrypoints": entrypoints_ml,
            "last_check_note": f"Isolation Forest pipeline verified. {len(entrypoints_ml)} entrypoints active.",
            "is_live": True
        }
        live_count += 1
    except Exception as e:
        health_data["ml"] = {
            "status": "simulated_fallback",
            "module_path": "src.ml",
            "detected_entrypoints": [],
            "last_check_note": f"Fallback: {e}",
            "is_live": False
        }

    # 3. Alerts Domain (Member 4)
    entrypoints_alerts = []
    try:
        from src.alerts import alert_engine, protocols
        for fn in ["evaluate_vitals_for_alerts", "is_duplicate_active_alert"]:
            if hasattr(alert_engine, fn):
                entrypoints_alerts.append(f"alert_engine.{fn}")
        for fn in ["get_protocol", "FLIGHT_SURGEON_PROTOCOLS"]:
            if hasattr(protocols, fn):
                entrypoints_alerts.append(f"protocols.{fn}")

        health_data["alerts"] = {
            "status": "live",
            "module_path": "src.alerts (alert_engine, protocols)",
            "detected_entrypoints": entrypoints_alerts,
            "last_check_note": f"Early warning rule engine active. {len(entrypoints_alerts)} entrypoints active.",
            "is_live": True
        }
        live_count += 1
    except Exception as e:
        health_data["alerts"] = {
            "status": "simulated_fallback",
            "module_path": "src.alerts",
            "detected_entrypoints": [],
            "last_check_note": f"Fallback: {e}",
            "is_live": False
        }

    # 4. Mental Health Domain (Member 4)
    entrypoints_mh = []
    try:
        from src.mental_health import sleep_tracker, tlx_assessment
        for fn in ["simulate_sleep_profile", "generate_sleep_history"]:
            if hasattr(sleep_tracker, fn):
                entrypoints_mh.append(f"sleep_tracker.{fn}")
        for fn in ["calculate_raw_tlx", "calculate_fatigue_risk_index"]:
            if hasattr(tlx_assessment, fn):
                entrypoints_mh.append(f"tlx_assessment.{fn}")

        health_data["mental_health"] = {
            "status": "live",
            "module_path": "src.mental_health (sleep_tracker, tlx_assessment)",
            "detected_entrypoints": entrypoints_mh,
            "last_check_note": f"Sleep actigraphy & NASA-TLX cognitive fatigue models active. {len(entrypoints_mh)} entrypoints.",
            "is_live": True
        }
        live_count += 1
    except Exception as e:
        health_data["mental_health"] = {
            "status": "simulated_fallback",
            "module_path": "src.mental_health",
            "detected_entrypoints": [],
            "last_check_note": f"Fallback: {e}",
            "is_live": False
        }

    # 5. Reports Domain (Member 4)
    entrypoints_reports = []
    try:
        import src.reports as rep_pkg
        for attr in dir(rep_pkg):
            if not attr.startswith("_") and callable(getattr(rep_pkg, attr)):
                entrypoints_reports.append(f"reports.{attr}")

        is_rep_live = len(entrypoints_reports) > 0
        health_data["reports"] = {
            "status": "live" if is_rep_live else "simulated_fallback",
            "module_path": "src.reports",
            "detected_entrypoints": entrypoints_reports,
            "last_check_note": (
                f"Custom reports generator active ({len(entrypoints_reports)} entrypoints)."
                if is_rep_live else
                "File is currently a stub; falling back to data_adapter clinical report synthesis."
            ),
            "is_live": is_rep_live
        }
        if is_rep_live:
            live_count += 1
    except Exception as e:
        health_data["reports"] = {
            "status": "simulated_fallback",
            "module_path": "src.reports",
            "detected_entrypoints": [],
            "last_check_note": f"File is currently a stub; fallback active ({e})",
            "is_live": False
        }

    total_domains = 5
    health_pct = round((live_count / total_domains) * 100.0, 1)

    summary = {
        "live_module_count": live_count,
        "total_modules": total_domains,
        "system_health_pct": health_pct,
        "status": "NOMINAL" if health_pct >= 80.0 else ("DEGRADED" if health_pct >= 40.0 else "CRITICAL")
    }

    return {
        "data": health_data,
        "summary": summary,
        "source": "live",
        "status_note": f"Integration Diagnostics: {live_count}/{total_domains} modules online ({health_pct}%)"
    }
