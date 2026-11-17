"""Oncoclastics / RMTI entrypoint (put this file in the repository ROOT, next to app.py.py).
Main file path in Streamlit Cloud: streamlit_app.py
It uses the site files from the folder oncoclastics_FINAL/ when that folder exists, otherwise from the root,
and keeps using your existing pages (HCC Calculator, Cohort Sandbox, 4D ...) from the root pages/ folder."""
import runpy
import sys
from pathlib import Path

import streamlit as st

REPO = Path(__file__).resolve().parent
_final = REPO / "oncoclastics_FINAL"
SITE = REPO if (REPO / "oncoclastic_style.py").exists() else (_final if _final.exists() else REPO)
for p in (REPO, SITE):                      # SITE ends up first on sys.path, so its newer files win
    if str(p) in sys.path:
        sys.path.remove(str(p))
    sys.path.insert(0, str(p))

# Page config once, here. Existing pages call st.set_page_config again; make those calls harmless.
_orig = getattr(st, "_rmti_set_page_config", None) or st.set_page_config
st._rmti_set_page_config = _orig
_orig(page_title="Oncoclastics \u00b7 RMTI", page_icon="\U0001F9EC", layout="wide", initial_sidebar_state="expanded")
st.set_page_config = lambda *a, **k: None

import oncoclastic_style as ui  # noqa: E402

st.session_state["rmti_nav"] = True


def find(rel, prefer_site=False):
    for base in ((SITE, REPO) if prefer_site else (REPO, SITE)):
        if (base / rel).exists():
            return str(base / rel)
    return None


# (file, title, icon, url_path, prefer the new site copy). Only files that exist are listed.
GROUPS = {
    "Foundation & evidence": [
        ("Home.py", ui.HOME_TITLE, "\U0001F9EC", None, True),
        ("pages/4_RMTI_Step_by_Step.py", "RMTI Step by Step", "\U0001F4D0", "RMTI_Step_by_Step", False),
        ("pages/5_Case_Studies_and_Videos.py", "Case Studies & Videos", "\U0001F3AC", "Case_Studies_and_Videos", False),
        ("pages/8_Johnson_Case_Study.py", "Johnson Case Study (HCC)", "\U0001F4DA", "Johnson_Case_Study", True),
    ],
    "Calculators": [
        ("pages/0_Risk_Calculator.py", "Risk Calculator", "\U0001F9EE", "Risk_Calculator", False),
        ("pages/1_HCC_Calculator.py", "HCC Calculator", "\U0001FA7A", "HCC_Calculator", False),
        ("pages/2_Cohort_Sandbox.py", "Cohort Sandbox", "\U0001F465", "Cohort_Sandbox", False),
    ],
    "4D simulations": [
        ("pages/3_4D_Risk_Matrix.py", "4D Risk Matrix", "\U0001F9CA", "4D_Risk_Matrix", False),
        ("pages/6_Live_4D_Lab.py", "Live 4D Lab", "\U0001F52C", "Live_4D_Lab", False),
        ("pages/7_Live_Risk_Matrix.py", "Live Risk Matrix", "\U0001F4CA", "Live_Risk_Matrix", False),
        ("pages/7_Liver_Progression_4D.py", "Liver Progression 4D", "\U0001F4C8", "Liver_Progression_4D", False),
    ],
    "Developers": [
        ("pages/6_Developer_Portal.py", "Developer Portal & API", "\U0001F50C", "Developer_Portal", False),
    ],
}

if not hasattr(st, "navigation"):
    st.warning("This Streamlit version has no grouped navigation (needs 1.36 or newer). Showing the home page only.")
    runpy.run_path(find("Home.py", True), run_name="__main__")
    st.stop()

nav = {}
for group, items in GROUPS.items():
    pages = []
    for rel, title, icon, url, prefer_site in items:
        path = find(rel, prefer_site)
        if path:
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
ui.apply(first_page=is_home)                # again after the page, so the shared look wins over a page's own colors
