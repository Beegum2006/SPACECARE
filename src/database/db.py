"""
SPACECARE Database Layer
Manages SQLite database connection, table initialization, and crew roster seeding.
"""

import sqlite3
import os
from pathlib import Path
from typing import Optional

# Database path resolution: data/spacecare.db relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_DIR = PROJECT_ROOT / "data"
DB_PATH = DB_DIR / "spacecare.db"


def get_db_connection() -> sqlite3.Connection:
    """Returns a SQLite connection with Row factory enabled for dictionary-like access."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_database() -> None:
    """Initializes the SQLite schema and seeds default astronaut roster if empty."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Astronauts Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS astronauts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            callsign TEXT NOT NULL,
            role TEXT NOT NULL,
            agency TEXT DEFAULT 'NASA',
            mission TEXT DEFAULT 'Expedition 71 / ISS',
            age INTEGER DEFAULT 42,
            baseline_hr REAL DEFAULT 70.0,
            baseline_spo2 REAL DEFAULT 98.0,
            baseline_bp_sys REAL DEFAULT 118.0,
            baseline_bp_dia REAL DEFAULT 76.0,
            baseline_temp REAL DEFAULT 36.8,
            baseline_rr REAL DEFAULT 14.0,
            baseline_hrv REAL DEFAULT 55.0,
            status TEXT DEFAULT 'NOMINAL',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 2. Vitals Telemetry Logs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vitals_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            astronaut_id INTEGER NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            heart_rate REAL NOT NULL,
            blood_pressure_sys REAL NOT NULL,
            blood_pressure_dia REAL NOT NULL,
            spo2 REAL NOT NULL,
            core_temperature REAL NOT NULL,
            respiration_rate REAL NOT NULL,
            hrv_rmssd REAL NOT NULL,
            ecg_status TEXT DEFAULT 'NORMAL_SINUS',
            is_simulated INTEGER DEFAULT 1,
            anomaly_score REAL DEFAULT 0.0,
            anomaly_flag INTEGER DEFAULT 0,
            FOREIGN KEY (astronaut_id) REFERENCES astronauts(id) ON DELETE CASCADE
        );
    """)

    # 3. ISS Environmental Logs (ECLSS)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS environmental_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            cabin_pressure_psi REAL NOT NULL,
            co2_partial_pressure_mmhg REAL NOT NULL,
            o2_percentage REAL NOT NULL,
            temperature_celsius REAL NOT NULL,
            relative_humidity_pct REAL NOT NULL,
            radiation_level_usv_h REAL DEFAULT 22.5,
            module_name TEXT DEFAULT 'Destiny Laboratory (US Lab)',
            is_simulated INTEGER DEFAULT 1
        );
    """)

    # 4. Space Radiation Logs (Real NASA OSDR / RAD telemetry)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS radiation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            dose_rate_usv_h REAL NOT NULL,
            cumulative_dose_msv REAL NOT NULL,
            detector TEXT DEFAULT 'Liulin-5 / RAD',
            location TEXT DEFAULT 'ISS Columbus Orbital Facility',
            dataset_source TEXT NOT NULL,
            nasa_id TEXT,
            is_simulated INTEGER DEFAULT 0
        );
    """)

    # 5. Mental Health & Cognitive Load Logs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mental_health_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            astronaut_id INTEGER NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            sleep_duration_hours REAL NOT NULL,
            sleep_efficiency_pct REAL NOT NULL,
            circadian_drift_hours REAL NOT NULL,
            nasa_tlx_mental REAL NOT NULL,
            nasa_tlx_physical REAL NOT NULL,
            nasa_tlx_temporal REAL NOT NULL,
            nasa_tlx_performance REAL NOT NULL,
            nasa_tlx_effort REAL NOT NULL,
            nasa_tlx_frustration REAL NOT NULL,
            overall_tlx_score REAL NOT NULL,
            fatigue_risk_index REAL NOT NULL,
            stress_level TEXT DEFAULT 'Normal',
            mood_rating REAL DEFAULT 7.0,
            social_connection_score REAL DEFAULT 8.0,
            notes TEXT,
            FOREIGN KEY (astronaut_id) REFERENCES astronauts(id) ON DELETE CASCADE
        );
    """)

    # 6. Early Warning Alerts & Protocols Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            astronaut_id INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            severity TEXT NOT NULL,
            category TEXT NOT NULL,
            source TEXT DEFAULT 'RULE_ENGINE',
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            metric_name TEXT,
            metric_value REAL,
            threshold_limit REAL,
            flight_surgeon_protocol TEXT NOT NULL,
            is_acknowledged INTEGER DEFAULT 0,
            acknowledged_at DATETIME,
            FOREIGN KEY (astronaut_id) REFERENCES astronauts(id) ON DELETE SET NULL
        );
    """)

    # 7. Health & Mission Reports Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS health_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            astronaut_id INTEGER NOT NULL,
            generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            report_title TEXT NOT NULL,
            mission_day INTEGER DEFAULT 42,
            overall_status TEXT DEFAULT 'FLIGHT_READY',
            executive_summary TEXT,
            vitals_summary_json TEXT,
            anomalies_detected_count INTEGER DEFAULT 0,
            radiation_accumulated_msv REAL DEFAULT 0.0,
            recommendations TEXT,
            medical_disclaimer_signed INTEGER DEFAULT 1,
            FOREIGN KEY (astronaut_id) REFERENCES astronauts(id) ON DELETE CASCADE
        );
    """)

    # Indexes for fast historical queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_vitals_ast_time ON vitals_logs(astronaut_id, timestamp);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_env_time ON environmental_logs(timestamp);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_time ON alerts(timestamp);")

    # Safe Idempotent Migrations for Phase 4 fields
    for migration_sql in [
        "ALTER TABLE mental_health_logs ADD COLUMN mood_rating REAL DEFAULT 7.0;",
        "ALTER TABLE mental_health_logs ADD COLUMN social_connection_score REAL DEFAULT 8.0;",
        "ALTER TABLE alerts ADD COLUMN source TEXT DEFAULT 'RULE_ENGINE';"
    ]:
        try:
            cursor.execute(migration_sql)
        except sqlite3.OperationalError:
            pass  # Column already exists in existing database

    conn.commit()

    # Seed default astronaut crew if empty
    cursor.execute("SELECT COUNT(*) FROM astronauts;")
    if cursor.fetchone()[0] == 0:
        seed_astronauts(conn)

    conn.close()


