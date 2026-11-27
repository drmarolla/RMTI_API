"""Risk Mechanism Theory Index (RMTI) - entry point. streamlit run app.py"""
import os
import streamlit as st
from rmti_ui import inject_css

import views.author as author
import views.calculator as calculator
import views.cases as cases
import views.developer_api as developer_api
import views.disaster_sandbox as disaster_sandbox
import views.docs as docs
import views.hcc_surveillance as hcc_surveillance
import views.hcc_treatment as hcc_treatment
import views.home as home
import views.library as library
import views.live_matrix as live_matrix
import views.matrix4d as matrix4d
import views.models3d as models3d
import views.sandbox as sandbox
import views.urban_cases as urban_cases

st.set_page_config(page_title="RMTI", page_icon="📊", layout="wide", initial_sidebar_state="expanded")
inject_css()

_NS = "".join(["http://", "www.w3.org/", "2000/svg"])
_SVG = (
    f'<svg xmlns="{_NS}" viewBox="0 0 260 64" width="260" height="64">'
    '<circle cx="32" cy="32" r="25" fill="rgba(56,189,248,0.12)" stroke="#38BDF8" stroke-width="2.4"/>'
    '<circle cx="32" cy="32" r="20" fill="none" stroke="rgba(255,255,255,0.28)" stroke-width="1" stroke-dasharray="4 3"/>'
    '<rect x="20" y="28" width="5.5" height="16" rx="2.5" fill="#093C5F"/>'
    '<rect x="29.25" y="19" width="5.5" height="25" rx="2.5" fill="#38BDF8"/>'
    '<rect x="38.5" y="23" width="5.5" height="21" rx="2.5" fill="#FFFFFF"/>'
    '<text x="68" y="31" font-family="Arial, sans-serif" font-weight="900" font-size="25" letter-spacing="1.4" fill="#FFFFFF">RMTI</text>'
    '<text x="69" y="45" font-family="Arial, sans-serif" font-weight="700" font-size="9.5" letter-spacing="0.6" fill="#E2E8F0">RISK MECHANISM</text>'
    '<text x="69" y="56" font-family="Arial, sans-serif" font-weight="700" font-size="9.5" letter-spacing="0.6" fill="#38BDF8">THEORY INDEX</text>'
    '</svg>'
)

st.sidebar.markdown(f'<div style="margin-bottom: 1.5rem;">{_SVG}</div>', unsafe_allow_html=True)

def render_technical_documentation():
    st.header("Technical Documentation Manual")
    st.caption("Resilient Macro-Micro Tumor Microenvironment Interface (RMTI) Core Reference")
    with st.container(border=True):
        st.markdown("### Core Metric Formulation Model Index")
        st.latex(r"R = L \cdot E \cdot V \cdot (1 - \rho)")

def render_author_profile():
    st.header("Author Academic Profile")
    st.caption("Risk Mechanism Theory Index (RMTI) Principal Investigator")
    with st.container(border=True):
        st.markdown("### Dr. Marolla")

PG = {
    "home": home.render if hasattr(home, 'render') else home.main if hasattr(home, 'main') else lambda: None,
    "calculator": calculator.render if hasattr(calculator, 'render') else calculator.main if hasattr(calculator, 'main') else lambda: None,
    "liver": lambda: cases.case_page("liver") if hasattr(cases, 'case_page') else lambda: None,
    "lung": lambda: cases.case_page("lung") if hasattr(cases, 'case_page') else lambda: None,
    "breast": lambda: cases.case_page("breast") if hasattr(cases, 'case_page') else lambda: None,
    "johnson": cases.johnson_page if hasattr(cases, 'johnson_page') else lambda: None,
    "urban": cases.urban_page if hasattr(cases, 'urban_page') else lambda: None,
    "library": library.render if hasattr(library, 'render') else library.main if hasattr(library, 'main') else lambda: None,
    "videos": cases.videos_page if hasattr(cases, 'videos_page') else lambda: None,
    "disaster_sandbox": disaster_sandbox.render if hasattr(disaster_sandbox, 'render') else disaster_sandbox.main if hasattr(disaster_sandbox, 'main') else lambda: None,
    "developer_api": developer_api.render if hasattr(developer_api, 'render') else developer_api.main if hasattr(developer_api, 'main') else lambda: None,
    "docs": render_technical_documentation,
    "author": render_author_profile
}

menu_options = [
    "Framework Home",
    "Live RMTI Calculator",
    "Hepatocellular Carcinoma (HCC) Case Study",
    "Non-Small Cell Lung Cancer Case Study",
    "HR-Positive Breast Cancer Case Study",
    "Johnson Cohort Surveillance Analysis",
    "Sub-Saharan Urban Flooding Case Study",
    "Framework Research Library",
    "Narrated 3D Motion Video Library",
    "Disaster Resilience Sandbox",
    "Developer API Integration Hub",
    "Technical Documentation Manual",
    "Author Academic Profile"
]

selected_page = st.sidebar.radio("Navigate Platform Modules", menu_options)

if selected_page == "Framework Home":
    PG["home"]()
elif selected_page == "Live RMTI Calculator":
    PG["calculator"]()
elif selected_page == "Hepatocellular Carcinoma (HCC) Case Study":
    PG["liver"]()
elif selected_page == "Non-Small Cell Lung Cancer Case Study":
    PG["lung"]()
elif selected_page == "HR-Positive Breast Cancer Case Study":
    PG["breast"]()
elif selected_page == "Johnson Cohort Surveillance Analysis":
    PG["johnson"]()
elif selected_page == "Sub-Saharan Urban Flooding Case Study":
    PG["urban"]()
elif selected_page == "Framework Research Library":
    PG["library"]()
elif selected_page == "Narrated 3D Motion Video Library":
    PG["videos"]()
elif selected_page == "Disaster Resilience Sandbox":
    PG["disaster_sandbox"]()
elif selected_page == "Developer API Integration Hub":
    PG["developer_api"]()
elif selected_page == "Technical Documentation Manual":
    PG["docs"]()
elif selected_page == "Author Academic Profile":
    PG["author"]()
