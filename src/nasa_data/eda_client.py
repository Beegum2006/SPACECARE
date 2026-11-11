"""
SPACECARE NASA Environmental Data Application (EDA) Client
Provides reference baseline comparisons derived from published NASA ISS ECLSS engineering specifications.

AUDIT NOTICE:
The local CSV dataset in data/sample_nasa/eda_iss_environment.csv is a CURATED REFERENCE FIXTURE
calibrated to published NASA ECLSS operational specifications (NASA-STD-3001). It is not an unedited
raw tabular export directly downloaded from the live NASA EDA database.
"""

import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SAMPLE_DATA_DIR = PROJECT_ROOT / "data" / "sample_nasa"
LOCAL_EDA_CSV = SAMPLE_DATA_DIR / "eda_iss_environment.csv"


def load_eda_benchmarks() -> pd.DataFrame:
    """Loads curated NASA ISS ECLSS engineering baseline reference records into a DataFrame."""
    if not LOCAL_EDA_CSV.exists():
        return pd.DataFrame()
    try:
        df = pd.read_csv(LOCAL_EDA_CSV)
        df["is_real_nasa_data"] = False  # Explicitly marked as reference engineering fixture
        df["provenance"] = "NASA ECLSS Engineering Baseline Reference Fixture"
        return df
    except Exception as e:
        logger.error(f"Error loading EDA reference fixture: {e}")
        return pd.DataFrame()


def get_eda_statistical_summary() -> Dict[str, Any]:
    """Computes reference statistical distributions from ISS ECLSS engineering specifications."""
    df = load_eda_benchmarks()
    if df.empty:
        return {}

    metrics = [
        ("cabin_pressure_psi", "psi"),
        ("co2_partial_pressure_mmhg", "mmHg"),
        ("o2_percentage", "%"),
        ("temperature_celsius", "°C"),
        ("relative_humidity_pct", "%")
    ]

    summary = {}
    for col, unit in metrics:
        if col in df.columns:
            summary[col] = {
                "unit": unit,
                "mean": round(float(df[col].mean()), 2),
                "std": round(float(df[col].std()), 2),
                "min": round(float(df[col].min()), 2),
                "max": round(float(df[col].max()), 2)
            }

    return summary


def compare_reading_against_eda(reading: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compares a given telemetry reading against NASA ISS ECLSS reference ranges.
    Returns deviation analysis and status.
    """
    stats = get_eda_statistical_summary()
    if not stats:
        return {"status": "UNKNOWN", "details": {}}

    comparison = {}
    is_aligned = True

    checks = [
        ("cabin_pressure_psi", reading.get("cabin_pressure_psi")),
        ("co2_partial_pressure_mmhg", reading.get("co2_partial_pressure_mmhg")),
        ("o2_percentage", reading.get("o2_percentage")),
        ("temperature_celsius", reading.get("temperature_celsius")),
        ("relative_humidity_pct", reading.get("relative_humidity_pct"))
    ]

    for col, val in checks:
        if val is not None and col in stats:
            ref = stats[col]
            within_bounds = ref["min"] - (2 * ref["std"]) <= val <= ref["max"] + (2 * ref["std"])
            diff_from_mean = round(val - ref["mean"], 2)
            comparison[col] = {
                "value": val,
                "nasa_mean": ref["mean"],
                "unit": ref["unit"],
                "difference": diff_from_mean,
                "within_nasa_bounds": within_bounds
            }
            if not within_bounds:
                is_aligned = False

    return {
        "is_aligned_with_nasa_baseline": is_aligned,
        "details": comparison
    }
