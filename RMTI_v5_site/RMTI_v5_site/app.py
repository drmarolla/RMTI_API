"""Risk Mechanism Theory Index (RMTI) - entry point. streamlit run app.py"""
import os
import streamlit as st
from rmti_ui import inject_css

# Original unmodified application views imports
from views import author, calculator, cases, developer_api, disaster_sandbox, docs, home, library, urban_cases

st.set_page_config(page_title="RMTI", page_icon="📊", layout="wide", initial_sidebar_state="expanded")
inject_css()

_NS = "".join(["http://", "www.w3.org/", "2000/svg"])
_SVG = (
    f'<svg xmlns="{_NS}" viewBox="0 0 260 64" width="260" height="64">'
    '<circle cx="32" cy="32" r="25" fill="rgba(56,189,248,0.12)" stroke="#38BDF8" stroke-width="2.4"/>'
    '<text x="68" y="31" font-family="Arial, sans-serif" font-weight="900" font-size="25" letter-spacing="1.4" fill="#FFFFFF">RMTI</text>'
    '</svg>'
)
st.sidebar.markdown(f'<div style="margin-bottom: 1.5rem;">{_SVG}</div>', unsafe_allow_html=True)

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
    home.render()
elif selected_page == "Live RMTI Calculator":
    calculator.render()
elif selected_page == "Hepatocellular Carcinoma (HCC) Case Study":
    cases.case_page("liver")
elif selected_page == "Non-Small Cell Lung Cancer Case Study":
    cases.case_page("lung")
elif selected_page == "HR-Positive Breast Cancer Case Study":
    cases.case_page("breast")
elif selected_page == "Johnson Cohort Surveillance Analysis":
    cases.johnson_page()
elif selected_page == "Sub-Saharan Urban Flooding Case Study":
    urban_cases.render()
elif selected_page == "Framework Research Library":
    library.render()
elif selected_page == "Narrated 3D Motion Video Library":
    cases.videos_page()
elif selected_page == "Disaster Resilience Sandbox":
    disaster_sandbox.render()
elif selected_page == "Developer API Integration Hub":
    developer_api.render()
elif selected_page == "Technical Documentation Manual":
    docs.render()
elif selected_page == "Author Academic Profile":
    author.render()
