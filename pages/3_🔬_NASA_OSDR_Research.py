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
from src.nasa_data.fastq_qc import analyze_fastq
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

tab_browser, tab_inspector, tab_about, tab_fastq = st.tabs([
    "📚 Human Spaceflight Study Explorer",
    "🔍 Live OSDR Metadata Inspector",
    "📖 About NASA OSDR Integration",
    "🧬 Raw RNA-seq Quality Control"
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
# ============================================================================
# TAB 4: NASA OSDR Raw RNA-seq Data & Quality Control
# ============================================================================
with tab_fastq:
    st.markdown("#### 🧬 NASA OSDR-316 Raw RNA-seq Dataset")

    st.info(
        "Authentic NASA OSDR raw sequencing reads. "
        "This is research data, not continuous astronaut wearable telemetry."
    )

    fastq_path = (
        PROJECT_ROOT
        / "data"
        / "nasa_downloads"
        / "OSD-316"
        / "GLDS-316_rna-seq_SRR11586267.fastq.gz"
    )

    st.markdown(
        "**Study:** OSD-316 – Plasticity of the human IgM repertoire "
        "in response to a long-term spaceflight"
    )
    st.markdown(
        "**Sample:** SRR11586267 | COS 5 | Postflight R+1 | Whole blood"
    )
    st.markdown("**Platform:** Illumina MiSeq | RNA-seq | Single-end")

    if st.button("Analyze downloaded NASA FASTQ file", key="analyze_osd316_fastq"):
        if not fastq_path.exists():
            st.error(f"FASTQ file not found: {fastq_path}")
        else:
            with st.spinner("Reading NASA FASTQ and calculating QC metrics..."):
                try:
                    qc = analyze_fastq(fastq_path)

                    st.success("FASTQ analysis completed.")

                    c1, c2, c3 = st.columns(3)
                    c1.metric("Valid reads", f"{qc['total_reads']:,}")
                    c2.metric("Total bases", f"{qc['total_bases']:,}")
                    c3.metric("File size", f"{qc['file_size_mb']} MB")

                    c4, c5, c6 = st.columns(3)
                    c4.metric("Average read length", f"{qc['average_read_length']} bases")
                    c5.metric("GC content", f"{qc['gc_content_pct']}%")
                    c6.metric("Mean Phred quality", qc["mean_phred_quality"])

                    c7, c8, c9 = st.columns(3)
                    c7.metric("Q30 bases", f"{qc['q30_percentage']}%")
                    c8.metric("Invalid records", qc["invalid_records"])
                    c9.metric(
                        "Read length range",
                        f"{qc['minimum_read_length']}–{qc['maximum_read_length']}"
                    )

                    st.caption(
                        "Q30 = fraction of bases with Phred quality score ≥30. "
                        "Metrics calculated locally from the downloaded FASTQ "
                        "using Phred+33 encoding."
                    )

                    with st.expander("View complete QC results"):
                        st.json(qc)

                except Exception as e:
                    st.error(f"FASTQ analysis failed: {e}")

    st.warning(
        "Scope: This is basic FASTQ structural and base-quality QC only. "
        "No read alignment, gene-expression quantification, IgM repertoire "
        "analysis, or clinical interpretation has been performed."
    )