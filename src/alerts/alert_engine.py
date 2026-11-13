"""
SPACECARE Early Warning Alert Engine
Combines deterministic physiological/environmental threshold rules with
unsupervised machine learning anomaly scores to evaluate and trigger tiered alerts.

Tier Hierarchy:
- NOMINAL: Parameters within normal spaceflight bounds.
- ADVISORY: Minor baseline deviation or multivariate ML anomaly alert.
- WARNING: Actionable physiological or life support deviation.
- CRITICAL: Immediate life-threatening hazard requiring immediate intervention.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from src.database.queries import create_alert, get_active_alerts
from src.alerts.protocols import FLIGHT_SURGEON_PROTOCOLS, get_protocol


def is_duplicate_active_alert(title: str, astronaut_id: Optional[int] = None) -> bool:
    """Checks if an identical active (unacknowledged) alert already exists to prevent alert spam."""
    active = get_active_alerts(limit=50)
    for a in active:
        if a["title"] == title and a.get("astronaut_id") == astronaut_id:
            return True
    return False


def evaluate_vitals_for_alerts(
    astronaut: Dict[str, Any],
    reading: Dict[str, Any],
    ml_result: Optional[Dict[str, Any]] = None
) -> List[int]:
    """
    Evaluates a vital signs reading against clinical spaceflight thresholds
    and ML anomaly predictions. Triggers alerts and returns created alert IDs.
    """
    ast_id = astronaut["id"]
    ast_name = astronaut["name"]
    created_alert_ids = []

    hr = float(reading.get("heart_rate", 70.0))
    spo2 = float(reading.get("spo2", 98.0))
    temp = float(reading.get("core_temperature", 36.8))
    rr = float(reading.get("respiration_rate", 14.0))

    # 1. Hypoxia Check
    if spo2 < 90.0:
        title = f"Acute Hypoxia Alert: {ast_name}"
        if not is_duplicate_active_alert(title, ast_id):
            proto = get_protocol("HYPOXIA")
            aid = create_alert(
                severity="CRITICAL",
                category="VITALS",
                title=title,
                message=f"Blood oxygen saturation collapsed to {spo2:.1f}%. Immediate supplemental oxygen required.",
                flight_surgeon_protocol="\n".join(proto["checklists"]),
                astronaut_id=ast_id,
                metric_name="spo2",
                metric_value=spo2,
                threshold_limit=90.0
            )
            created_alert_ids.append(aid)
    elif spo2 < 94.0:
        title = f"Mild Hypoxemia Advisory: {ast_name}"
        if not is_duplicate_active_alert(title, ast_id):
            aid = create_alert(
                severity="WARNING",
                category="VITALS",
                title=title,
                message=f"SpO2 decreased to {spo2:.1f}%. Verify cabin O2 and crew breathing rate.",
                flight_surgeon_protocol="Check pulse oximeter sensor placement and verify cabin O2 partial pressure.",
                astronaut_id=ast_id,
                metric_name="spo2",
                metric_value=spo2,
                threshold_limit=94.0
            )
            created_alert_ids.append(aid)

    # 2. Cardiac Arrhythmia / Tachycardia Check
    if hr > 130.0 or hr < 45.0:
        title = f"Severe Arrhythmia / Tachycardia: {ast_name}"
        if not is_duplicate_active_alert(title, ast_id):
            proto = get_protocol("CARDIAC_ARRHYTHMIA")
            aid = create_alert(
                severity="CRITICAL",
                category="VITALS",
                title=title,
                message=f"Heart rate measured at {hr:.1f} bpm. Exceeds critical cardiac limits.",
                flight_surgeon_protocol="\n".join(proto["checklists"]),
                astronaut_id=ast_id,
                metric_name="heart_rate",
                metric_value=hr,
                threshold_limit=130.0
            )
            created_alert_ids.append(aid)
    elif hr > 105.0:
        title = f"Elevated Heart Rate Warning: {ast_name}"
        if not is_duplicate_active_alert(title, ast_id):
            aid = create_alert(
                severity="WARNING",
                category="VITALS",
                title=title,
                message=f"Resting heart rate elevated at {hr:.1f} bpm. Monitor for physical stress or dehydration.",
                flight_surgeon_protocol="Assess astronaut workload, verify hydration, and monitor ECG rhythm.",
                astronaut_id=ast_id,
                metric_name="heart_rate",
                metric_value=hr,
                threshold_limit=105.0
            )
            created_alert_ids.append(aid)

    # 3. Core Body Temperature / Heat Stress Check
    if temp > 38.5:
        title = f"Hyperthermia Heat Stress: {ast_name}"
        if not is_duplicate_active_alert(title, ast_id):
            proto = get_protocol("HEAT_STRESS")
            aid = create_alert(
                severity="CRITICAL",
                category="VITALS",
                title=title,
                message=f"Core body temperature reached {temp:.2f}°C. Severe risk of heat stroke.",
                flight_surgeon_protocol="\n".join(proto["checklists"]),
                astronaut_id=ast_id,
                metric_name="core_temperature",
                metric_value=temp,
                threshold_limit=38.5
            )
            created_alert_ids.append(aid)
    elif temp > 37.6:
        title = f"Elevated Core Temperature: {ast_name}"
        if not is_duplicate_active_alert(title, ast_id):
            aid = create_alert(
                severity="WARNING",
                category="VITALS",
                title=title,
                message=f"Core temperature is elevated at {temp:.2f}°C. Evaluate active cooling garments.",
                flight_surgeon_protocol="Provide oral hydration and check LCVG coolant loop temperature.",
                astronaut_id=ast_id,
                metric_name="core_temperature",
                metric_value=temp,
                threshold_limit=37.6
            )
            created_alert_ids.append(aid)

    # 4. Machine Learning Multivariate Anomaly Check
    
    # 4. Machine Learning Multivariate Anomaly Check
    if ml_result and ml_result.get("is_anomaly") == 1:
        raw_score = ml_result.get("raw_decision_score", -0.1)
        title = f"ML Anomaly Detected: {ast_name}"

        if not is_duplicate_active_alert(title, ast_id):
            proto = get_protocol("ML_MULTIVARIATE_ANOMALY")
            top_features = []

            for feat, feature_data in ml_result.get(
                "feature_contributions", {}
            ).items():
                if feature_data.get("deviation_severity") in (
                    "HIGH", "MODERATE"
                ):
                    z_score = feature_data.get("z_score", 0.0)
                    top_features.append(
                        f"{feat} (Z: {z_score:+.2f})"
                    )

            feat_text = (
                ", ".join(top_features)
                if top_features
                else "Multi-feature divergence"
            )

            aid = create_alert(
                severity="ADVISORY",
                category="ML_ANOMALY",
                source="ML_MODEL",
                title=title,
                message=(
                    f"Isolation Forest flagged biometric pattern "
                    f"(Score: {raw_score:.3f}). "
                    f"Primary drivers: {feat_text}."
                ),
                flight_surgeon_protocol="\n".join(
                    proto["checklists"]
                ),
                astronaut_id=ast_id,
                metric_name="ml_score",
                metric_value=raw_score,
                threshold_limit=0.0
            )

            created_alert_ids.append(aid)

    return created_alert_ids


def evaluate_environment_for_alerts(reading: Dict[str, Any]) -> List[int]:
    """
    Evaluates ISS ECLSS environmental readings against spacecraft life support thresholds.
    Triggers alerts and returns created alert IDs.
    """
    created_alert_ids = []
    press = float(reading.get("cabin_pressure_psi", 14.7))
    co2 = float(reading.get("co2_partial_pressure_mmhg", 2.8))
    o2 = float(reading.get("o2_percentage", 21.0))
    temp = float(reading.get("temperature_celsius", 22.2))
    module = reading.get("module_name", "ISS Complex")

    # 1. Cabin Depressurization Check
    if press < 13.5:
        title = f"Cabin Decompression Alert ({module})"
        if not is_duplicate_active_alert(title):
            proto = get_protocol("DECOMPRESSION")
            aid = create_alert(
                severity="CRITICAL",
                category="ENVIRONMENT",
                title=title,
                message=f"Cabin total pressure dropped to {press:.2f} psi. Immediate structural seal breach suspected.",
                flight_surgeon_protocol="\n".join(proto["checklists"]),
                metric_name="cabin_pressure_psi",
                metric_value=press,
                threshold_limit=13.5
            )
            created_alert_ids.append(aid)
    elif press < 14.2:
        title = f"Low Cabin Pressure Warning ({module})"
        if not is_duplicate_active_alert(title):
            aid = create_alert(
                severity="WARNING",
                category="ENVIRONMENT",
                title=title,
                message=f"Cabin pressure decreased to {press:.2f} psi. Verify Pressure Control Assembly (PCA).",
                flight_surgeon_protocol="Check PCA nitrogen/oxygen injection valves and inspect hatch equalizers.",
                metric_name="cabin_pressure_psi",
                metric_value=press,
                threshold_limit=14.2
            )
            created_alert_ids.append(aid)

    # 2. Hypercapnia / CO2 Check
    if co2 > 4.5:
        title = f"Hypercapnia Scrubber Failure ({module})"
        if not is_duplicate_active_alert(title):
            proto = get_protocol("HYPERCAPNIA")
            aid = create_alert(
                severity="CRITICAL",
                category="ENVIRONMENT",
                title=title,
                message=f"CO2 partial pressure reached {co2:.2f} mmHg. Severe cognitive and physiological impairment risk.",
                flight_surgeon_protocol="\n".join(proto["checklists"]),
                metric_name="co2_partial_pressure_mmhg",
                metric_value=co2,
                threshold_limit=4.5
            )
            created_alert_ids.append(aid)
    elif co2 > 3.8:
        title = f"Elevated CO2 Warning ({module})"
        if not is_duplicate_active_alert(title):
            proto = get_protocol("HYPERCAPNIA")
            aid = create_alert(
                severity="WARNING",
                category="ENVIRONMENT",
                title=title,
                message=f"Cabin CO2 partial pressure is elevated at {co2:.2f} mmHg. Verify CDRA cycling.",
                flight_surgeon_protocol="\n".join(proto["checklists"]),
                metric_name="co2_partial_pressure_mmhg",
                metric_value=co2,
                threshold_limit=3.8
            )
            created_alert_ids.append(aid)

    # 3. Oxygen Deficiency Check
    if o2 < 19.5:
        title = f"Hypoxic Cabin Atmosphere ({module})"
        if not is_duplicate_active_alert(title):
            aid = create_alert(
                severity="CRITICAL",
                category="ENVIRONMENT",
                title=title,
                message=f"Oxygen concentration decreased to {o2:.2f}%. Verify Oxygen Generation System (OGS).",
                flight_surgeon_protocol="Initiate backup O2 candle or repressurization from external high-pressure tanks.",
                metric_name="o2_percentage",
                metric_value=o2,
                threshold_limit=19.5
            )
            created_alert_ids.append(aid)

    # 4. Thermal Loop Degradation Check
    if temp > 28.0:
        title = f"Cabin Overheating Warning ({module})"
        if not is_duplicate_active_alert(title):
            aid = create_alert(
                severity="WARNING",
                category="ENVIRONMENT",
                title=title,
                message=f"Cabin temperature has risen to {temp:.1f}°C. Internal Active Thermal Control loop issue.",
                flight_surgeon_protocol="Inspect IATCS water coolant loop pumps and cabin heat exchangers.",
                metric_name="temperature_celsius",
                metric_value=temp,
                threshold_limit=28.0
            )
            created_alert_ids.append(aid)

    return created_alert_ids
