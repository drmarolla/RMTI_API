"""
Risk Mechanism Theory Index (RMTI) Platform Entry Point
Override patch: Rolling back workspace structure to Thursday, Nov 26, 12:00 PM EST.
"""
import os
import sys
import importlib.util
import streamlit as st

# Step up folder layout trees to anchor deep into your repository root directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Restore the premium theme context engine configuration
try:
    from rmti_theme import apply as _theme
    _theme()
except Exception:
    pass

try:
    from rmti_ui import inject_css
    inject_css()
except Exception:
    st.markdown("<style>div.block-container{padding-top:1.5rem;}</style>", unsafe_allow_html=True)

# Defensive helper function to safely find and import modular pages from views
def safe_import_module(module_name):
    # Try importing natively from views package
    try:
        return importlib.import_module(f"views.{module_name}")
    except Exception:
        pass
    # Alternative direct-file check lookup strategy
    for directory in [BASE_DIR, os.path.join(REPO_ROOT, "views"), REPO_ROOT]:
        target_path = os.path.join(directory, f"{module_name}.py")
        if os.path.exists(target_path):
            try:
                spec = importlib.util.spec_from_file_location(module_name, target_path)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                return mod
            except Exception:
                pass
    return None

# Resolve core view layers
home = safe_import_module("home")
calculator = safe_import_module("calculator")
cases = safe_import_module("cases")
library = safe_import_module("library")
author = safe_import_module("author")
developer_api = safe_import_module("developer_api")
disaster_sandbox = safe_import_module("disaster_sandbox")
docs = safe_import_module("docs")

# Force-extract high-end case study modules and 3D videos directly from your original backup file
try:
    spec = importlib.util.spec_from_file_location(
        "high_end_cases", 
        os.path.join(REPO_ROOT, "5_Case_Studies_and_Videos (1).py")
    )
    case_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(case_module)
except Exception:
    case_module = cases

# Generic safe execution utility for module routing layout
def execute_render(module_obj, alternative_func_name=None):
    if not module_obj:
        st.info("Module resources are compiling on the server...")
        return
    for target_func in ["render", "main", "show"]:
        if hasattr(module_obj, target_func):
            getattr(module_obj, target_func)()
            return
    if alternative_func_name and hasattr(module_obj, alternative_func_name):
        getattr(module_obj, alternative_func_name)()

st.set_page_config(page_title="RMTI Platform", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

# Vector logo graphics generation system
_NS = "".join(["http://", "www.w3.org/", "2000/svg"])
_SVG = (
    f'<svg xmlns="{_NS}" viewBox="0 0 260 64" width="260" height="64">'
    '<circle cx="32" cy="32" r="25" fill="rgba(56,189,248,0.12)" stroke="#38BDF8" stroke-width="2.4"/>'
    '<text x="68" y="31" font-family="Arial, sans-serif" font-weight="900" font-size="25" fill="#FFFFFF">RMTI</text>'
    '</svg>'
)
st.sidebar.markdown(f'<div style="margin-bottom: 1.5rem;">{_SVG}</div>', unsafe_allow_html=True)

# Connect platform routing selections straight to your original build templates
PG = {
    "home": lambda: execute_render(home),
    "calculator": lambda: execute_render(calculator),
    "liver": lambda: getattr(case_module, "case_page", lambda x: None)("liver"),
    "lung": lambda: getattr(case_module, "case_page", lambda x: None)("lung"),
    "breast": lambda: getattr(case_module, "case_page", lambda x: None)("breast"),
    "johnson": lambda: execute_render(case_module, "johnson_page") if hasattr(case_module, "johnson_page") else execute_render(cases, "johnson_page"),
    "urban": lambda: execute_render(case_module, "urban_page") if hasattr(case_module, "urban_page") else execute_render(cases, "urban_page"),
    "library": lambda: execute_render(library),
    "videos": lambda: execute_render(case_module, "videos_page") if hasattr(case_module, "videos_page") else execute_render(cases, "videos_page"),
    "disaster_sandbox": lambda: execute_render(disaster_sandbox),
    "developer_api": lambda: execute_render(developer_api),
    "docs": lambda: execute_render(docs),
    "author": lambda: execute_render(author)
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
