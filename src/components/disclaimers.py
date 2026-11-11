"""
SPACECARE Disclaimers Component
Provides standardized medical disclaimers and data integrity notices across all dashboard views.
"""

import streamlit as st


def render_medical_disclaimer(compact: bool = False) -> None:
    """Renders the required non-diagnostic medical and aerospace research disclaimer."""
    if compact:
        st.markdown(
            """
            <div class="disclaimer-banner" style="padding: 6px 12px; margin: 6px 0 12px 0;">
                ⚠️ <strong>RESEARCH PROTOTYPE ONLY</strong>: SPACECARE is an aerospace simulation & engineering prototype. 
                <strong>Not certified for clinical diagnosis, patient triage, or medical treatment.</strong>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            """
            <div class="disclaimer-banner">
                ⚠️ <strong>MEDICAL & REGULATORY NOTICE:</strong><br>
                SPACECARE is developed solely as an aerospace engineering research and educational simulation platform.
                It is <strong>NOT</strong> an FDA-cleared or CE-marked medical device and must never be utilized as a substitute 
                for professional clinical evaluation, diagnostic decision-making, or operational life-support flight controls.
            </div>
            """,
            unsafe_allow_html=True
        )


def render_sidebar_disclaimer() -> None:
    """Renders persistent non-diagnostic notice in the Streamlit sidebar."""
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        """
        <div style="font-size: 0.72rem; color: #94a3b8; line-height: 1.35; padding: 4px 6px;">
            <strong style="color: #f59e0b;">⚠️ Prototype Notice:</strong><br>
            Non-diagnostic research simulation. Not for medical treatment or clinical decision-making.
        </div>
        """,
        unsafe_allow_html=True
    )
