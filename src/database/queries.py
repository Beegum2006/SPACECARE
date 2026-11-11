"""
SPACECARE Database Queries
Data access layer for Astronaut Roster, Vitals, Environment, Alerts, and Reports.
Supports dynamic crew configuration (add, update, delete crew members).
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from src.database.db import get_db_connection


# ============================================================================
# Astronaut Crew Management (Dynamic & Configurable)
# ============================================================================

def get_astronauts(include_all: bool = True) -> List[Dict[str, Any]]:
    """Fetches all registered astronauts."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM astronauts ORDER BY id ASC;")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_astronaut_by_id(astronaut_id: int) -> Optional[Dict[str, Any]]:
    """Fetches a specific astronaut profile by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM astronauts WHERE id = ?;", (astronaut_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def add_astronaut(
    name: str,
    callsign: str,
    role: str,
    agency: str = "NASA",
    mission: str = "Expedition 71 / ISS",
    age: int = 40,
    baseline_hr: float = 70.0,
    baseline_spo2: float = 98.0,
    baseline_bp_sys: float = 118.0,
    baseline_bp_dia: float = 76.0,
    baseline_temp: float = 36.8,
    baseline_rr: float = 14.0,
    baseline_hrv: float = 55.0,
    status: str = "NOMINAL"
) -> int:
    """Adds a new astronaut to the active mission crew roster."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO astronauts (
            name, callsign, role, agency, mission, age,
            baseline_hr, baseline_spo2, baseline_bp_sys, baseline_bp_dia,
            baseline_temp, baseline_rr, baseline_hrv, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        name, callsign, role, agency, mission, age,
        baseline_hr, baseline_spo2, baseline_bp_sys, baseline_bp_dia,
        baseline_temp, baseline_rr, baseline_hrv, status
    ))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id


def update_astronaut(astronaut_id: int, **kwargs) -> bool:
    """Updates fields of an existing astronaut."""
    if not kwargs:
        return False
    conn = get_db_connection()
    cursor = conn.cursor()
    fields = [f"{k} = ?" for k in kwargs.keys()]
    values = list(kwargs.values()) + [astronaut_id]
    cursor.execute(f"UPDATE astronauts SET {', '.join(fields)} WHERE id = ?;", values)
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success


def delete_astronaut(astronaut_id: int) -> bool:
    """Removes an astronaut from the crew roster."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM astronauts WHERE id = ?;", (astronaut_id,))
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success


# ============================================================================
# Vitals Logging & Retrieval
# ============================================================================

def log_vitals(
    astronaut_id: int,
    heart_rate: float,
    blood_pressure_sys: float,
    blood_pressure_dia: float,
    spo2: float,
    core_temperature: float,
    respiration_rate: float,
    hrv_rmssd: float,
    ecg_status: str = "NORMAL_SINUS",
    is_simulated: int = 1,
    anomaly_score: float = 0.0,
    anomaly_flag: int = 0
) -> int:
    """Records a single vital signs snapshot."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO vitals_logs (
            astronaut_id, heart_rate, blood_pressure_sys, blood_pressure_dia,
            spo2, core_temperature, respiration_rate, hrv_rmssd,
            ecg_status, is_simulated, anomaly_score, anomaly_flag
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        astronaut_id, heart_rate, blood_pressure_sys, blood_pressure_dia,
        spo2, core_temperature, respiration_rate, hrv_rmssd,
        ecg_status, is_simulated, anomaly_score, anomaly_flag
    ))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id


def get_latest_vitals(astronaut_id: int) -> Optional[Dict[str, Any]]:
    """Returns the most recent vital sign entry for an astronaut."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM vitals_logs 
        WHERE astronaut_id = ? 
        ORDER BY timestamp DESC, id DESC LIMIT 1;
    """, (astronaut_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_vitals_history(astronaut_id: int, limit: int = 100) -> List[Dict[str, Any]]:
    """Returns historical vitals for plotting time series."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM vitals_logs 
        WHERE astronaut_id = ? 
        ORDER BY timestamp DESC, id DESC LIMIT ?;
    """, (astronaut_id, limit))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return list(reversed(rows))


# ============================================================================
# ISS Environmental Life Support (ECLSS) Logs
# ============================================================================

