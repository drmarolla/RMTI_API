"""RMTI landing page (Infor-style layout): top bar, hero, key benefits, tool cards, 3D models, API docs.
Saved under the name app.py.py so it is the start page without changing Streamlit settings."""
import sys
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="RMTI Oncoclastics", page_icon="🧬", layout="wide", initial_sidebar_state="collapsed")
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import oncoclastic_style as ui  # noqa: E402

SRC = ROOT / "developer_portal.html"
if not SRC.exists():
    st.error("developer_portal.html was not found next to Home.py. Upload it to the repository root.")
    st.stop()

ui.apply(first_page=True)
ui.topbar([("Risk Calculator", "/Risk_Calculator"), ("HCC Calculator", "/HCC_Calculator"), ("Cohort Sandbox", "/Cohort_Sandbox"),
           ("4D Risk Matrix", "/4D_Risk_Matrix"), ("Live Risk Matrix", "/Live_Risk_Matrix"), ("Case Studies", "/Case_Studies_and_Videos")])

ui.hero_lp(
    "Risk intelligence › RMTI",
    "Time-indexed risk scoring for <em>cancer care</em> and <em>disaster science</em>",
    "Score hazard, exposure, vulnerability and resilience for liver, lung and breast cancer and for floods and heat. "
    "Use the tools in your browser or call the API.",
    ("Open the Risk Calculator", "/Risk_Calculator"), ("See the live matrix", "/Live_Risk_Matrix"))
ui.stats([(4, "levers in one equation", "", ui.RED), (3, "cancer sites: liver, lung, breast", "", ui.BLUE_A),
          (2, "domains: oncology and disaster science", "", ui.RED_L), (8, "scoring and validation endpoints", "", ui.BLUE_L)])

ui.benefits("Key benefits of the RMTI platform", "Everything you need to <b>score, track and explain</b> risk", [
    dict(icon="target", title="One equation, four levers", text="Likelihood, exposure, vulnerability and resilience combine into a single score, R = L · E · V · (1 − ρ).", color=ui.RED),
    dict(icon="gauge", title="Fixed risk tiers", text="A fixed five-band scale (0, 0.05, 0.15, 0.35, 0.60, 1.0) so a score means the same thing every time.", color=ui.BLUE_A),
    dict(icon="trend", title="Trajectory over time", text="Track V(t) and ρ(t) across review cycles: is risk drifting, or is delivery closing the gap?", color=ui.RED),
    dict(icon="users", title="Cohort ranking", text="Rank a cohort and see how the tiers relate to outcomes in the sandbox.", color=ui.BLUE_D),
    dict(icon="liver", title="Liver, lung and breast", text="Published cohorts followed from Stage 1 to Stage 4 and scored with RMTI, with sources cited.", color=ui.BLUE_A),
    dict(icon="pulse", title="Floods and heat", text="The same four levers score disaster hazards, the field the method comes from.", color=ui.RED),
    dict(icon="code", title="Open API", text="Eight scoring and validation endpoints plus the evidence registry. JSON in, JSON out.", color=ui.BLUE_D),
    dict(icon="shield", title="Transparent by design", text="Research prototype on synthetic or published values. Not validated, not a medical device. Apache-2.0.", color=ui.RED),
])

ui.section("Tools", "Choose a tool to get started", "Every tool opens in its own page. Use the menu to move between them at any time.")
ui.path_cards([
    dict(icon="calculator", title="Risk Calculator", text="Snapshot, trajectory, cohort ranking and validation in one place.", tag="Open", color=ui.RED, href="/Risk_Calculator"),
    dict(icon="liver", title="HCC Calculator", text="The liver cancer module, the published application.", tag="Open", color=ui.BLUE_A, href="/HCC_Calculator"),
    dict(icon="users", title="Cohort Sandbox", text="Try cohort ranking with sample data.", tag="Open", color=ui.RED, href="/Cohort_Sandbox"),
    dict(icon="cube", title="4D Risk Matrix", text="See how L, E, V and ρ combine into risk.", tag="Open", color=ui.BLUE_D, href="/4D_Risk_Matrix"),
    dict(icon="pulse", title="Live Risk Matrix", text="New: sliders with the formula and four matrices updating live.", tag="New", color=ui.RED, href="/Live_Risk_Matrix"),
    dict(icon="route", title="RMTI Step by Step", text="Walk through the method one step at a time.", tag="Open", color=ui.BLUE_A, href="/RMTI_Step_by_Step"),
    dict(icon="film", title="Case Studies and Videos", text="Liver, flood and heat case studies.", tag="Open", color=ui.RED, href="/Case_Studies_and_Videos"),
])

ui.industries("3D models", "Cancer-site and <b>disaster models</b>",
              "Drag to turn a model. Liver, lung, breast and disaster science each have their own module.")

PORTAL = ":root,:root:not([data-theme=light]){--surface:#eaf4ff!important;--line:#b9d9f7!important;--muted:#1e3a5f!important;--ink:#0b2545!important;--code:#0b2545!important;--accent:#1d6fd0!important;--bg:#fff!important}.m{background:#d9262c!important}.m.get{background:#1d6fd0!important}.copy{background:#1d6fd0!important;color:#fff!important}"
FIX = """<script>document.addEventListener('click',function(e){var a=e.target.closest('a[href^="#"]');
if(a){e.preventDefault();location.hash=a.getAttribute('href');}});</script></body>"""


def view(css, height):
    html = SRC.read_text(encoding="utf-8").replace("</head>", "<style>" + css + PORTAL + "</style></head>", 1).replace("</body>", FIX, 1)
    components.html(html, height=height, scrolling=True)


view("header.top,.docs,footer,.notice{display:none!important}body{background:#fff}.stage{padding:.5rem 2rem}", 470)
ui.industries("API", "API <b>documentation</b>", "Eight scoring and validation endpoints plus the evidence registry. JSON in, JSON out.")
view("header.top,.stage,footer,.notice{display:none!important}aside{top:8px!important}html{scroll-padding-top:8px!important}", 1000)
video = ROOT / "rmti_1_explained.mp4"
if video.exists():
    with st.expander("▶ Watch: RMTI explained"):
        st.video(str(video))
ui.foot("Oncoclastics Platform on RMTI engine v2.4.0. Apache-2.0. Research use only. drmarolla_rmti@2026")
