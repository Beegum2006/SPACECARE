"""
SPACECARE NASA RadLab Radiation Service
Interfaces with the NASA OSDR RadLab Data API for authentic cosmic radiation
dosimetry measurements (Liulin-5, DOSTEL, TEPC) collected aboard the ISS.

AUDIT & REGULATORY CITATIONS:
- NASA-STD-3001 Volume 1, Rev B (Standard for Spaceflight Human-System Standard: Crew Health)
  mandates a universal 600 mSv career effective dose limit based on 3% REID at 95% CL.
- Effective dose (E) calculation requires organ weighting factors (w_T) and radiation quality (Q).
- Operational ambient dose equivalent H*(10) is tracked here as an aerospace operational approximation.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import requests

from src.database.db import get_db_connection

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SAMPLE_DATA_DIR = PROJECT_ROOT / "data" / "sample_nasa"
LOCAL_RADLAB_CACHE = SAMPLE_DATA_DIR / "radlab_iss_dosimetry.json"

RADLAB_BASE_API = "https://visualization.osdr.nasa.gov/radlab/api"

# Authoritative Standards & Guidelines
NASA_RADIATION_STANDARDS = {
    "career_effective_dose_limit_msv": 600.0,  # NASA-STD-3001 Vol 1, Rev B (Universal 3% REID at 95% CL)
    "ncrp_132_30_day_advisory_msv": 100.0,    # NCRP Report 132 operational benchmark for blood-forming organs
    "saa_elevation_threshold_usv_h": 50.0      # Operational telemetry heuristic indicating South Atlantic Anomaly passage
}


def load_local_radlab_records() -> List[Dict[str, Any]]:
    """Loads curated reference test fixtures calibrated to published ISS Liulin-5 & DOSTEL data."""
    if not LOCAL_RADLAB_CACHE.exists():
        return []
    try:
        with open(LOCAL_RADLAB_CACHE, "r", encoding="utf-8") as f:
            records = json.load(f)
        for r in records:
            r["is_real_nasa_data"] = False  # Explicitly marked as reference fixture
            r["provenance"] = "NASA RadLab Reference Test Fixture (Calibrated to Published Ranges)"
        return records
    except Exception as e:
        logger.error(f"Error loading RadLab reference fixture: {e}")
        return []


def fetch_radlab_telemetry(
    spacecraft: str = "ISS",
    module: Optional[str] = None,
    limit: int = 20,
    timeout_sec: int = 5
) -> Tuple[List[Dict[str, Any]], bool]:
    """
    Retrieves radiation telemetry.
    Attempts live query to the official NASA RadLab Data API.
    Falls back to local calibrated reference fixtures if the government server times out.
    
    Returns:
        (records_list, is_live_api_boolean)
    """
    params = {"spacecraft": spacecraft, "trajectory": "LEO"}
    if module:
        params["module"] = module

    try:
        response = requests.get(
            RADLAB_BASE_API,
            params=params,
            timeout=timeout_sec,
            headers={"User-Agent": "SPACECARE-Radiation-Monitor/1.0"}
        )
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                formatted = []
                for item in data[:limit]:
                    formatted.append({
                        "timestamp": item.get("timestamp", ""),
                        "spacecraft": item.get("spacecraft", spacecraft),
                        "trajectory": item.get("trajectory", "LEO"),
                        "module": item.get("module", "US Lab"),
                        "instrument": item.get("instrument", "Liulin-5"),
                        "instrument_family": item.get("instrument_family", "Dosimeter"),
                        "absorbed_dose_rate_ugy_h": float(item.get("absorbed_dose_rate", 15.0)),
                        "dose_equivalent_rate_usv_h": float(item.get("dose_equivalent_rate", 24.0)),
                        "flux_cm2_sr_s": float(item.get("flux", 2.0)),
                        "celestial_body": item.get("celestial_body", "Earth"),
                        "is_real_nasa_data": True,  # Genuine live API response
                        "provenance": "NASA RadLab Data API (Verified Live Response)"
                    })
                return formatted, True
    except Exception as e:
        logger.info(f"Live RadLab API call timed out or failed ({e}); utilizing local calibrated reference fixtures.")

    # Fallback to local calibrated reference fixtures
    cached = load_local_radlab_records()
    if module:
        cached = [r for r in cached if module.lower() in r.get("module", "").lower()]
    return cached[:limit], False


def sync_radlab_records_to_db(records: List[Dict[str, Any]]) -> int:
    """
    Persists radiation records into the SQLite database radiation_logs table.
    Sets is_simulated = 0 ONLY if records are verified live API responses;
    otherwise sets is_simulated = 1 for local reference fixtures to preserve provenance integrity.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    inserted = 0

    running_cumulative_msv = 0.0

    for r in records:
        dose_rate = float(r.get("dose_equivalent_rate_usv_h", 24.0))
        # Operational approximation: multiplying hourly equivalent rate by assumed 4-hour window
        running_cumulative_msv += (dose_rate * 4.0) / 1000.0

        is_real = bool(r.get("is_real_nasa_data", False))
        is_simulated_flag = 0 if is_real else 1

        cursor.execute("""
            INSERT INTO radiation_logs (
                timestamp, dose_rate_usv_h, cumulative_dose_msv,
                detector, location, dataset_source, nasa_id, is_simulated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            r.get("timestamp"),
            dose_rate,
            round(running_cumulative_msv, 3),
            r.get("instrument", "Liulin-5 / DOSTEL"),
            r.get("module", "ISS Orbital Complex"),
            r.get("provenance", "NASA RadLab Reference Fixture"),
            "RADLAB-ISS-EXP71",
            is_simulated_flag
        ))
        inserted += 1

    conn.commit()
    conn.close()
    return inserted


def calculate_radiation_summary(records: List[Dict[str, Any]], mission_days: int = 42) -> Dict[str, Any]:
    """
    Calculates operational dosimetry statistics and evaluates against NASA-STD-3001 Vol 1 Rev B.
    
    NOTE: Multiplying ambient dose equivalent rate by hours yields an operational ambient dose
    equivalent H*(10) estimate in mSv, not a clinical effective dose (E) calculation.
    """
    if not records:
        return {
            "avg_dose_rate_usv_h": 0.0,
            "avg_absorbed_rate_ugy_h": 0.0,
            "peak_dose_rate_usv_h": 0.0,
            "estimated_cumulative_msv": 0.0,
            "pct_career_limit": 0.0,
            "pct_30_day_limit": 0.0,
            "status": "NOMINAL",
            "citation": "NASA-STD-3001 Vol 1 Rev B"
        }

    eq_rates = [r.get("dose_equivalent_rate_usv_h", 0.0) for r in records]
    ab_rates = [r.get("absorbed_dose_rate_ugy_h", 0.0) for r in records]

    avg_eq = sum(eq_rates) / len(eq_rates)
    avg_ab = sum(ab_rates) / len(ab_rates)
    peak_eq = max(eq_rates)

    # Operational estimate: avg_uSv_h * 24 hours * days / 1000 = mSv ambient equivalent
    cumulative_msv = (avg_eq * 24.0 * mission_days) / 1000.0

    career_limit = NASA_RADIATION_STANDARDS["career_effective_dose_limit_msv"]
    acute_limit = NASA_RADIATION_STANDARDS["ncrp_132_30_day_advisory_msv"]
    saa_threshold = NASA_RADIATION_STANDARDS["saa_elevation_threshold_usv_h"]

    pct_career = (cumulative_msv / career_limit) * 100.0
    pct_30d = (cumulative_msv / acute_limit) * 100.0

    if pct_30d > 80.0 or pct_career > 80.0:
        status = "CRITICAL"
    elif pct_30d > 50.0 or pct_career > 50.0:
        status = "WARNING"
    elif peak_eq >= saa_threshold:
        status = "ELEVATED_SAA"
    else:
        status = "NOMINAL"

    return {
        "avg_dose_rate_usv_h": round(avg_eq, 2),
        "avg_absorbed_rate_ugy_h": round(avg_ab, 2),
        "peak_dose_rate_usv_h": round(peak_eq, 2),
        "estimated_cumulative_msv": round(cumulative_msv, 2),
        "pct_career_limit": round(pct_career, 1),
        "pct_30_day_limit": round(pct_30d, 1),
        "status": status,
        "citation": "NASA-STD-3001 Vol 1 Rev B (600 mSv Career PEL)"
    }
