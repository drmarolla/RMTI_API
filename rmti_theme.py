"""rmti_theme.py  --  shared look for the app and every page: white, light blue, red. CSS and a top menu only; no data, no network.
Call rmti_theme.apply() once near the top of a page. apply(nav=False) hides the top menu."""
import streamlit as st

NAVY, BLUE, LIGHT, LINE, RED = "#0f2a4a", "#1d6fd0", "#f3f8fd", "#d9e6f2", "#d9262c"

_LOGO = ('<svg viewBox="0 0 40 32" width="30" height="25"><rect x="0" y="16" width="7" height="16" rx="1.5" fill="#6cb4f5"/>'
         '<rect x="10" y="8" width="7" height="24" rx="1.5" fill="#1d6fd0"/><rect x="20" y="0" width="7" height="9" rx="1.5" fill="#d9262c"/>'
         '<rect x="20" y="12" width="7" height="6" rx="1.5" fill="#d9262c"/><rect x="20" y="21" width="7" height="11" rx="1.5" fill="#d9262c"/>'
         '<rect x="30" y="12" width="7" height="20" rx="1.5" fill="#0f2a4a"/></svg>')
_LINKS = [("Risk Calculator", "Risk_Calculator"), ("HCC", "HCC_Calculator"), ("Cohort Sandbox", "Cohort_Sandbox"),
          ("4D Matrix", "4D_Risk_Matrix"), ("Live Matrix", "Live_Risk_Matrix"), ("Step by Step", "RMTI_Step_by_Step"),
          ("Case Studies", "Case_Studies_and_Videos")]


def _alert(kind, bg, bar, fg):   # one rule per Streamlit alert type (warning, info, success, error)
    sel = f'div[data-testid="stAlert"]:has([data-testid="stAlertContent{kind}"])'
    return (f'{sel}{{background:{bg} !important;color:{fg} !important;box-shadow:inset 4px 0 0 {bar};border-radius:10px}}'
            f'{sel} > div{{background:transparent !important;color:{fg} !important}}')


_CSS = f"""
<style>
html, body, [class*="css"] {{ font-family: "Inter", "Segoe UI", system-ui, -apple-system, Roboto, Helvetica, Arial, sans-serif; }}
.block-container {{ padding-top: 1.2rem; max-width: 1400px; }}
h1 {{ font-weight: 800; letter-spacing: -0.02em; color: {NAVY}; }}
h2, h3 {{ letter-spacing: -0.01em; color: {NAVY}; }}
div[data-testid="stMetric"] {{ background: {LIGHT}; border: 1px solid {LINE}; border-radius: 12px; padding: 12px 16px; }}
.stTabs [data-baseweb="tab-list"] {{ gap: 6px; }}
.stTabs [data-baseweb="tab"] {{ font-weight: 600; border-radius: 8px 8px 0 0; padding: 8px 14px; }}
section[data-testid="stSidebar"] {{ border-right: 1px solid {LINE}; }}
div[data-testid="stExpander"] {{ border-radius: 12px; border: 1px solid {LINE}; }}
{_alert("Warning", "#fdf0f0", RED, "#7a1a1d")}
{_alert("Error", "#fde3e4", RED, "#7a1a1d")}
{_alert("Info", "#eaf4ff", BLUE, NAVY)}
{_alert("Success", "#eaf4ff", BLUE, NAVY)}
.rnav {{ display:flex; align-items:center; gap:1.1rem; flex-wrap:wrap; padding:.55rem 0 .8rem; margin:0 0 .8rem; border-bottom:1px solid {LINE}; font-family:Inter,"Segoe UI",system-ui,sans-serif }}
.rnav a {{ text-decoration:none; color:{NAVY}; font-weight:600; font-size:.9rem }} .rnav a:hover {{ color:{BLUE} }}
.rnav .rl {{ display:flex; align-items:center; gap:.45rem }} .rnav .rl span {{ display:flex; flex-direction:column; line-height:1 }}
.rnav .rl b {{ font-size:1.15rem; letter-spacing:.02em }} .rnav .rl small {{ font-size:.45rem; letter-spacing:.3em; color:#4a6482; margin-top:.15rem }}
</style>
"""


def apply(nav=True):
    html = _CSS
    if nav:
        links = "".join(f'<a href="/{s}" target="_self">{t}</a>' for t, s in _LINKS)
        html += f'<div class="rnav"><a class="rl" href="/" target="_self">{_LOGO}<span><b>RMTI</b><small>ONCOCLASTICS</small></span></a>{links}</div>'
    st.markdown(html, unsafe_allow_html=True)
