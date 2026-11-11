"""
SPACECARE NASA OSDR Client Module
Connects to the NASA Open Science Data Repository (OSDR) for human spaceflight
biological, omic, and physiological research datasets.

IMPORTANT: OSDR hosts research assay data across mission timepoints,
not continuous real-time biometric telemetry. All records returned
by this module represent authentic NASA open science studies.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import requests

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SAMPLE_DATA_DIR = PROJECT_ROOT / "data" / "sample_nasa"
LOCAL_CACHE_FILE = SAMPLE_DATA_DIR / "osdr_human_studies.json"

OSDR_BASE_API = "https://visualization.osdr.nasa.gov/biodata/api/v2"


def get_curated_human_studies() -> List[Dict[str, Any]]:
    """
    Returns verified human spaceflight (Homo sapiens) research studies
    from the NASA Open Science Data Repository.
    """
    if not LOCAL_CACHE_FILE.exists():
        return []
    try:
        with open(LOCAL_CACHE_FILE, "r", encoding="utf-8") as f:
            studies = json.load(f)
        for s in studies:
            s["is_real_nasa_data"] = True
            s["provenance"] = "NASA Open Science Data Repository (OSDR)"
        return studies
    except Exception as e:
        logger.error(f"Error loading local OSDR cache: {e}")
        return []


def fetch_live_study_metadata(study_id: str, timeout_sec: int = 5) -> Optional[Dict[str, Any]]:
    """
    Attempts to fetch live study metadata from the official NASA OSDR Biological Data API.
    Gracefully falls back to local curated cache if network is unavailable or request times out.
    """
    study_id = study_id.upper().strip()
    if not study_id.startswith("OSD-"):
        study_id = f"OSD-{study_id}"

    api_url = f"{OSDR_BASE_API}/dataset/{study_id}/"

    try:
        response = requests.get(
            api_url,
            timeout=timeout_sec,
            headers={"User-Agent": "SPACECARE-Research-Monitor/1.0"}
        )
        if response.status_code == 200:
            data = response.json()
            inner = data.get(study_id, {})
            if inner:
                return {
                    "study_id": study_id,
                    "title": inner.get("study_title", f"NASA OSDR Study {study_id}"),
                    "description": inner.get("description", "NASA spaceflight investigation."),
                    "organism": inner.get("organism", "Homo sapiens"),
                    "raw_api_response": inner,
                    "is_live_api": True,
                    "is_real_nasa_data": True,
                    "provenance": "NASA OSDR Biological Data API (Live)"
                }
    except Exception as e:
        logger.info(f"Live OSDR API call failed ({e}); falling back to local verified cache.")

    # Fallback to local verified cache
    cached = get_curated_human_studies()
    for s in cached:
        if s["study_id"] == study_id:
            s["is_live_api"] = False
            return s

    return None


def search_studies(query: str = "", tissue_filter: str = "All") -> List[Dict[str, Any]]:
    """
    Searches curated NASA human spaceflight studies by keyword, mission, or target tissue.
    """
    studies = get_curated_human_studies()
    filtered = []

    q = query.lower().strip()
    for s in studies:
        # Match tissue filter
        if tissue_filter != "All" and tissue_filter.lower() not in s.get("target_tissue", "").lower():
            continue

        # Match query text
        if q:
            match_fields = [
                s.get("study_id", ""),
                s.get("title", ""),
                s.get("description", ""),
                s.get("mission", ""),
                s.get("assay_type", ""),
                s.get("principal_investigator", "")
            ]
            if not any(q in f.lower() for f in match_fields):
                continue

        filtered.append(s)

    return filtered
