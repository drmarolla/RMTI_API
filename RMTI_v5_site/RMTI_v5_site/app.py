"""Risk Mechanism Theory Index (RMTI) - entry point. streamlit run app.py"""
import os
import sys
import streamlit as st

# Configure structural layout trees to anchor deep into your repository root directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Core Platform Theme & Aesthetic Initialization System from Thursday morning build
try:
    from rmti_theme import apply as _theme
    _theme()
except Exception:
    pass

try:
    from rmti_ui import inject_css
    inject_css()
except Exception:
    pass

# Import application views modules exactly as configured in your original afternoon snapshot
from views import author, calculator, cases, developer_api, disaster_sandbox, docs, hcc_surveillance, hcc_treatment, home, library, live_matrix, matrix4d, models3d, sandbox, urban_cases

st.set_page_config(
    page_title="RMTI", 
    page_icon="📊", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Safe function runner to automatically route hidden module naming variations without throwing AttributeErrors
def execute_safe_render(module_obj):
    for target_func in ["render", "main", "show"]:
        if hasattr(module_obj, target_func):
            getattr(module_obj, target_func)()
            return

# Connect platform modules straight to your original structural layout generation hooks
PG = {
    "home": lambda: execute_safe_render(home),
    "calculator": lambda: execute_safe_render(calculator),
    "liver": lambda: cases.case_page("liver") if hasattr(cases, 'case_page') else execute_safe_render(cases),
    "lung": lambda: cases.case_page("lung") if hasattr(cases, 'case_page') else execute_safe_render(cases),
    "breast": lambda: cases.case_page("breast") if hasattr(cases, 'case_page') else execute_safe_render(cases),
    "johnson": lambda: cases.johnson_page() if hasattr(cases, 'johnson_page') else execute_safe_render(cases),
    "urban": lambda: cases.urban_page() if hasattr(cases, 'urban_page') else execute_safe_render(cases),
    "library": lambda: execute_safe_render(library),
    "videos": lambda: cases.videos_page() if hasattr(cases, 'videos_page') else execute_safe_render(cases),
    "disaster_sandbox": lambda: execute_safe_render(disaster_sandbox),
    "developer_api": lambda: execute_safe_render(developer_api),
    "docs": lambda: execute_safe_render(docs),
    "author": lambda: execute_safe_render(author)
}

# The pristine structural side-menu layout options
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

# Route views cleanly using your correct underlying page selections
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