def log_environment(
    cabin_pressure_psi: float,
    co2_partial_pressure_mmhg: float,
    o2_percentage: float,
    temperature_celsius: float,
    relative_humidity_pct: float,
    radiation_level_usv_h: float = 22.5,
    module_name: str = "Destiny Laboratory (US Lab)",
    is_simulated: int = 1
) -> int:
    """Logs ISS environmental telemetry."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO environmental_logs (
            cabin_pressure_psi, co2_partial_pressure_mmhg, o2_percentage,
            temperature_celsius, relative_humidity_pct, radiation_level_usv_h,
            module_name, is_simulated
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        cabin_pressure_psi, co2_partial_pressure_mmhg, o2_percentage,
        temperature_celsius, relative_humidity_pct, radiation_level_usv_h,
        module_name, is_simulated
    ))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id


def get_latest_environment() -> Optional[Dict[str, Any]]:
    """Returns the most recent ISS environmental reading."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM environmental_logs ORDER BY timestamp DESC, id DESC LIMIT 1;")
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_environment_history(limit: int = 100) -> List[Dict[str, Any]]:
    """Returns historical ISS environmental telemetry."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM environmental_logs ORDER BY timestamp DESC, id DESC LIMIT ?;", (limit,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return list(reversed(rows))


# ============================================================================
# Mental Health & Cognitive Load Logs
# ============================================================================

def log_mental_health(
    astronaut_id: int,
    sleep_duration_hours: float,
    sleep_efficiency_pct: float,
    circadian_drift_hours: float,
    nasa_tlx_mental: float,
    nasa_tlx_physical: float,
    nasa_tlx_temporal: float,
    nasa_tlx_performance: float,
    nasa_tlx_effort: float,
    nasa_tlx_frustration: float,
    overall_tlx_score: float,
    fatigue_risk_index: float,
    stress_level: str = "Normal",
    mood_rating: float = 7.0,
    social_connection_score: float = 8.0,
    notes: str = ""
) -> int:
    """Logs a mental health & cognitive load evaluation record."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO mental_health_logs (
            astronaut_id, sleep_duration_hours, sleep_efficiency_pct,
            circadian_drift_hours, nasa_tlx_mental, nasa_tlx_physical,
            nasa_tlx_temporal, nasa_tlx_performance, nasa_tlx_effort,
            nasa_tlx_frustration, overall_tlx_score, fatigue_risk_index,
            stress_level, mood_rating, social_connection_score, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        astronaut_id, sleep_duration_hours, sleep_efficiency_pct,
        circadian_drift_hours, nasa_tlx_mental, nasa_tlx_physical,
        nasa_tlx_temporal, nasa_tlx_performance, nasa_tlx_effort,
        nasa_tlx_frustration, overall_tlx_score, fatigue_risk_index,
        stress_level, mood_rating, social_connection_score, notes
    ))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id


def get_mental_health_history(astronaut_id: int, limit: int = 30) -> List[Dict[str, Any]]:
    """Returns historical mental health logs for an astronaut."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM mental_health_logs 
        WHERE astronaut_id = ? 
        ORDER BY timestamp DESC, id DESC LIMIT ?;
    """, (astronaut_id, limit))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return list(reversed(rows))


# ============================================================================
# Alerts & Early Warning Management
# ============================================================================

def create_alert(
    severity: str,
    category: str,
    title: str,
    message: str,
    flight_surgeon_protocol: str,
    astronaut_id: Optional[int] = None,
    metric_name: Optional[str] = None,
    metric_value: Optional[float] = None,
    threshold_limit: Optional[float] = None,
    source: str = "RULE_ENGINE"
) -> int:
    """Creates a new early warning alert."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO alerts (
            astronaut_id, severity, category, source, title, message,
            metric_name, metric_value, threshold_limit, flight_surgeon_protocol
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        astronaut_id, severity, category, source, title, message,
        metric_name, metric_value, threshold_limit, flight_surgeon_protocol
    ))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id


def get_active_alerts(limit: int = 20) -> List[Dict[str, Any]]:
    """Returns unacknowledged alerts sorted by severity and timestamp."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.*, ast.name as astronaut_name, ast.callsign
        FROM alerts a
        LEFT JOIN astronauts ast ON a.astronaut_id = ast.id
        WHERE a.is_acknowledged = 0
        ORDER BY 
            CASE a.severity
                WHEN 'CRITICAL' THEN 1
                WHEN 'WARNING' THEN 2
                WHEN 'ADVISORY' THEN 3
                ELSE 4
            END,
            a.timestamp DESC
        LIMIT ?;
    """, (limit,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def acknowledge_alert(alert_id: int) -> bool:
    """Marks an alert as acknowledged by Flight Surgeon / Operator."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE alerts 
        SET is_acknowledged = 1, acknowledged_at = CURRENT_TIMESTAMP 
        WHERE id = ?;
    """, (alert_id,))
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success


# ============================================================================
# Health Reports
# ============================================================================

def save_health_report(
    astronaut_id: int,
    report_title: str,
    mission_day: int,
    overall_status: str,
    executive_summary: str,
    vitals_summary_json: str,
    anomalies_detected_count: int,
    radiation_accumulated_msv: float,
    recommendations: str
) -> int:
    """Saves a generated health report to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO health_reports (
            astronaut_id, report_title, mission_day, overall_status,
            executive_summary, vitals_summary_json, anomalies_detected_count,
            radiation_accumulated_msv, recommendations
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        astronaut_id, report_title, mission_day, overall_status,
        executive_summary, vitals_summary_json, anomalies_detected_count,
        radiation_accumulated_msv, recommendations
    ))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id


def get_reports_for_astronaut(astronaut_id: int) -> List[Dict[str, Any]]:
    """Retrieves all reports generated for an astronaut."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM health_reports 
        WHERE astronaut_id = ? 
        ORDER BY generated_at DESC;
    """, (astronaut_id,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows
