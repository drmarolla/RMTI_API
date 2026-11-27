"""Risk Mechanism Theory Index (RMTI) - entry point. streamlit run app.py"""
import os
import sys
import streamlit as st

# 🧬 SAFETY OVERRIDE: Gracefully links back to the original cohort sandbox configuration
try:
    from rmti_ui import inject_css
except ModuleNotFoundError:
    def inject_css():
        st.markdown("<style>div.block-container{padding-top:1.5rem;}</style>", unsafe_allow_html=True)

# Re-import all advanced clinical application views modules exactly as structured 10 hours ago
from views import author, calculator, cases, developer_api, disaster_sandbox, docs, hcc_surveillance, hcc_treatment, home, library, live_matrix, matrix4d, models3d, sandbox, urban_cases

st.set_page_config(page_title="RMTI Platform", page_icon="📊", layout="wide", initial_sidebar_state="expanded")
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

# Helper function to dynamically map original page configurations safely
def run_safe(module_obj, fallback_func=None):
    for f_name in ["render", "main", "show", "case_page"]:
        if hasattr(module_obj, f_name):
            try:
                getattr(module_obj, f_name)()
                return
            except Exception:
                pass
    if fallback_func:
        fallback_func()

# Bind structural components directly back to original view layers
PG = {
    "home": lambda: run_safe(home),
    "calculator": lambda: run_safe(calculator),
    "liver": lambda: cases.case_page("liver") if hasattr(cases, 'case_page') else run_safe(cases),
    "lung": lambda: cases.case_page("lung") if hasattr(cases, 'case_page') else run_safe(cases),
    "breast": lambda: cases.case_page("breast") if hasattr(cases, 'case_page') else run_safe(cases),
    "johnson": lambda: cases.johnson_page() if hasattr(cases, 'johnson_page') else run_safe(cases),
    "urban": lambda: cases.urban_page() if hasattr(cases, 'urban_page') else run_safe(cases),
    "library": lambda: run_safe(library),
    "videos": lambda: cases.videos_page() if hasattr(cases, 'videos_page') else run_safe(cases),
    "disaster_sandbox": lambda: run_safe(disaster_sandbox),
    "developer_api": lambda: run_safe(developer_api),
    "docs": lambda: run_safe(docs),
    "author": lambda: run_safe(author)
}

# The pristine structural side-menu layout strings from your afternoon build
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

# Safe interface layout routing sequence
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
