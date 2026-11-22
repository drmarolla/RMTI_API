"""Risk Mechanism Theory Index (RMTI) - Streamlit entry point.   streamlit run app.py"""
import runpy
from pathlib import Path

import streamlit as st

import rmti_core as core
from rmti_ui import inject_css, kpi
from views import developer_api

ROOT = Path(__file__).parent

st.set_page_config(page_title=core.APP_TITLE, page_icon=":material/monitoring:", layout="wide",
                   initial_sidebar_state="expanded")
inject_css()
logo = ROOT / "static" / "rmti_logo.svg"
if logo.exists():
    st.logo(str(logo), size="large")


def _find(*names):
    for n in names:
        for base in (ROOT, ROOT / "pages"):
            if (base / n).exists():
                return base / n
    return None


def _legacy(path: Path):
    """Run an existing page script unchanged (its own set_page_config is ignored)."""
    def run():
        orig = st.set_page_config
        st.set_page_config = lambda *a, **k: None
        try:
            runpy.run_path(str(path), run_name="__main__")
        finally:
            st.set_page_config = orig
    return run


def _page(names, title, icon, slug):
    p = _find(*names)
    return st.Page(_legacy(p), title=title, icon=icon, url_path=slug) if p else None


def home():
    with st.container(border=True, key="hero"):
        left, right = st.columns([1.3, 1], gap="large", vertical_alignment="center")
        with left:
            st.markdown('<span class="pill">Risk Intelligence · RMTI</span>', unsafe_allow_html=True)
            st.markdown('<div class="hero-title">Quantify systemic risk.<br>Before it fragments care.</div>',
                        unsafe_allow_html=True)
            st.markdown('<div class="hero-sub">The Risk Mechanism Theory Index applies hazard–exposure–vulnerability–'
                        'resilience assessment from disaster-risk reduction to clinical oncology, giving '
                        'evidence-based triage across liver, lung and breast cancer.</div>', unsafe_allow_html=True)
            b1, b2, _ = st.columns([1.2, 1.4, 0.6])
            if b1.button("Explore the tools", type="primary", width="stretch"):
                st.switch_page(CALC or DEV)
            if CASES and b2.button("Watch the case study", width="stretch"):
                st.switch_page(CASES)
        with right:
            st.markdown("""
<div class="diagram"><svg viewBox="0 0 260 195" width="100%" style="max-width:300px" role="img" aria-label="R equals L times E times V times one minus rho">
<ellipse cx="130" cy="95" rx="100" ry="70" fill="none" stroke="#CBD5E1" stroke-dasharray="4 4"/>
<ellipse cx="130" cy="95" rx="62" ry="44" fill="none" stroke="#CBD5E1" stroke-dasharray="4 4"/>
<circle cx="130" cy="95" r="24" fill="#BE123C"/><text x="130" y="101" text-anchor="middle" fill="#fff" font-weight="700" font-size="16">R</text>
<text x="130" y="131" text-anchor="middle" fill="#0F172A" font-size="10">Risk</text>
<circle cx="52" cy="40" r="17" fill="#2563EB"/><text x="52" y="45" text-anchor="middle" fill="#fff" font-weight="700" font-size="13">L</text>
<text x="52" y="68" text-anchor="middle" fill="#475569" font-size="10">Likelihood</text>
<circle cx="208" cy="40" r="17" fill="#BE123C"/><text x="208" y="45" text-anchor="middle" fill="#fff" font-weight="700" font-size="13">E</text>
<text x="208" y="68" text-anchor="middle" fill="#475569" font-size="10">Exposure</text>
<circle cx="52" cy="150" r="17" fill="#0F172A"/><text x="52" y="155" text-anchor="middle" fill="#fff" font-weight="700" font-size="13">V</text>
<text x="52" y="180" text-anchor="middle" fill="#475569" font-size="10">Vulnerability</text>
<circle cx="208" cy="150" r="17" fill="#93C5FD"/><text x="208" y="155" text-anchor="middle" fill="#0F172A" font-weight="700" font-size="13">ρ</text>
<text x="208" y="180" text-anchor="middle" fill="#475569" font-size="10">Resilience</text></svg>
<span class="formula">R = L · E · V · (1 − ρ)</span></div>""", unsafe_allow_html=True)
    st.write("")
    cols = st.columns(4, gap="medium")
    for col, (n, l, a) in zip(cols, [("4", "Levers in one unified framework", "red"),
                                     ("3", "Cancer sites: liver, lung, breast", "blue"),
                                     ("2", "Domains: oncology &amp; disaster science", "navy"),
                                     ("3", "Clinical case study walkthroughs", "sky")]):
        col.markdown(kpi(n, l, a), unsafe_allow_html=True)
    st.write("")
    st.caption(core.DISCLAIMER)


HOME = st.Page(home, title="Home", icon=":material/home:", default=True, url_path="home")
CALC = _page(("0_Risk_Calculator.py", "risk_calculator_app.py"), "RMTI Calculator", ":material/calculate:", "rmti-calculator")
LIVE = _page(("7_Live_Risk_Matrix.py",), "Live Risk Matrix", ":material/grid_view:", "live-risk-matrix")
MATRIX = _page(("3_4D_Risk_Matrix.py",), "4D Risk Matrix", ":material/view_in_ar:", "4d-risk-matrix")
CASES = _page(("5_Case_Studies_and_Videos.py", "5_Case_Studies_and_Videos (1).py"), "Case Studies", ":material/movie:", "case-studies")
JOHNSON = _page(("8_Johnson_Case_Study.py",), "Johnson Case Study", ":material/person_search:", "johnson-case")
DEV = st.Page(developer_api.render, title="Developer API", icon=":material/code:", url_path="developer-api")

nav = {"": [HOME],
       "Tools": [p for p in (CALC, LIVE, MATRIX) if p],
       "Evidence": [p for p in (CASES, JOHNSON) if p],
       "Platform": [DEV]}
pg = st.navigation({k: v for k, v in nav.items() if v})

_, b_dev, b_req = st.columns([6, 1.5, 1.9])
if b_dev.button("Developer API", width="stretch", key="top_dev"):
    st.switch_page(DEV)
if b_req.button("Request API access", type="primary", width="stretch", key="top_req"):
    developer_api.request_access_dialog()

pg.run()
