"""
Oncoclastics / RMTI design system for Streamlit.

Usage on EVERY page (first lines after st.set_page_config):

    from ui.theme import inject_theme, top_nav, footer
    inject_theme()
    top_nav(active="Home")

All visuals are pure HTML/CSS/SVG (no JavaScript, no extra packages), so they run
on Streamlit Community Cloud unchanged. Motion respects prefers-reduced-motion.
"""
from __future__ import annotations

import html
import streamlit as st

# ---------------------------------------------------------------- palette
INK = "#0B2545"
BLUE = "#3B52D4"
NAVY = "#2B3A9E"
TEAL = "#4FA095"
DEEP = "#00443F"
AMBER = "#F2A100"
CORAL = "#E8553D"
RED = "#C8344B"
MIST = "#F6F7F9"

DISCLAIMER = (
    "DEMO MODE · public sandbox. Synthetic, illustrative or published aggregate "
    "values only. Do not enter patient data. Not validated · not a medical device · "
    "not for patient-care or emergency decisions."
)

# ---------------------------------------------------------------- CSS
_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@200;300;400;500;600&family=Inter:wght@400;500;600&display=swap');

:root {{
  --ink:{INK}; --blue:{BLUE}; --navy:{NAVY}; --teal:{TEAL}; --deep:{DEEP};
  --amber:{AMBER}; --coral:{CORAL}; --red:{RED}; --mist:{MIST};
  --radius:20px;
}}

html, body, [class*="css"], .stApp {{ font-family:'Inter',system-ui,sans-serif; color:var(--ink); }}
h1,h2,h3,h4 {{ font-family:'Outfit','Inter',sans-serif !important; font-weight:300 !important; letter-spacing:-0.015em; color:var(--ink); }}
h1 {{ font-size:clamp(2.2rem,4.6vw,3.8rem) !important; line-height:1.08 !important; }}
h2 {{ font-size:clamp(1.6rem,2.6vw,2.2rem) !important; }}