def seed_astronauts(conn: sqlite3.Connection) -> None:
    """Seeds the 4-member ISS Expedition 71 crew roster."""
    astronauts = [
        (
            "Dr. Elena Vance",
            "Aegis",
            "Commander",
            "NASA",
            "Expedition 71 / ISS",
            44,
            68.0,
            98.5,
            116.0,
            74.0,
            36.7,
            13.5,
            58.0,
            "NOMINAL"
        ),
        (
            "Marcus 'Orion' Cole",
            "Vanguard",
            "Flight Engineer 1",
            "NASA",
            "Expedition 71 / ISS",
            39,
            72.0,
            98.0,
            120.0,
            78.0,
            36.8,
            14.0,
            52.0,
            "NOMINAL"
        ),
        (
            "Dr. Aisha Patel",
            "Caduceus",
            "Flight Engineer 2 / Medical Officer",
            "NASA",
            "Expedition 71 / ISS",
            41,
            64.0,
            99.0,
            114.0,
            72.0,
            36.6,
            13.0,
            62.0,
            "NOMINAL"
        ),
        (
            "Kaito 'Nova' Tanaka",
            "Cosmos",
            "Mission Specialist",
            "JAXA / NASA Partner",
            "Expedition 71 / ISS",
            36,
            75.0,
            97.8,
            122.0,
            80.0,
            36.9,
            15.0,
            49.0,
            "NOMINAL"
        ),
    ]

    cursor = conn.cursor()
    cursor.executemany("""
        INSERT INTO astronauts (
            name, callsign, role, agency, mission, age,
            baseline_hr, baseline_spo2, baseline_bp_sys, baseline_bp_dia,
            baseline_temp, baseline_rr, baseline_hrv, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, astronauts)
    conn.commit()


if __name__ == "__main__":
    init_database()
    print("SPACECARE database schema initialized and crew roster seeded successfully.")
