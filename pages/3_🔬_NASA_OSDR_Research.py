"""
SPACECARE - Subsystem 3: NASA OSDR Research Integration
Authentic NASA Open Science Data Repository spaceflight omics, biological,
and physiological research explorer.

All studies and records presented in this console represent VERIFIED NASA open scientific data.
"""

import streamlit as st
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.nasa_data.osdr_client import (
    get_curated_human_studies, search_studies, fetch_live_study_metadata
)
from src.components.mission_header import render_mission_header, render_crew_selector_sidebar
from src.components.disclaimers import render_medical_disclaimer, render_sidebar_disclaimer
from src.components.badges import render_provenance_badge

st.set_page_config(page_title="SPACECARE | NASA OSDR Research", page_icon="🔬", layout="wide")

# Mission Header & Persistent Disclaimers
render_mission_header("NASA Open Science Data Repository (OSDR)")
render_medical_disclaimer(compact=True)
selected_astronaut = render_crew_selector_sidebar()
render_sidebar_disclaimer()

# Mandatory Provenance Notice
render_provenance_badge("real", "NASA Open Science Data Repository (OSDR)", "Verified Human Spaceflight Studies")

# Educational & Scientific Nature Callout
st.markdown(
    """
    <div style="background: rgba(11, 61, 145, 0.15); border: 1px solid rgba(59, 130, 246, 0.35); border-radius: 8px; padding: 12px 18px; margin-bottom: 20px; font-size: 0.86rem; color: #cbd5e1; line-height: 1.5;">
        ℹ️ <strong>RESEARCH DATA VS. CONTINUOUS TELEMETRY NOTICE:</strong><br>
        The datasets archived in the <strong>NASA Open Science Data Repository (OSDR)</strong> represent rigorous biological,
        transcriptomic, and clinical research investigations collected at mission milestones (pre-flight, in-flight, post-flight).
        They are <strong>not continuous wearable vital signs</strong>, but rather the empirical scientific evidence base for understanding
        spaceflight hazards such as <em>Spaceflight-Associated Neuro-ocular Syndrome (SANS)</em>, <em>immune dysregulation</em>, and <em>telomere dynamics</em>.
    </div>
    """,
    unsafe_allow_html=True
)

tab_browser, tab_inspector, tab_about = st.tabs([
    "📚 Human Spaceflight Study Explorer",
    "🔍 Live OSDR Metadata Inspector",
    "📖 About NASA OSDR Integration"
])

# ============================================================================
# TAB 1: Human Spaceflight Study Explorer
# ============================================================================
with tab_browser:
    st.markdown("#### 🧑‍🚀 Verified NASA Astronaut & Human Studies (Homo sapiens)")
    
    col_search, col_filter = st.columns([3, 1])
    with col_search:
        search_query = st.text_input(
            "Search Studies:",
            placeholder="Search by keyword, mission, SANS, immune, telomere, PI...",
            key="osdr_search_input"
        )
    with col_filter:
        tissue_selection = st.selectbox(
            "Target Tissue Filter:",
            ["All", "Blood", "Hair", "Retina", "Saliva"],
            key="osdr_tissue_filter"
        )

    studies = search_studies(query=search_query, tissue_filter=tissue_selection)
    st.markdown(f"**Found Studies:** `{len(studies)} authentic NASA research investigations`")

    for s in studies:
        with st.expander(f"🔬 [{s['study_id']}] {s['title']}", expanded=True):
            st.markdown(f"**Mission / Context:** `{s['mission']}` • **Duration:** `{s['flight_duration_days']} days`")
            st.markdown(f"**Principal Investigator:** {s['principal_investigator']}")
            st.markdown(f"**Assay Type:** `{s['assay_type']}` • **Platform:** `{s['platform']}`")
            st.markdown(f"**Target Tissue / Biospecimen:** `{s['target_tissue']}` (Sample Count: `{s['sample_count']}`)")
            
            st.markdown("##### 🧪 Investigation Overview")
            st.write(s["description"])

            st.markdown("##### 📌 Key Spaceflight Biological Findings")
            for finding in s.get("key_findings", []):
                st.markdown(f"- {finding}")

            c_doi, c_url = st.columns([1, 1])
            with c_doi:
                st.markdown(f"**Publication DOI:** [`{s.get('doi', 'N/A')}`](https://doi.org/{s.get('doi', '')})")
            with c_url:
                st.markdown(f"**Official NASA Repository:** [View Study on OSDR Portal]({s.get('repository_url', 'https://osdr.nasa.gov')})")

# ============================================================================
# TAB 2: Live OSDR Metadata Inspector
# ============================================================================
with tab_inspector:
    st.markdown("#### 🌐 Live NASA OSDR API Query")
    st.markdown(
        """
        Query any dataset accession number directly from the NASA OSDR Biological Data API 
        (e.g., `OSD-140`, `OSD-316`, `OSD-174`, `OSD-816`, `OSD-943`, or `OSD-166`).
        """
    )

    col_id, col_btn = st.columns([3, 1])
    with col_id:
        query_id = st.text_input("Enter NASA Study Accession ID:", value="OSD-140", key="live_osd_query")
    with col_btn:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        lookup_btn = st.button("Query NASA OSDR API", type="primary", use_container_width=True)

    if lookup_btn or query_id:
        with st.spinner(f"Contacting NASA OSDR API for {query_id}..."):
            result = fetch_live_study_metadata(query_id, timeout_sec=5)
            if result:
                badge_type = "real"
                render_provenance_badge(badge_type, result.get("provenance", "NASA OSDR"))

                st.success(f"Successfully retrieved metadata for {result['study_id']}.")
                st.markdown(f"### {result.get('title')}")
                st.markdown(f"**Organism:** `{result.get('organism', 'Homo sapiens')}`")
                st.markdown(f"**Description:** {result.get('description')}")

                if "key_findings" in result:
                    st.markdown("#### 🔬 Published Spaceflight Findings")
                    for kf in result["key_findings"]:
                        st.markdown(f"- {kf}")

                if "raw_api_response" in result:
                    with st.expander("Raw NASA OSDR API Response Payload"):
                        st.json(result["raw_api_response"])
            else:
                st.error(f"Could not retrieve study metadata for '{query_id}'. Verify the study ID format (e.g. OSD-140).")

# ============================================================================
# TAB 3: About NASA OSDR Integration
# ============================================================================
with tab_about:
    st.markdown("#### 🏛️ About the NASA Open Science Data Repository (OSDR)")
    st.markdown(
        """
        The **NASA Open Science Data Repository (OSDR)** merges data from **GeneLab** and the 
        **Ames Life Sciences Data Archive (ALSDA)** into a unified, publicly accessible portal for 
        biological and biomedical spaceflight investigations.

        - **Official Repository**: [https://osdr.nasa.gov/](https://osdr.nasa.gov/)
        - **Biological Data API**: `https://visualization.osdr.nasa.gov/biodata/api/v2/`
        - **Data Standard**: Follows FAIR principles (Findable, Accessible, Interoperable, and Reusable).
        - **SPACECARE Integration**: All data queried here preserves original study accession codes, 
          author attributions, DOIs, and official publication findings without modification or synthetic fabrication.
        """
    )