/* page chrome */
header[data-testid="stHeader"] {{ background:rgba(255,255,255,.85); backdrop-filter:blur(8px); }}
.block-container {{ max-width:1180px; padding-top:1.2rem; padding-bottom:4rem; }}
section[data-testid="stSidebar"] {{ background:var(--mist); border-right:1px solid #E7E9EE; }}
section[data-testid="stSidebar"] a {{ border-radius:12px; }}

/* buttons -> pill style */
.stButton > button, .stDownloadButton > button, a[data-testid="stPageLink-NavLink"] {{
  border-radius:999px; font-weight:500; transition:transform .15s ease, box-shadow .15s ease;
}}
.stButton > button[kind="primary"] {{ background:var(--blue); border:0; padding:.55rem 1.4rem; }}
.stButton > button:hover {{ transform:translateY(-1px); box-shadow:0 6px 18px rgba(59,82,212,.25); }}

/* page-link pills (top nav) */
a[data-testid="stPageLink-NavLink"] {{
  border:1px solid #E1E4EA; background:#fff; justify-content:center; padding:.35rem .9rem;
}}
a[data-testid="stPageLink-NavLink"]:hover {{ border-color:var(--blue); background:#F1F3FF; transform:translateY(-1px); }}

/* ---------- top brand bar ---------- */
.rm-brand {{ display:flex; align-items:center; gap:.7rem; padding:.2rem 0 .6rem; }}
.rm-brand .mark {{ display:flex; gap:3px; align-items:flex-end; height:34px; }}
.rm-brand .mark i {{ width:9px; border-radius:3px; display:block; animation:bars 2.4s ease-in-out infinite; }}
.rm-brand .mark i:nth-child(1) {{ height:14px; background:var(--blue); }}
.rm-brand .mark i:nth-child(2) {{ height:26px; background:var(--red); animation-delay:.25s; }}
.rm-brand .mark i:nth-child(3) {{ height:20px; background:var(--blue); animation-delay:.5s; }}
.rm-brand b {{ font-family:'Outfit'; font-weight:500; font-size:1.5rem; line-height:1; }}
.rm-brand small {{ display:block; letter-spacing:.32em; font-size:.62rem; color:#6B7A90; margin-top:3px; }}
@keyframes bars {{ 0%,100%{{transform:scaleY(1)}} 50%{{transform:scaleY(.68)}} }}
.rm-brand .mark i {{ transform-origin:bottom; }}

/* ---------- hero ---------- */
.rm-hero {{ position:relative; overflow:hidden; border-radius:28px; padding:3.2rem 3rem 3rem;
  background:linear-gradient(120deg,#FFFFFF 0%, #F6F7F9 60%, #EEF1FF 100%); border:1px solid #E7E9EE; min-height:430px; }}
.rm-hero .eyebrow {{ font-size:.78rem; font-weight:600; letter-spacing:.2em; text-transform:uppercase; color:var(--red); }}
.rm-hero h1 {{ margin:.7rem 0 1rem; max-width:620px; }}
.rm-hero p.lead {{ max-width:520px; font-size:1.08rem; line-height:1.6; color:#33465F; }}
.rm-hero .cta {{ display:inline-block; margin-top:1.4rem; background:var(--blue); color:#fff !important; text-decoration:none !important;
  padding:.8rem 1.7rem; border-radius:999px; font-weight:500; transition:transform .15s, box-shadow .15s; }}
.rm-hero .cta:hover {{ transform:translateY(-2px); box-shadow:0 10px 24px rgba(59,82,212,.3); }}
.rm-hero svg.art {{ position:absolute; right:-40px; top:0; height:100%; width:55%; min-width:360px; pointer-events:none; }}
.rm-hero .copy {{ position:relative; z-index:2; }}
@media (max-width:900px) {{ .rm-hero svg.art {{ opacity:.25; width:90%; }} .rm-hero {{ padding:2rem 1.4rem; }} }}

.art .f1 {{ animation:floatA 7s ease-in-out infinite; }}
.art .f2 {{ animation:floatB 9s ease-in-out infinite; }}
.art .f3 {{ animation:floatA 11s ease-in-out infinite reverse; }}
.art .spin {{ transform-origin:300px 220px; animation:spin 26s linear infinite; }}
.art .pulse {{ transform-box:fill-box; transform-origin:center; animation:pulse 3.6s ease-in-out infinite; }}
.art .dash {{ stroke-dasharray:6 10; animation:dash 3s linear infinite; }}
@keyframes floatA {{ 0%,100%{{transform:translate(0,0)}} 50%{{transform:translate(-18px,14px)}} }}
@keyframes floatB {{ 0%,100%{{transform:translate(0,0)}} 50%{{transform:translate(16px,-16px)}} }}
@keyframes spin {{ to{{transform:rotate(360deg)}} }}
@keyframes pulse {{ 0%,100%{{transform:scale(1)}} 50%{{transform:scale(1.18)}} }}
@keyframes dash {{ to{{stroke-dashoffset:-64}} }}

/* ---------- animated stat counters (pure CSS) ---------- */
@property --n {{ syntax:'<integer>'; initial-value:0; inherits:false; }}
.rm-stats {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); gap:1rem; margin:1.4rem 0 .4rem; }}
.rm-stat {{ background:#fff; border:1px solid #E7E9EE; border-radius:var(--radius); padding:1.2rem 1.3rem; position:relative; overflow:hidden;
  transition:transform .2s, box-shadow .2s; }}
.rm-stat:hover {{ transform:translateY(-4px); box-shadow:0 14px 30px rgba(11,37,69,.08); }}
.rm-stat::before {{ content:""; position:absolute; left:0; top:0; height:4px; width:100%; background:var(--c,var(--blue)); }}
.rm-stat .num {{ font-family:'Outfit'; font-weight:300; font-size:2.6rem; line-height:1.1; counter-reset:n var(--n);
  animation:count 1.8s cubic-bezier(.2,.7,.2,1) forwards; }}
.rm-stat .num::after {{ content:counter(n) var(--suffix,""); }}
.rm-stat .lbl {{ font-size:.86rem; color:#5B6B80; margin-top:.2rem; }}
@keyframes count {{ from{{--n:0}} to{{--n:var(--to)}} }}

/* ---------- logo / credibility strip ---------- */
.rm-strip {{ background:var(--mist); border-radius:var(--radius); padding:1.1rem 1.6rem; display:flex; align-items:center; gap:2rem; flex-wrap:wrap; margin:1.6rem 0; }}
.rm-strip span.t {{ color:#6B7A90; font-size:.85rem; max-width:140px; }}
.rm-strip .chip {{ font-family:'Outfit'; font-weight:500; font-size:1.05rem; color:#4A5A70; opacity:.8; }}

/* ---------- pathway cards ---------- */
.rm-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(250px,1fr)); gap:1.1rem; margin:1rem 0 2rem; }}
.rm-card {{ border:1px solid #E7E9EE; border-radius:var(--radius); padding:1.5rem; background:#fff; position:relative; overflow:hidden;
  transition:transform .22s, box-shadow .22s, border-color .22s; }}
.rm-card:hover {{ transform:translateY(-6px); box-shadow:0 18px 38px rgba(11,37,69,.10); border-color:var(--c,var(--blue)); }}
.rm-card .ico {{ width:54px; height:54px; border-radius:16px; display:grid; place-items:center; background:color-mix(in srgb,var(--c,var(--blue)) 12%,white); margin-bottom:1rem; }}
.rm-card .ico svg {{ width:30px; height:30px; stroke:var(--c,var(--blue)); fill:none; stroke-width:1.8; stroke-linecap:round; stroke-linejoin:round; }}
.rm-card:hover .ico svg {{ animation:wiggle .7s ease; }}
@keyframes wiggle {{ 0%,100%{{transform:rotate(0)}} 30%{{transform:rotate(-10deg) scale(1.08)}} 60%{{transform:rotate(8deg)}} }}
.rm-card h4 {{ margin:0 0 .35rem; font-size:1.25rem !important; font-weight:400 !important; }}
.rm-card p {{ margin:0; color:#47586F; font-size:.93rem; line-height:1.55; }}
.rm-card .tag {{ display:inline-block; margin-top:.9rem; font-size:.72rem; font-weight:600; letter-spacing:.12em; text-transform:uppercase; color:var(--c,var(--blue)); }}

/* ---------- equation banner ---------- */
.rm-eq {{ background:linear-gradient(135deg,#0B2545,#12396B); color:#fff; border-radius:24px; padding:2rem 2.2rem; margin:1.4rem 0; position:relative; overflow:hidden; }}
.rm-eq::after {{ content:""; position:absolute; right:-60px; top:-60px; width:220px; height:220px; border-radius:50%; background:radial-gradient(circle,rgba(79,160,149,.55),transparent 70%); animation:pulse 5s ease-in-out infinite; }}
.rm-eq .formula {{ font-family:'Outfit'; font-weight:300; font-size:clamp(1.8rem,4vw,2.9rem); letter-spacing:.02em; }}
.rm-eq .formula em {{ font-style:normal; color:var(--amber); }}
.rm-eq .legend {{ display:flex; gap:1.4rem; flex-wrap:wrap; margin-top:.8rem; font-size:.88rem; color:#C9D6EA; }}

/* ---------- alert / callout ---------- */
.rm-demo {{ border:1px solid #F0B8BF; background:#FFF4F5; color:#7A1E2C; border-radius:14px; padding:.75rem 1rem; font-size:.86rem; margin:.5rem 0 1rem; }}
.rm-demo b {{ color:#9B1B30; }}
.rm-callout {{ border-left:4px solid var(--red); background:#fff; border-radius:0 var(--radius) var(--radius) 0; padding:1.3rem 1.6rem; box-shadow:0 1px 0 #E7E9EE, 0 0 0 1px #F0F1F4; line-height:1.7; }}

/* ---------- section header ---------- */
.rm-sec {{ margin:2.4rem 0 .6rem; }}
.rm-sec .k {{ font-size:.75rem; letter-spacing:.2em; text-transform:uppercase; color:var(--red); font-weight:600; }}
.rm-sec h2 {{ margin:.2rem 0 0; }}
.rm-sec p {{ color:#47586F; max-width:680px; margin:.3rem 0 0; }}

/* ---------- metrics / dataframes / plots ---------- */
[data-testid="stMetric"] {{ background:#fff; border:1px solid #E7E9EE; border-radius:var(--radius); padding:1rem 1.2rem; }}
[data-testid="stMetricValue"] {{ font-family:'Outfit'; font-weight:300; }}
[data-testid="stDataFrame"], [data-testid="stPlotlyChart"] {{ border-radius:var(--radius); overflow:hidden; }}
[data-testid="stExpander"] {{ border-radius:var(--radius); border:1px solid #E7E9EE; }}
.stTabs [data-baseweb="tab-list"] {{ gap:.4rem; }}
.stTabs [data-baseweb="tab"] {{ border-radius:999px; padding:.4rem 1rem; background:var(--mist); }}
.stTabs [aria-selected="true"] {{ background:var(--blue) !important; color:#fff !important; }}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] {{ display:none; }}

/* ---------- footer ---------- */
.rm-foot {{ margin-top:3rem; padding-top:1.2rem; border-top:1px solid #E7E9EE; font-size:.8rem; color:#6B7A90; display:flex; justify-content:space-between; flex-wrap:wrap; gap:.6rem; }}

/* reveal on load */
.rm-hero, .rm-card, .rm-stat, .rm-eq {{ animation:rise .7s ease both; }}
.rm-grid .rm-card:nth-child(2) {{ animation-delay:.08s }} .rm-grid .rm-card:nth-child(3) {{ animation-delay:.16s }}
.rm-grid .rm-card:nth-child(4) {{ animation-delay:.24s }} .rm-grid .rm-card:nth-child(5) {{ animation-delay:.32s }}
@keyframes rise {{ from{{opacity:0; transform:translateY(16px)}} to{{opacity:1; transform:none}} }}

@media (prefers-reduced-motion: reduce) {{ * {{ animation:none !important; transition:none !important; }}
  .rm-stat .num {{ --n:var(--to); }} }}
</style>
"""

# ---------------------------------------------------------------- icons (Lucide-style paths)
ICONS = {
    "calculator": '<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M8 7h8M8 12h.01M12 12h.01M16 12h.01M8 16h.01M12 16h.01M16 16h.01"/>',
    "liver": '<path d="M3 11c0-4 4-6 9-6s9 2 9 6c0 5-5 8-10 8-3 0-4-2-6-3-1-1-2-2-2-5z"/><path d="M12 9v4"/>',
    "users": '<circle cx="9" cy="8" r="3.2"/><path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6"/><circle cx="17" cy="9" r="2.4"/><path d="M17 14c2.5 0 4 1.8 4 4"/>',
    "cube": '<path d="M12 3l8 4.5v9L12 21l-8-4.5v-9z"/><path d="M12 12l8-4.5M12 12L4 7.5M12 12v9"/>',
    "route": '<circle cx="6" cy="18" r="2.5"/><circle cx="18" cy="6" r="2.5"/><path d="M8.5 18H15a3 3 0 000-6H9a3 3 0 010-6h6.5"/>',
    "book": '<path d="M4 5a2 2 0 012-2h13v16H6a2 2 0 00-2 2z"/><path d="M4 21V5M9 8h6"/>',
    "pulse": '<path d="M3 12h4l2-6 4 12 2-6h6"/>',
    "code": '<path d="M8 8l-5 4 5 4M16 8l5 4-5 4M14 5l-4 14"/>',
    "shield": '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/><path d="M9 12l2 2 4-4"/>',
}


def icon(name: str) -> str:
    return f'<svg viewBox="0 0 24 24" aria-hidden="true">{ICONS[name]}</svg>'


# ---------------------------------------------------------------- hero art
def _hero_art() -> str:
    """Overlapping, slowly moving shapes in the spirit of modern health-tech brand art."""
    return f"""
<svg class="art" viewBox="0 0 600 440" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
  <g class="f1"><rect x="330" y="40" width="300" height="110" rx="55" fill="{TEAL}" opacity=".9"/></g>
  <g class="f2" style="mix-blend-mode:multiply">
    <circle cx="300" cy="230" r="150" fill="{AMBER}" opacity=".92"/>
    <circle cx="420" cy="230" r="150" fill="{BLUE}" opacity=".88"/>
    <circle cx="540" cy="230" r="120" fill="{TEAL}" opacity=".8"/>
  </g>
  <circle cx="360" cy="230" r="56" fill="#fff"/>
  <g class="spin"><path d="M300 90 A140 140 0 0 1 440 220" fill="none" stroke="{DEEP}" stroke-width="26" stroke-linecap="round"/></g>
  <circle class="pulse" cx="420" cy="110" r="24" fill="{NAVY}"/>
  <circle class="pulse" cx="420" cy="350" r="24" fill="{NAVY}" style="animation-delay:1.2s"/>
  <g class="f3"><path d="M180 330 q60 -70 120 0 t120 0" fill="none" stroke="{CORAL}" stroke-width="5" stroke-linecap="round" class="dash"/></g>
  <circle class="pulse" cx="150" cy="120" r="12" fill="{CORAL}" style="animation-delay:.6s"/>
</svg>"""


# ---------------------------------------------------------------- public API
def inject_theme() -> None:
    """Call once per page, right after st.set_page_config()."""
    st.markdown(_CSS, unsafe_allow_html=True)


def brand() -> None:
    st.markdown(
        '<div class="rm-brand"><div class="mark"><i></i><i></i><i></i></div>'
        '<div><b>RMTI</b><small>ONCOCLASTICS</small></div></div>',
        unsafe_allow_html=True,
    )


NAV = [
    ("Home", "Home.py"),
    ("Risk Calculator", "pages/Risk_Calculator.py"),
    ("HCC Calculator", "pages/HCC_Calculator.py"),
    ("Cohort Sandbox", "pages/Cohort_Sandbox.py"),
    ("4D Risk Matrix", "pages/4D_Risk_Matrix.py"),
    ("Case Studies", "pages/Case_Studies_and_Videos.py"),
]


def top_nav(active: str = "Home", nav: list[tuple[str, str]] | None = None) -> None:
    """Brand + pill navigation. Edit NAV paths to match your /pages file names."""
    brand()
    items = nav or NAV
    cols = st.columns(len(items))
    for col, (label, path) in zip(cols, items):
        with col:
            try:
                st.page_link(path, label=label)
            except Exception:  # path mismatch should never crash a page
                st.caption(label)


def hero(eyebrow: str, title: str, lead: str, cta_label: str = "Explore the platform", cta_href: str = "#pathways") -> None:
    st.markdown(
        f"""<div class="rm-hero">{_hero_art()}
        <div class="copy">
          <div class="eyebrow">{html.escape(eyebrow)}</div>
          <h1>{title}</h1>
          <p class="lead">{html.escape(lead)}</p>
          <a class="cta" href="{html.escape(cta_href)}">{html.escape(cta_label)}</a>
        </div></div>""",
        unsafe_allow_html=True,
    )


def stats(items: list[tuple[int, str, str, str]]) -> None:
    """items = [(value:int, label:str, suffix:str, css_color)]. Counts up on load."""
    cells = "".join(
        f'<div class="rm-stat" style="--to:{v};--suffix:\'{html.escape(s)}\';--c:{c}">'
        f'<div class="num"></div><div class="lbl">{html.escape(l)}</div></div>'
        for v, l, s, c in items
    )
    st.markdown(f'<div class="rm-stats">{cells}</div>', unsafe_allow_html=True)


def strip(label: str, names: list[str]) -> None:
    chips = "".join(f'<span class="chip">{html.escape(n)}</span>' for n in names)
    st.markdown(f'<div class="rm-strip"><span class="t">{html.escape(label)}</span>{chips}</div>', unsafe_allow_html=True)


def section(kicker: str, title: str, text: str = "", anchor: str = "") -> None:
    a = f'<a id="{anchor}"></a>' if anchor else ""
    p = f"<p>{html.escape(text)}</p>" if text else ""
    st.markdown(
        f'{a}<div class="rm-sec"><div class="k">{html.escape(kicker)}</div><h2>{html.escape(title)}</h2>{p}</div>',
        unsafe_allow_html=True,
    )


def cards(items: list[dict]) -> None:
    """items = [{icon, title, text, tag, color}]"""
    out = "".join(
        f'<div class="rm-card" style="--c:{i.get("color", BLUE)}"><div class="ico">{icon(i["icon"])}</div>'
        f'<h4>{html.escape(i["title"])}</h4><p>{html.escape(i["text"])}</p>'
        f'<span class="tag">{html.escape(i.get("tag", ""))}</span></div>'
        for i in items
    )
    st.markdown(f'<div class="rm-grid">{out}</div>', unsafe_allow_html=True)


def equation_banner() -> None:
    st.markdown(
        """<div class="rm-eq"><div class="formula">R = <em>L</em> · <em>E</em> · <em>V</em> · (1 − <em>ρ</em>)</div>
        <div class="legend"><span><b>L</b> hazard</span><span><b>E</b> exposure</span>
        <span><b>V</b> vulnerability</span><span><b>ρ</b> resilience / care-system</span></div></div>""",
        unsafe_allow_html=True,
    )


def demo_banner(text: str = DISCLAIMER) -> None:
    st.markdown(f'<div class="rm-demo"><b>{html.escape(text.split("·")[0].strip())}</b> · {html.escape("·".join(text.split("·")[1:]).strip())}</div>', unsafe_allow_html=True)


def callout(markdown_html: str) -> None:
    st.markdown(f'<div class="rm-callout">{markdown_html}</div>', unsafe_allow_html=True)


def footer() -> None:
    st.markdown(
        '<div class="rm-foot"><span>Core logic created and formulated by Dr. Cesar Marolla · Quantifying systemic risk in disaster science and oncology</span>'
        '<span>Demo · not a medical device</span></div>',
        unsafe_allow_html=True,
    )
