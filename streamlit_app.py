"""Oncoclastics / RMTI entrypoint with grouped navigation.
Set Main file path to streamlit_app.py in Streamlit Cloud (Settings). Home.py still works on its own if you prefer the old layout."""
import runpy
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# Page config once, here. Existing pages call st.set_page_config again; make those calls harmless.
_orig = getattr(st, "_rmti_set_page_config", None) or st.set_page_config
st._rmti_set_page_config = _orig
_orig(page_title="Oncoclastics \u00b7 RMTI", page_icon="\U0001F9EC", layout="wide", initial_sidebar_state="expanded")
st.set_page_config = lambda *a, **k: None

import oncoclastic_style as ui  # noqa: E402

st.session_state["rmti_nav"] = True

# (file, title, icon, url_path): only files that exist are listed, so a missing page never breaks the app.
GROUPS = {
    "Foundation & evidence": [
        ("Home.py", ui.HOME_TITLE, "\U0001F9EC", None),
        ("pages/4_RMTI_Step_by_Step.py", "RMTI Step by Step", "\U0001F4D0", "RMTI_Step_by_Step"),
        ("pages/5_Case_Studies_and_Videos.py", "Case Studies & Videos", "\U0001F3AC", "Case_Studies_and_Videos"),
        ("pages/8_Johnson_Case_Study.py", "Johnson Case Study (HCC)", "\U0001F4DA", "Johnson_Case_Study"),
    ],
    "Calculators": [
        ("pages/0_Risk_Calculator.py", "Risk Calculator", "\U0001F9EE", "Risk_Calculator"),
        ("pages/1_HCC_Calculator.py", "HCC Calculator", "\U0001FA7A", "HCC_Calculator"),
        ("pages/2_Cohort_Sandbox.py", "Cohort Sandbox", "\U0001F465", "Cohort_Sandbox"),
    ],
    "4D simulations": [
        ("pages/3_4D_Risk_Matrix.py", "4D Risk Matrix", "\U0001F9CA", "4D_Risk_Matrix"),
        ("pages/6_Live_4D_Lab.py", "Live 4D Lab", "\U0001F52C", "Live_4D_Lab"),
        ("pages/7_Live_Risk_Matrix.py", "Live Risk Matrix", "\U0001F4CA", "Live_Risk_Matrix"),
        ("pages/7_Liver_Progression_4D.py", "Liver Progression 4D", "\U0001F4C8", "Liver_Progression_4D"),
    ],
    "Developers": [
        ("pages/6_Developer_Portal.py", "Developer Portal & API", "\U0001F50C", "Developer_Portal"),
    ],
}

if not hasattr(st, "navigation"):
    st.warning("This Streamlit version has no grouped navigation (needs 1.36 or newer). Showing the home page only.")
    runpy.run_path(str(ROOT / "Home.py"), run_name="__main__")
    st.stop()

nav = {}
for group, items in GROUPS.items():
    pages = []
    for path, title, icon, url in items:
        if (ROOT / path).exists():
            kw = {"url_path": url} if url else {"default": True}
            pages.append(st.Page(path, title=title, icon=icon, **kw))
    if pages:
        nav[group] = pages

pg = st.navigation(nav)
with st.sidebar:
    st.caption(f"RMTI engine {ui.ENGINE_VERSION} \u00b7 research prototype")
is_home = pg.title == ui.HOME_TITLE
ui.apply(first_page=is_home)
if not is_home:
    ui.governance_bar()
pg.run()
