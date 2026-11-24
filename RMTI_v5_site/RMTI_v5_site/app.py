"""Risk Mechanism Theory Index (RMTI) - entry point.   streamlit run app.py"""
import os

import streamlit as st

from engine import APP_TITLE
from rmti_ui import inject_css
from views import calculator, cases, developer_api, docs, hcc_surveillance, hcc_treatment, home, library, live_matrix, matrix4d, models3d, sandbox

st.set_page_config(page_title=APP_TITLE, page_icon=":material/monitoring:", layout="wide", initial_sidebar_state="expanded")
inject_css()
logo = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "rmti_logo.svg")
if os.path.exists(logo):
    st.logo(logo, size="large")


def P(fn, title, icon, slug, default=False):
    return st.Page(fn, title=title, icon=f":material/{icon}:", url_path=slug, default=default)


ROOT = os.path.dirname(os.path.abspath(__file__))
GITHUB_VIDEO_BASE = "https://githubusercontent.com"


def _find_asset(rel_path: str, min_bytes: int = 2048):
    """Walk up from app.py to repo root to find local asset; returns None if missing or LFS pointer."""
    d = ROOT
    for _ in range(4):
        candidate = os.path.join(d, rel_path)
        if os.path.exists(candidate) and os.path.getsize(candidate) >= min_bytes:
            return candidate
        d = os.path.dirname(d)
    return None


@st.dialog("RMTI Clinical Case Studies & 3D Trajectory Models", width="large")
def case_study_dialog():
    v1_mp4 = _find_asset(os.path.join("assets", "videos", "video1_4stages_3d.mp4")) or f"{GITHUB_VIDEO_BASE}/video1_4stages_3d.mp4"
    v1_vtt = _find_asset(os.path.join("assets", "videos", "video1_4stages.vtt"), min_bytes=20)
    v2_mp4 = _find_asset(os.path.join("assets", "videos", "video2_trajectory_3d.mp4")) or f"{GITHUB_VIDEO_BASE}/video2_trajectory_3d.mp4"
    v2_vtt = _find_asset(os.path.join("assets", "videos", "video2_trajectory.vtt"), min_bytes=20)

    tab1, tab2 = st.tabs([
        "Case Study 1: 4-Stage Liver Progression & Cohort Triage",
        "Case Study 2: Time-Indexed Trajectory R(t) & Kalman Filtering",
    ])

    with tab1:
        st.video(v1_mp4, subtitles=v1_vtt)
        st.caption(
            "Hepatocellular carcinoma 4-stage pathological progression & cohort triage (SSRN: 7427450). "
            "Narrated. Click CC in the player bar to toggle closed captions. Research prototype, not a medical device."
        )

    with tab2:
        st.video(v2_mp4, subtitles=v2_vtt)
        st.caption(
            "Longitudinal time-indexed trajectory R(t) with unrounded IR_raw, R_raw, EAL_raw, and steady-state filtered V*(t) "
            "(N = 2,000 synthetic landmark design). Narrated. Click CC in the player bar to toggle closed captions."
        )


PG = {
    "home": P(home.render, "Home", "home", "home", True),
    "calc": P(calculator.render, "RMTI Calculator", "calculate", "rmti-calculator"),
    "hccs": P(hcc_surveillance.render, "HCC Surveillance Calculator", "monitor_heart", "hcc-surveillance"),
    "hcct": P(hcc_treatment.render, "HCC Treatment Calculator", "medication", "hcc-treatment"),
    "sandbox": P(sandbox.render, "Cohort Sandbox", "folder_open", "cohort-sandbox"),
    "models": P(models3d.render, "Interactive Tumor Models", "deployed_code", "tumor-models"),
    "live": P(live_matrix.render, "Live Risk Matrix", "grid_view", "live-risk-matrix"),
    "m4d": P(matrix4d.render, "4D Risk Matrix", "view_in_ar", "4d-risk-matrix"),
    "library": P(library.render, "All case studies", "library_books", "case-studies"),
    "liver": P(cases.liver, "Liver cancer (HCC)", "water_drop", "case-liver"),
    "lung": P(cases.lung, "Lung cancer", "air", "case-lung"),
    "breast": P(cases.breast, "Breast cancer", "favorite", "case-breast"),
    "johnson": P(cases.johnson_page, "HCC pathway (Johnson)", "timeline", "case-hcc-pathway"),
    "urban": P(cases.urban_page, "Six African cities", "location_city", "case-urban"),
    "videos": P(cases.videos_page, "Video library", "movie", "video-library"),
    "method": P(docs.method, "Method and tiers", "functions", "method"),
    "steps": P(docs.steps, "Step by step", "checklist", "step-by-step"),
    "refs": P(docs.references, "References and disclaimer", "menu_book", "references"),
    "api": P(developer_api.render, "Developer API", "code", "developer-api"),
}
home.PAGES = PG
pg = st.navigation({
    "": [PG["home"]],
    "Clinical calculators": [PG["calc"], PG["hccs"], PG["hcct"]],
    "Research tools": [PG["sandbox"]],
    "Interactive models": [PG["models"], PG["live"], PG["m4d"]],
    "Case studies": [PG["library"], PG["liver"], PG["lung"], PG["breast"], PG["johnson"], PG["urban"], PG["videos"]],
    "Documentation": [PG["method"], PG["steps"], PG["refs"]],
    "Platform": [PG["api"]],
})
_, b0, b1, b2 = st.columns([3, 2, 1.5, 2])
if b0.button("Watch the case study", width="stretch", key="top_case"):
    case_study_dialog()
if b1.button("Developer API", width="stretch", key="top_dev"):
    st.switch_page(PG["api"])
if b2.button("Request API access", type="primary", width="stretch", key="top_req"):
    developer_api.request_access_dialog()
pg.run()
