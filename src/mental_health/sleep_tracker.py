"""
SPACECARE Mental Health & Behavioral Monitoring - Sleep & Circadian Tracker
Simulates astronaut sleep architecture, circadian rhythm desynchronosis,
and orbital night-day cycle impact.

DISCLAIMER: All calculations are SYNTHETIC behavioral models for aerospace systems simulation.
"""

import numpy as np
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional


def simulate_sleep_profile(
    astronaut_id: int,
    base_hours: float = 7.2,
    circadian_phase_offset_hours: float = 0.5,
    sleep_efficiency_pct: float = 88.0
) -> Dict[str, Any]:
    """
    Simulates a sleep architecture record for an astronaut aboard the ISS.
    
    The ISS experiences 16 sunrises and sunsets every 24 hours (90-minute orbital period),
    which induces circadian misalignment without strict cabin lighting protocols.
    """
    # Introduce small realistic drift
    actual_duration = float(np.clip(base_hours + np.random.normal(0, 0.4), 4.5, 9.5))
    actual_efficiency = float(np.clip(sleep_efficiency_pct + np.random.normal(0, 2.5), 60.0, 98.0))
    drift = float(np.clip(circadian_phase_offset_hours + np.random.normal(0, 0.2), -3.0, 3.0))

    # Sleep stage breakdown (% of total sleep)
    rem_pct = float(np.clip(22.0 + np.random.normal(0, 2.0), 15.0, 30.0))
    deep_pct = float(np.clip(18.0 + np.random.normal(0, 2.0) - (abs(drift) * 1.5), 10.0, 25.0))
    light_pct = 100.0 - rem_pct - deep_pct
    # Calculate sleep debt compared to 8.0 hr baseline target
    sleep_debt = max(0.0, 8.0 - actual_duration)

    return {
        "astronaut_id": astronaut_id,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "sleep_duration_hours": round(actual_duration, 2),
        "sleep_efficiency_pct": round(actual_efficiency, 1),
        "circadian_drift_hours": round(drift, 2),
        "rem_percentage": round(rem_pct, 1),
        "deep_sleep_percentage": round(deep_pct, 1),
        "light_sleep_percentage": round(light_pct, 1),
        "sleep_debt_hours": round(sleep_debt, 2),
        "is_simulated": 1
    }


def generate_sleep_history(astronaut_id: int, days: int = 14) -> List[Dict[str, Any]]:
    """Generates a 14-day chronological sleep history."""
    now = datetime.now(timezone.utc)
    history = []
    
    for d in range(days):
        t = now - timedelta(days=days - 1 - d)
        rec = simulate_sleep_profile(
            astronaut_id=astronaut_id,
            base_hours=7.3 + 0.3 * np.sin(d * 0.8),
            circadian_phase_offset_hours=0.3 * np.sin(d * 0.5),
            sleep_efficiency_pct=87.0
        )
        rec["timestamp"] = t.strftime("%Y-%m-%d 06:30:00")
        history.append(rec)
        
    return history
