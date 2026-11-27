"""Risk Mechanism Theory Index (RMTI) - entry point. streamlit run app.py"""
import os
import streamlit as st
from rmti_ui import inject_css

# Clean, safe individual line imports to eliminate compiler traps
import views.author as author
import views.calculator as calculator
import views.cases as cases
import views.developer_api as developer_api
import views.disaster_sandbox as disaster_sandbox
import views.docs as docs
import views.home as home
import views.library as library

st.set_page_config(page_title="RMTI", page_icon="📊", layout="wide", initial_sidebar_state="expanded")
inject_css()

_NS = "".join(["http://", "www.w3.org/", "2000/svg"])
_SVG = (
    f'<svg xmlns="{_NS}" viewBox="0 0 260 64" width="260" height="64">'
    '<circle cx="32" cy="32" r="25" fill="rgba(56,189,248,0.12)" stroke="#38BDF8" stroke-width="2.4"/>'
    '<text x="68" y="31" font-family="Arial, sans-serif" font-weight="900" font-size="25" fill="#FFFFFF">RMTI</text>'
    '</svg>'
)
st.sidebar.markdown(f'<div style="margin-bottom: 1.5rem;">{_SVG}</div>', unsafe_allow_html=True)

# Safe lookup mapping dictionary
PG = {
    "home": home.render if hasattr(home, 'render') else home.main if hasattr(home, 'main') else lambda: st.info("Loading..."),
    "calculator": calculator.render if hasattr(calculator, 'render') else calculator.main if hasattr(calculator, 'main') else lambda: st.info("Loading..."),
    "liver": lambda: cases.case_page("liver") if hasattr(cases, 'case_page') else st.info("Loading..."),
    "lung": lambda: cases.case_page("lung") if hasattr(cases, 'case_page') else st.info("Loading..."),
    "breast": lambda: cases.case_page("breast") if hasattr(cases, 'case_page') else st.info("Loading..."),
    "johnson": cases.johnson_page if hasattr(cases, 'johnson_page') else lambda: st.info("Loading..."),
    "urban": cases.urban_page if hasattr(cases, 'urban_page') else lambda: st.info("Loading..."),
    "library": library.render if hasattr(library, 'render') else library.main if hasattr(library, 'main') else lambda: st.info("Loading..."),
    "videos": cases.videos_page if hasattr(cases, 'videos_page') else lambda: st.info("Loading..."),
    "disaster_sandbox": disaster_sandbox.render if hasattr(disaster_sandbox, 'render') else disaster_sandbox.main if hasattr(disaster_sandbox, 'main') else lambda: st.info("Loading..."),
    "developer_api": developer_api.render if hasattr(developer_api, 'render') else developer_api.main if hasattr(developer_api, 'main') else lambda: st.info("Loading..."),
    "docs": docs.render if hasattr(docs, 'render') else docs.main if hasattr(docs, 'main') else lambda: st.info("Loading..."),
    "author": author.render if hasattr(author, 'render') else author.main if hasattr(author, 'main') else lambda: st.info("Loading...")
}

menu_options = [
    "Framework Home", "Live RMTI Calculator", "Hepatocellular Carcinoma (HCC) Case Study",
    "Non-Small Cell Lung Cancer Case Study", "HR-Positive Breast Cancer Case Study",
    "Johnson Cohort Surveillance Analysis", "Sub-Saharan Urban Flooding Case Study",
    "Framework Research Library", "Narrated 3D Motion Video Library",
    "Disaster Resilience Sandbox", "Developer API Integration Hub",
    "Technical Documentation Manual", "Author Academic Profile"
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
