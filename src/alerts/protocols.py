"""
SPACECARE Alerts & Early Warning - Flight Surgeon Action Protocols
Standard aerospace emergency response procedures and clinical checklists
for physiological deviations and environmental life support failures.
"""

from typing import Dict, Any, List

FLIGHT_SURGEON_PROTOCOLS: Dict[str, Dict[str, Any]] = {
    "HYPOXIA": {
        "title": "NASA Emergency Protocol: Acute Hypoxia Response",
        "category": "VITALS",
        "severity": "CRITICAL",
        "trigger_condition": "SpO2 < 90% or compensatory respiration > 24 br/min",
        "checklists": [
            "1. Immediately don emergency quick-don oxygen mask (100% O2 positive pressure).",
            "2. Verify module ambient oxygen concentration and partial pressure on ECLSS console.",
            "3. Inspect suit/hatch seals for micro-leaks or sudden cabin atmospheric displacement.",
            "4. Alert Flight Surgeon (Surgeon-1) and Mission Control Flight Director (Flight).",
            "5. Re-evaluate pulse oximetry and arterial oxygen saturation every 60 seconds."
        ]
    },
    "CARDIAC_ARRHYTHMIA": {
        "title": "NASA Protocol: Acute Cardiac Dysrhythmia & Tachycardia",
        "category": "VITALS",
        "severity": "CRITICAL",
        "trigger_condition": "Resting Heart Rate > 120 bpm or HRV RMSSD < 20 ms",
        "checklists": [
            "1. Order immediate cessation of all physical exertion and extravehicular activity (EVA).",
            "2. Transition crew member to recumbent position inside crew quarters.",
            "3. Attach 12-lead Holter electrocardiogram electrodes for continuous waveform monitoring.",
            "4. Assess microgravity fluid shift and administer electrolyte oral rehydration solution.",
            "5. Flight Surgeon consultation for anti-arrhythmic medication protocol review."
        ]
    },
    "HYPERCAPNIA": {
        "title": "ISS ECLSS Protocol: Elevated CO2 & CDRA Scrubber Malfunction",
        "category": "ENVIRONMENT",
        "severity": "WARNING",
        "trigger_condition": "Cabin CO2 Partial Pressure > 3.8 mmHg",
        "checklists": [
            "1. Verify Carbon Dioxide Removal Assembly (CDRA) bed cycling status in Node 3.",
            "2. Switch to backup Amine Swingbed or Russian Vozdukh CO2 scrubbing system.",
            "3. Increase Inter-Module Ventilation (IMV) fan speeds to eliminate stagnant CO2 pockets.",
            "4. Screen crew members for early hypercapnic symptoms: fronto-orbital headache, lethargy, dyspnea.",
            "5. Log environmental exposure duration for flight medical records."
        ]
    },
    "DECOMPRESSION": {
        "title": "ISS Emergency Protocol: Rapid Cabin Depressurization",
        "category": "ENVIRONMENT",
        "severity": "CRITICAL",
        "trigger_condition": "Cabin Pressure < 13.5 psi or pressure decay rate > 0.1 psi/min",
        "checklists": [
            "1. Sound orbital emergency klaxon and alert all crew across all modules.",
            "2. Isolate compromised module by sealing inter-module pressure hatches.",
            "3. Crew retreats immediately toward designated Soyuz / Crew Dragon safe-haven craft.",
            "4. Verify high-pressure N2/O2 repressurization manifold valve actuation.",
            "5. Maintain continuous comms with Mission Control Houston and TsUP Moscow."
        ]
    },
    "HEAT_STRESS": {
        "title": "NASA Thermal Protocol: Hyperthermia & Core Temperature Spike",
        "category": "VITALS",
        "severity": "WARNING",
        "trigger_condition": "Core Body Temperature > 38.2°C",
        "checklists": [
            "1. Terminate high-workload operations or spacewalk immediately.",
            "2. Maximize liquid cooling circulation in Liquid Cooling & Ventilation Garment (LCVG).",
            "3. Administer chilled oral hydration fluids (electrolyte supplemented).",
            "4. Monitor core temperature sensor every 5 minutes until stabilized below 37.3°C."
        ]
    },
    "COGNITIVE_FATIGUE": {
        "title": "Aerospace Neurobehavioral Protocol: Critical Cognitive Fatigue",
        "category": "MENTAL_HEALTH",
        "severity": "WARNING",
        "trigger_condition": "Cognitive Fatigue Risk Index > 65 or NASA-TLX > 75",
        "checklists": [
            "1. Reassign safety-critical duties (docking, robotic arm, spacewalk) to backup crew.",
            "2. Enforce mandatory 8.5-hour dark rest period in sound-attenuated crew quarters.",
            "3. Review mission timeline and reduce cognitive task density for following flight day.",
            "4. Check circadian lighting schedule (blue-enriched vs dim amber spectrum)."
        ]
    },
    "ML_MULTIVARIATE_ANOMALY": {
        "title": "AI Early Warning: Multivariate Biometric Divergence",
        "category": "ML_ANOMALY",
        "severity": "ADVISORY",
        "trigger_condition": "Isolation Forest Anomaly Score < 0.0 with abnormal feature attribution",
        "checklists": [
            "1. Review feature attribution radar to identify primary deviating physiological parameters.",
            "2. Cross-reference telemetry with active astronaut activity log (sleep, meal, workout).",
            "3. Verify biometric sensor contact quality and electrode impedance.",
            "4. Flag astronaut telemetry record for scheduled Flight Surgeon shift review."
        ]
    }
}


def get_protocol(protocol_key: str) -> Dict[str, Any]:
    """Retrieves flight surgeon protocol by key, or returns generic nominal protocol."""
    return FLIGHT_SURGEON_PROTOCOLS.get(
        protocol_key,
        {
            "title": "Standard Spaceflight Telemetry Monitoring",
            "category": "GENERAL",
            "severity": "NOMINAL",
            "trigger_condition": "All vitals and life support nominal",
            "checklists": ["Maintain continuous nominal telemetry monitoring."]
        }
    )
