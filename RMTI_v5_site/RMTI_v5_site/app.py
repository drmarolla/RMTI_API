"""Risk Mechanism Theory Index (RMTI) - entry point. streamlit run app.py"""
import os
import sys
import importlib.util
import streamlit as st
from rmti_ui import inject_css

# Configure explicit module lookup trees across your repository folders
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))
sys.path.append(REPO_ROOT)

# Core Platform Theme & Aesthetic Initialization System
try:
    from rmti_theme import apply as _theme
    _theme()
except Exception:
    pass

# Import standard dashboard application module view pages
import views.author as author
import views.calculator as calculator
import views.cases as cases
import views.developer_api as developer_api
import views.disaster_sandbox as disaster_sandbox
import views.docs as docs
import views.home as home
import views.library as library

# Secure high-end analytical layouts directly from your pristine asset file
try:
    spec = importlib.util.spec_from_file_location(
        "high_end_cases", 
        os.path.join(REPO_ROOT, "5_Case_Studies_and_Videos (1).py")
    )
    case_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(case_module)
except Exception:
    case_module = cases

st.set_page_config(
    page_title="RMTI Platform", 
    page_icon="📊", 
    layout="wide", 
    initial_sidebar_state="expanded"
)
inject_css()

_NS = "".join(["http://", "www.w3.org/", "2000/svg"])
_SVG = (
    f'<svg xmlns="{_NS}" viewBox="0 0 260 64" width="260" height="64">'
    '<circle cx="32" cy="32" r="25" fill="rgba(56,189,248,0.12)" stroke="#38BDF8" stroke-width="2.4"/>'
    '<text x="68" y="31" font-family="Arial, sans-serif" font-weight="900" font-size="25" fill="#FFFFFF">RMTI</text>'
    '</svg>'
)
st.sidebar.markdown(f'<div style="margin-bottom: 1.5rem;">{_SVG}</div>', unsafe_allow_html=True)

# Safe function runner mapping utility
def safe_render(module_obj, fallback_func_name="render"):
    if hasattr(module_obj, fallback_func_name):
        getattr(module_obj, fallback_func_name)()
    elif hasattr(module_obj, "main"):
        getattr(module_obj, "main")()
    elif hasattr(module_obj, "show"):
        getattr(module_obj, "show")()

# Map options to original structural layout generation hooks
PG = {
    "home": lambda: safe_render(home),
    "calculator": lambda: safe_render(calculator),
    "liver": lambda: getattr(case_module, "case_page", cases.case_page)("liver"),
    "lung": lambda: getattr(case_module, "case_page", cases.case_page)("lung"),
    "breast": lambda: getattr(case_module, "case_page", cases.case_page)("breast"),
    "johnson": lambda: getattr(case_module, "johnson_page", cases.johnson_page)(),
    "urban": lambda: getattr(case_module, "urban_page", cases.urban_page)(),
    "library": lambda: safe_render(library),
    "videos": lambda: getattr(case_module, "videos_page", cases.videos_page)(),
    "disaster_sandbox": lambda: safe_render(disaster_sandbox),
    "developer_api": lambda: safe_render(developer_api),
    "docs": lambda: safe_render(docs),
    "author": lambda: safe_render(author)
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

# Exact layout module processing routes
if selected_page == "Framework Home": PG["home"]()
elif selected_page == "Live RMTI Calculator": PG["calculator"]()
elif selected_page == "Hepatocellular Carcinoma (HCC) Case Study": PG["liver"]()
elif selected_page == "Non-Small Cell Lung Cancer Case Study": PG["lung"]()
elif selected_page == "HR-Positive Breast Cancer Case Study": PG["breast"]()
elif selected_page == "Johnson Cohort Surveillance Analysis": PG["johnson"]()
elif selected_page == "Sub-Saharan Urban Flooding Case Study": PG["urban"]()
elif selected_page == "Framework Research Library": PG["library"]()
elif selected_page == "Narrated 3D Motion Video Library": PG["videos"]()
elif selected_page == "Disaster Resilience Sandbox": PG["disaster_sandbox"]()
elif selected_page == "Developer API Integration Hub": PG["developer_api"]()
elif selected_page == "Technical Documentation Manual": PG["docs"]()
elif selected_page == "Author Academic Profile": PG["author"]()
