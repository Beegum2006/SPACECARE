"""
SPACECARE Mental Health - NASA Task Load Index (NASA-TLX) Calculator
Standard aerospace assessment tool for evaluating cognitive workload and fatigue risk.

DISCLAIMER: All calculations are SYNTHETIC educational & systems engineering models.
"""

from typing import Dict, Any, Tuple


def calculate_raw_tlx(
    mental: float,
    physical: float,
    temporal: float,
    performance: float,
    effort: float,
    frustration: float
) -> float:
    """
    Calculates the Raw NASA-TLX score (unweighted arithmetic mean of the 6 subscales).
    Range: 0 (minimal workload) to 100 (extreme mental/physical strain).
    """
    scores = [mental, physical, temporal, performance, effort, frustration]
    return float(round(sum(scores) / len(scores), 2))


def calculate_fatigue_risk_index(
    tlx_score: float,
    sleep_duration_hours: float,
    sleep_efficiency_pct: float,
    circadian_drift_hours: float
) -> Tuple[float, str]:
    """
    Computes an integrated Aerospace Fatigue Risk Index (0 - 100) and risk category.
    
    Formula weights:
    - TLX Workload (40%)
    - Sleep Duration Deficit (35%)
    - Sleep Inefficiency (15%)
    - Circadian Phase Misalignment (10%)
    """
    # 1. TLX component (0 - 40 points)
    tlx_component = (tlx_score / 100.0) * 40.0

    # 2. Sleep deficit component: baseline target is 8.0 hours
    sleep_deficit = max(0.0, 8.0 - sleep_duration_hours)
    sleep_component = min(35.0, (sleep_deficit / 3.5) * 35.0)

    # 3. Sleep efficiency component: baseline target is 90%
    inefficiency = max(0.0, 90.0 - sleep_efficiency_pct)
    efficiency_component = min(15.0, (inefficiency / 30.0) * 15.0)

    # 4. Circadian phase drift component (absolute hours from normal schedule)
    drift_component = min(
    10.0,
    (abs(circadian_drift_hours) / 2.5) * 10.0
)
    total_risk = round(tlx_component + sleep_component + efficiency_component + drift_component, 1)
    total_risk = max(0.0, min(100.0, total_risk))

    if total_risk < 35.0:
        category = "LOW_RISK"
    elif total_risk < 65.0:
        category = "MODERATE_RISK"
    else:
        category = "HIGH_RISK"

    return total_risk, category
