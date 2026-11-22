"""Oncoclastics / RMTI: ONE-FILE site entry. Main file path in Streamlit Cloud: streamlit_app.py
Self-contained: look, new home page, grouped navigation. Uses your existing pages if they are in the repository
(root pages/ folder), and animation/index.html if present. Nothing else is required."""
import html as _html
import runpy
import sys
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

BUILD = "2026-11-22-e"
REPO = Path(__file__).resolve().parent
_ROOT = REPO
BASES = [REPO] + ([REPO.parent] if (REPO.parent / "app.py.py").exists() and REPO.parent != REPO else [])
for _p in reversed(BASES):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

# page config once; pages call it again, so make later calls harmless
_orig = getattr(st, "_rmti_set_page_config", None) or st.set_page_config
st._rmti_set_page_config = _orig
_orig(page_title="Oncoclastics \u00b7 RMTI", page_icon="\U0001F9EC", layout="wide", initial_sidebar_state="expanded")
st.set_page_config = lambda *a, **k: None

import base64  # noqa: E402

# ---- calm filter: softens CSS that other modules inject with st.markdown / st.html (hard outlines, heavy type, vivid fills) ----
import colorsys  # noqa: E402
import re  # noqa: E402

_RAW_MD = getattr(st, "_rmti_raw_markdown", None) or st.markdown
st._rmti_raw_markdown = _RAW_MD


def _vivid(m):
    h = m.group(0)
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
    hh, ll, ss = colorsys.rgb_to_hls(r, g, b)
    if ss >= 0.55 and 0.28 <= ll <= 0.62:
        if hh <= 0.05 or hh >= 0.94:
            return "#c9505a"
        if 0.5 <= hh <= 0.7:
            return "#4a86c5"
    return h


def _block(m):
    body = m.group(1)
    if re.search(r"position\s*:\s*fixed", body) and re.search(r"bottom\s*:\s*0", body):
        body = re.sub(r"position\s*:\s*fixed", "position:static", body)
    return "{" + body + "}"


def _soft_shadow(m):
    v = m.group(2)
    if re.search(r"(?<![\d.])(?:[3-9]|\d{2})px\s+(?:[3-9]|\d{2})px\s+0", v + " "):
        return m.group(1) + "0 1px 2px rgba(15,39,64,.06),0 6px 18px rgba(15,39,64,.05)"
    return m.group(0)


def _calm_css(css):
    css = re.sub(r"\{([^{}]*)\}", _block, css)
    css = re.sub(r"(box-shadow\s*:\s*)([^;}]*)", _soft_shadow, css)
    css = re.sub(r"(border(?:-top|-right|-bottom)?\s*:\s*)(?:[2-9]|\d{2})px(\s+solid)\s+[^;}!]+", r"\g<1>1px\2 #d9e4ef", css)
    css = re.sub(r"(border-left\s*:\s*)(?:[4-9]|\d{2})px", r"\g<1>3px", css)
    css = re.sub(r"font-weight\s*:\s*(?:800|900)", "font-weight:650", css)
    css = re.sub(r"font-weight\s*:\s*700", "font-weight:600", css)
    return re.sub(r"#[0-9a-fA-F]{6}\b", _vivid, css)


def _calm_body(body):
    if isinstance(body, str) and "<style" in body:
        return re.sub(r"(<style[^>]*>)(.*?)(</style>)", lambda m: m.group(1) + _calm_css(m.group(2)) + m.group(3), body, flags=re.S)
    return body


def _wrap(fn):
    def inner(body, *a, **k):
        return fn(_calm_body(body), *a, **k)
    inner._calm = True
    return inner


if not getattr(st.markdown, "_calm", False):
    st.markdown = _wrap(st.markdown)
    if hasattr(st, "html") and not getattr(st.html, "_calm", False):
        st.html = _wrap(st.html)


RED, RED_D = "#c9505a", "#a93f48"                   # primary action color
BLUE, BLUE_M, LINE = "#eef5fb", "#d6e6f4", "#d9e4ef"  # soft light-blue surfaces and borders
INK, BODY, MUTED = "#1f2d3d", "#334155", "#5d6d80"     # headings, body text, secondary text
ENGINE_VERSION = "v2.4.0"
YEAR, OWNER, ORCID = 2026, "Dr. Cesar Marolla", "0000-0001-8498-7380"
HOME_TITLE = "Overview & Oncoclastics"

_DEFAULT_LOGO = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 250 64">'
    f'<rect x="6" y="38" width="9" height="18" rx="1.5" fill="#5b9bd5"/>'
    f'<rect x="19" y="26" width="9" height="30" rx="1.5" fill="{RED}"/>'
    f'<rect x="32" y="34" width="9" height="22" rx="1.5" fill="#5b9bd5"/>'
    f'<circle cx="23.5" cy="15" r="4.5" fill="{RED}"/>'
    f'<text x="54" y="37" font-family="Arial,Helvetica,sans-serif" font-size="27" fill="{INK}">RMTI</text>'
    f'<text x="55" y="54" font-family="Arial,Helvetica,sans-serif" font-size="10" letter-spacing="3" fill="{MUTED}">ONCOCLASTICS</text>'
    '</svg>')

_CSS = """
.stApp,[data-testid="stAppViewContainer"]{background:#fff;color:%BODY%}
html,body,.stApp{font-size:17px;line-height:1.65}
h1,h2,h3,h4{color:%INK%;font-weight:600;letter-spacing:-.01em}
h1{font-size:2.05rem}h2{font-size:1.5rem;margin-top:1.8rem}h3{font-size:1.2rem}
p,li{color:%BODY%}
a{color:#3b78b4}
[data-testid="stCaptionContainer"],.stCaption{color:%MUTED%}
.block-container,[data-testid="stMainBlockContainer"]{max-width:1100px;padding-top:4.5rem;padding-bottom:3rem}
[data-testid="stSidebar"]{background:%BLUE%;border-right:1px solid %LINE%}
[data-testid="stSidebarNav"]{padding-top:.4rem}
[data-testid="stSidebarNav"] ul{padding:0;margin:0;gap:0}
[data-testid="stSidebarNav"] li{margin:0}
[data-testid="stSidebarNavLink"]{padding:.28rem .7rem;margin:1px 0;min-height:0;border-radius:6px;font-size:.95rem}
[data-testid="stSidebarNavLink"] span{line-height:1.25}
[data-testid="stSidebarNavLink"][aria-current="page"]{background:%BLUE_M%;font-weight:600}
[data-testid="stSidebarNavSeparator"],[data-testid="stNavSectionHeader"]{color:%MUTED%;font-size:.72rem;letter-spacing:.08em;text-transform:uppercase}
.stButton>button,.stDownloadButton>button,[data-testid="stLinkButton"] a{background:%RED%;color:#fff;border:0;border-radius:8px;padding:.45rem 1.1rem}
.stButton>button:hover,.stDownloadButton>button:hover,[data-testid="stLinkButton"] a:hover{background:%RED_D%;color:#fff}
[data-testid="stExpander"]{border:1px solid %LINE%;border-radius:10px;background:#fff}
[data-testid="stExpander"] summary{font-weight:600;color:%INK%}
[data-testid="stMetric"]{background:%BLUE%;border:1px solid %LINE%;border-radius:10px;padding:.7rem 1rem}
[data-testid="stMetricValue"]{color:%INK%}
[data-baseweb="tab-list"]{gap:.25rem}
[data-baseweb="tab"]{border-radius:8px 8px 0 0}
[data-testid="stDataFrame"],[data-testid="stTable"]{border:1px solid %LINE%;border-radius:8px}
code{background:#f1f5f9;color:%INK%;border-radius:5px}
table{border-collapse:collapse;width:100%;font-size:.93rem}
th{background:#eaf3fb;color:%INK%;text-align:left}
th,td{border:1px solid %LINE%;padding:.6rem .75rem;vertical-align:top}
.rm-card{background:#fff;border:1px solid %LINE%;border-left:5px solid %RED%;border-radius:10px;padding:1.1rem 1.4rem;margin:.6rem 0 1rem;box-shadow:0 2px 6px rgba(31,45,61,.04)}
.rm-card.soft{background:%BLUE%;border-left-color:#5b9bd5}
.rm-note{background:#fdf1f2;border-left:4px solid %RED%;border-radius:6px;padding:.7rem 1rem;color:#4a3338;font-size:.95rem}
.rm-gov{background:#fdf1f2;border:1px solid #f1ccd0;border-radius:8px;padding:.45rem .9rem;color:#5a3a40;font-size:.86rem;margin:0 0 1rem}
.rm-kicker{color:%RED%;font-weight:700;letter-spacing:.12em;font-size:.8rem;text-transform:uppercase}
.rm-sym{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;background:%BLUE%;border:1px solid %BLUE_M%;border-radius:6px;padding:.05rem .45rem;color:%INK%;font-weight:600}
.rm-tools{display:flex;flex-wrap:wrap;gap:.45rem;margin:.3rem 0 1rem}
.rm-tools a{padding:.3rem .85rem;border:1px solid #c5d6e6;border-radius:999px;text-decoration:none;color:%INK%;font-size:.92rem;background:#fff}
.rm-tools a:hover{background:%BLUE_M%;border-color:#9fbbd6}
[data-testid="stAlert"]:has([data-testid="stAlertContentSuccess"]),[data-testid="stAlertContainer"]:has([data-testid="stAlertContentSuccess"]){background:%BLUE% !important;border:1px solid %LINE%;color:%INK% !important}
[data-testid="stAlert"]:has([data-testid="stAlertContentSuccess"]) *{color:%INK% !important}
@media (max-width:768px){.block-container,[data-testid="stMainBlockContainer"]{padding-left:.9rem;padding-right:.9rem}}
[data-testid="stHeader"]{background:rgba(255,255,255,.92) !important;border-bottom:1px solid #e3ebf3 !important;box-shadow:none !important}
[data-testid="stSidebar"]{background:#f6f9fc !important;border-right:1px solid #e3ebf3 !important;box-shadow:none !important}
[data-testid="stSidebar"] *{color:#1f2d3d !important;text-shadow:none !important;letter-spacing:normal !important}
[data-testid="stSidebarNavLink"]{background:transparent !important;border:0 !important;box-shadow:none !important;border-radius:8px !important;padding:.35rem .7rem !important;margin:1px 0 !important;font-weight:500 !important}
[data-testid="stSidebarNavLink"]:hover{background:#eaf2fa !important}
[data-testid="stSidebarNavLink"][aria-current="page"]{background:#e3eefa !important;box-shadow:inset 3px 0 0 #c9505a !important;font-weight:600 !important}
[data-testid="stNavSectionHeader"],[data-testid="stSidebarNavSeparator"]{font-size:.72rem !important;letter-spacing:.08em !important;font-weight:600 !important;text-transform:uppercase !important;opacity:.75}
.stApp h1,.stApp h2,.stApp h3,.stApp h4{font-weight:600 !important;letter-spacing:-.01em !important;text-transform:none !important;text-shadow:none !important}
.stButton>button,.stDownloadButton>button,[data-testid^="stBaseButton"]{border-radius:8px !important;box-shadow:none !important;border-width:1px !important}
footer{visibility:hidden}
"""


def logo_svg() -> str:
    custom = _ROOT / "assets" / "rmti_logo.svg"
    return custom.read_text(encoding="utf-8") if custom.exists() else _DEFAULT_LOGO


LINE1 = f"Oncoclastics Platform \u00b7 Risk Mechanism Theory Index (RMTI) engine {ENGINE_VERSION} \u00b7 Apache-2.0"
LINE2 = f"For research use only. Not for clinical or diagnostic use. \u00a9 {YEAR} {OWNER} \u00b7 ORCID {ORCID}"


def _footer_svg(with_logo: bool) -> str:
    top, logo = 0, ""
    if with_logo:
        b64 = base64.b64encode(logo_svg().encode("utf-8")).decode("ascii")
        logo = (f'<image x="250" y="8" width="200" height="52" preserveAspectRatio="xMidYMid meet" '
                f'href="data:image/svg+xml;base64,{b64}"/>')
        top = 64
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 {top + 46}">{logo}'
            f'<line x1="0" x2="700" y1="1" y2="1" stroke="{LINE}"/>'
            f'<text x="350" y="{top + 20}" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" font-size="12" fill="{INK}">{LINE1}</text>'
            f'<text x="350" y="{top + 38}" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" font-size="11" fill="{MUTED}">{LINE2}</text>'
            f'</svg>')


def apply(first_page: bool = False) -> None:
    """Inject the shared look and the bottom signature (every page after the first also gets the RMTI logo)."""
    with_logo = not first_page
    b64 = base64.b64encode(_footer_svg(with_logo).encode("utf-8")).decode("ascii")
    css = _CSS
    for k, v in (("%RED_D%", RED_D), ("%RED%", RED), ("%BLUE_M%", BLUE_M), ("%BLUE%", BLUE), ("%LINE%", LINE),
                 ("%INK%", INK), ("%BODY%", BODY), ("%MUTED%", MUTED)):
        css = css.replace(k, v)
    css += ('.block-container::after,[data-testid="stMainBlockContainer"]::after{content:"";display:block;'
            f'height:{110 if with_logo else 46}px;margin:3rem auto 0;'
            f'background:url(data:image/svg+xml;base64,{b64}) center/contain no-repeat}}')
    _RAW_MD("<style>" + css + "</style>", unsafe_allow_html=True)


def governance_bar() -> None:
    st.markdown('<div class="rm-gov"><b>Research prototype.</b> Synthetic or published aggregate values only. '
                'Do not enter patient data. Not a medical device; not for clinical decisions.</div>', unsafe_allow_html=True)


HOME_HTML = r'''<!DOCTYPE html>
<html lang="en" data-theme="light"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Oncoclastics · RMTI</title>
<style>
:root{--bg:#ffffff;--ink:#1f2d3d;--body:#334155;--muted:#5d6d80;--red:#c9505a;--red2:#a93f48;--blue:#eef5fb;--blue2:#d6e6f4;--line:#d9e4ef;--code:#f1f5f9;color-scheme:light dark;box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0f1722;--ink:#e8edf2;--body:#c3cedb;--muted:#93a1b3;--blue:#16212f;--blue2:#22344a;--line:#2a3a50;--code:#16212f}}
:root[data-theme="dark"]{--bg:#0f1722;--ink:#e8edf2;--body:#c3cedb;--muted:#93a1b3;--blue:#16212f;--blue2:#22344a;--line:#2a3a50;--code:#16212f}
html{scroll-padding-top:env(safe-area-inset-top,0px);scroll-behavior:smooth}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--body);font:17px/1.65 system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif}
.wrap{max-width:1040px;margin:0 auto;padding:0 20px 28px}
.top{display:flex;flex-wrap:wrap;align-items:center;gap:.4rem 1.4rem;padding:16px 0;border-bottom:1px solid var(--line)}
.brand{font-weight:800;letter-spacing:.14em;color:var(--ink);font-size:.95rem}.brand span{color:var(--red)}
.top nav{display:flex;flex-wrap:wrap;gap:.2rem 1.2rem;margin-left:auto;font-size:.95rem}
.top a{color:var(--body);text-decoration:none}.top a:hover{color:var(--red)}
.hero{padding:44px 28px 26px;margin-top:18px;border:1px solid var(--line);border-radius:16px;background:linear-gradient(180deg,var(--blue) 0%,var(--bg) 100%)}
.kick{color:var(--red);font-weight:700;letter-spacing:.12em;font-size:.8rem;text-transform:uppercase}
h1{font-size:clamp(32px,6.2vw,48px);line-height:1.12;font-weight:650;color:var(--ink);margin:.15em 0 .35em;letter-spacing:-.02em}
h2{font-size:1.55rem;color:var(--ink);margin:2.6rem 0 .5rem;letter-spacing:-.01em}
h3{font-size:1.05rem;color:var(--ink);margin:.2rem 0 .3rem}
.lead{font-size:1.15rem;max-width:46em}
.cta{display:flex;flex-wrap:wrap;gap:.7rem;margin:1.2rem 0 0}
.btn{display:inline-block;padding:.6rem 1.2rem;border-radius:8px;text-decoration:none;font-weight:600;border:1px solid var(--red);background:var(--red);color:#fff}
.btn:hover{background:var(--red2)}.btn.ghost{background:transparent;color:var(--red)}.btn.ghost:hover{background:var(--blue)}
.trust{display:flex;flex-wrap:wrap;gap:.45rem;margin:1.4rem 0 0}
.chip{border:1px solid var(--line);background:var(--blue);color:var(--ink);border-radius:999px;padding:.2rem .8rem;font-size:.85rem}
.card{background:var(--bg);border:1px solid var(--line);border-left:5px solid var(--red);border-radius:10px;padding:1.1rem 1.4rem;margin:.7rem 0 1rem}
.card.soft{background:var(--blue);border-left-color:#5b9bd5}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px}
.panel{border:1px solid var(--line);border-radius:10px;padding:1rem 1.1rem;background:var(--bg)}
.panel small{color:var(--muted)}
.sym{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;background:var(--blue);border:1px solid var(--blue2);border-radius:6px;padding:.05rem .45rem;color:var(--ink);font-weight:600}
.tw{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:.93rem;min-width:600px}
th{background:var(--blue);color:var(--ink);text-align:left}
th,td{border:1px solid var(--line);padding:.55rem .75rem;vertical-align:top}
a{color:#3b78b4}
.small{color:var(--muted);font-size:.9rem}
svg.diag{width:100%;height:auto;display:block}
svg.diag text{font-family:system-ui,-apple-system,"Segoe UI",Arial,sans-serif}
iframe{width:100%;height:860px;border:1px solid var(--line);border-radius:8px;background:#05080e}
audio{width:100%;margin:.4rem 0}
.try{display:grid;grid-template-columns:minmax(240px,1fr) minmax(280px,1.4fr);gap:18px;align-items:start}
@media (max-width:760px){.try{grid-template-columns:1fr}}
.sl{display:grid;grid-template-columns:7.5em 1fr 3em;align-items:center;gap:.5rem;margin:.35rem 0;font-size:.95rem}
input[type=range]{width:100%;accent-color:var(--red)}
pre{background:var(--code);border:1px solid var(--line);border-radius:8px;padding:.8rem 1rem;overflow-x:auto;font:13px/1.55 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;color:var(--ink);margin:.3rem 0 .6rem;white-space:pre}
.out{display:flex;gap:.8rem;flex-wrap:wrap;margin:.6rem 0}
.out div{background:var(--blue);border:1px solid var(--line);border-radius:10px;padding:.5rem .9rem}
.out b{display:block;font-size:1.35rem;color:var(--ink)}
button.cp{background:transparent;border:1px solid var(--line);color:var(--body);border-radius:6px;padding:.15rem .6rem;font-size:.8rem;cursor:pointer;float:right}
.m{display:inline-block;min-width:3.4em;text-align:center;border-radius:5px;padding:0 .35em;font:600 .78rem ui-monospace,Menlo,monospace;background:var(--blue);color:var(--ink);border:1px solid var(--blue2)}
footer{margin-top:2.8rem;padding-top:1rem;border-top:1px solid var(--line);text-align:center;color:var(--muted);font-size:.82rem;line-height:1.7}
</style></head><body><div class="wrap">

<header class="top"><div class="brand">RMTI <span>·</span> ONCOCLASTICS</div>
<nav><a href="#researchers">For researchers and clinicians</a><a href="#developers">For developers</a><a href="#evidence">Evidence</a><a href="#cite">Cite</a></nav></header>

<section class="hero">
<div class="kick">Oncology and disaster science</div>
<h1>Oncoclastics: quantify how cancer trajectories fragment</h1>
<p class="lead">The Risk Mechanism Theory Index (RMTI) scores hazard, exposure, vulnerability and resilience over time, for liver, lung and breast cancer and for disaster science. One transparent equation, JSON in, JSON out.</p>
<div class="cta"><a class="btn" href="#try">Try the formula</a><a class="btn ghost" href="#developers">API quickstart</a><a class="btn ghost" href="#researchers">Read the definition</a></div>
<div class="trust"><span class="chip">Research prototype</span><span class="chip">Not a medical device</span><span class="chip">Synthetic or published aggregate values only</span><span class="chip">Apache-2.0</span><span class="chip">Zenodo DOI 10.5281/zenodo.24254220</span><span class="chip">No HIPAA, SOC 2 or clinical-validation claims</span></div>
</section>

<h2 id="engine">How the engine works</h2>
<svg class="diag" viewBox="0 0 900 250" role="img" aria-label="Inputs L, E, V, rho bio and rho care feed the RMTI equation, which returns a score, a trajectory, a two-sense reading and a FHIR RiskAssessment">
<defs><marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="var(--muted)"/></marker></defs>
<g stroke="var(--muted)" stroke-width="1.4" fill="none" marker-end="url(#ar)">
<path d="M170 37L300 120"/><path d="M170 81L300 124"/><path d="M170 125L300 128"/><path d="M170 169L300 132"/><path d="M170 213L300 136"/>
<path d="M540 128L680 42"/><path d="M540 128L680 100"/><path d="M540 128L680 158"/><path d="M540 128L680 216"/></g>
<g font-size="14" fill="var(--ink)">
<rect x="20" y="20" width="150" height="34" rx="8" fill="var(--blue)" stroke="var(--line)"/><text x="95" y="42" text-anchor="middle">L  likelihood</text>
<rect x="20" y="64" width="150" height="34" rx="8" fill="var(--blue)" stroke="var(--line)"/><text x="95" y="86" text-anchor="middle">E  exposure</text>
<rect x="20" y="108" width="150" height="34" rx="8" fill="var(--blue)" stroke="var(--line)"/><text x="95" y="130" text-anchor="middle">V  vulnerability</text>
<rect x="20" y="152" width="150" height="34" rx="8" fill="var(--blue)" stroke="var(--line)"/><text x="95" y="174" text-anchor="middle">ρ bio  biological reserve</text>
<rect x="20" y="196" width="150" height="34" rx="8" fill="var(--blue)" stroke="var(--line)"/><text x="95" y="218" text-anchor="middle">ρ care  care delivery</text>
<rect x="300" y="66" width="240" height="124" rx="12" fill="var(--bg)" stroke="var(--red)" stroke-width="2.4"/>
<text x="420" y="104" text-anchor="middle" font-weight="700">RMTI engine</text>
<text x="420" y="130" text-anchor="middle" font-family="ui-monospace,Menlo,monospace">R = L · E · V · (1 − ρ)</text>
<text x="420" y="154" text-anchor="middle" font-family="ui-monospace,Menlo,monospace" font-size="12.5" fill="var(--muted)">ρ = 1 − (1 − ρ bio)(1 − ρ care)</text>
<text x="420" y="176" text-anchor="middle" font-size="12" fill="var(--muted)">fixed five-band scale</text>
<g font-size="13.5">
<rect x="680" y="20" width="200" height="44" rx="8" fill="var(--blue)" stroke="var(--line)"/><text x="690" y="39">Snapshot score and band</text><text x="690" y="56" font-size="11.5" fill="var(--muted)" font-family="ui-monospace,Menlo,monospace">POST /v1/snapshot</text>
<rect x="680" y="78" width="200" height="44" rx="8" fill="var(--blue)" stroke="var(--line)"/><text x="690" y="97">Trajectory V(t), ρ(t)</text><text x="690" y="114" font-size="11.5" fill="var(--muted)" font-family="ui-monospace,Menlo,monospace">POST /v1/trajectory</text>
<rect x="680" y="136" width="200" height="44" rx="8" fill="var(--blue)" stroke="var(--line)"/><text x="690" y="155">Two senses of oncoclastics</text><text x="690" y="172" font-size="11.5" fill="var(--muted)" font-family="ui-monospace,Menlo,monospace">POST /v1/oncoclastics/two-sense</text>
<rect x="680" y="194" width="200" height="44" rx="8" fill="var(--blue)" stroke="var(--line)"/><text x="690" y="213">FHIR RiskAssessment</text><text x="690" y="230" font-size="11.5" fill="var(--muted)" font-family="ui-monospace,Menlo,monospace">POST /v1/fhir/risk-assessment</text>
</g></g></svg>

<h2 id="researchers">For researchers and clinicians: what oncoclastics means</h2>
<div class="card">
We use the term <b>oncoclastics</b> (adjective: <i>oncoclastic</i>; from <i>onco-</i>, tumor, and <i>-clastic</i>, broken or fragmented, from the Greek <i>klastos</i>) for the application of hazard–exposure–vulnerability–resilience assessment, as developed in disaster-risk reduction, to the fragmentation of cancer-related trajectories, whether biological (the progression from chronic injury to cancer; <i>biological oncoclastics</i>) or systemic (the disruption of surveillance and care; <i>care-system oncoclastics</i>). To our knowledge the term is new. Its closest relatives point elsewhere: an oncolytic agent destroys tumor cells (Russell et al., 2012) and an osteoclast resorbs bone (Teitelbaum, 2000), whereas what is broken here is the continuity of a trajectory or care pathway, not the tumor.<br><br>
We use the biological sense, with the path from chronic liver injury toward HCC, including noncirrhotic HCC, as the trajectory of interest; the care-system sense enters only through the care-system component of <span class="sym">ρ</span>. The same framing applies to oncology in general, including lung and breast cancer.</div>
<div class="tw"><table>
<tr><th>RMTI term</th><th>Biological oncoclastics</th><th>Care-system oncoclastics (through <span class="sym">ρ</span>)</th></tr>
<tr><td><b>Unit</b></td><td>Individual patient; progression from chronic injury toward cancer</td><td>Care pathway of the same patient (surveillance and follow-up)</td></tr>
<tr><td><span class="sym">L</span> likelihood</td><td>Probability of progression to cancer over the horizon</td><td>Not changed by disruption of care</td></tr>
<tr><td><span class="sym">E</span> exposure</td><td>Burden of metabolic, inflammatory, toxic or hemodynamic insults</td><td>Not changed by disruption of care</td></tr>
<tr><td><span class="sym">V</span> vulnerability</td><td>Allostatic load carried forward across cycles</td><td>Not scored separately</td></tr>
<tr><td><span class="sym">ρ</span> resilience</td><td>Biological adaptive reserve, <span class="sym">ρ<sub>bio</sub></span></td><td>Care-system capacity, <span class="sym">ρ<sub>care</sub></span></td></tr>
</table></div>
<div class="card soft" id="cite"><b>Cite:</b> Marolla C. <i>Oncoclastics: definition note, version 1.0.0.</i> Zenodo; 2026. <a href="https://doi.org/10.5281/zenodo.24254220">doi:10.5281/zenodo.24254220</a></div>

<h2>From tumor events to trajectory</h2>
<p class="small">Liver (Lau-Min 2025), lung (Sabakhtarishvili 2025) and breast (O’Shaughnessy 2026) cohorts, followed from Stage 1 to Stage 4 and scored with RMTI. Choose the organ and pace under the player. Research prototype; the mappings are illustrative.</p>
<iframe title="From tumor events to trajectory" allow="autoplay" srcdoc="__ANIM__"></iframe>

<h2 id="developers">For developers</h2>
<p>The API is JSON in, JSON out. Start it locally, check health, then send a case. Pass the <code>X-API-Key</code> header on every <code>/v1</code> call when keys are configured (<code>RMTI_API_KEYS</code>).</p>
<div class="grid">
<div class="panel"><h3>1 · Start</h3><pre>pip install -r requirements.txt
uvicorn api:app --port 8000
curl localhost:8000/health</pre><small>Open routes: <code>/docs</code>, <code>/redoc</code>, <code>/openapi.json</code>, <code>/widget</code></small></div>
<div class="panel"><h3>2 · Send a case</h3><p class="small" style="margin:.1rem 0">Two-sense snapshot: biological sense (L, E, V, ρ bio) and care-system sense (ρ care).</p><pre>POST /v1/oncoclastics/two-sense</pre><small>Fields: L, E, V, rho_bio, rho_care, rho_care_after, C</small></div>
<div class="panel"><h3>3 · Follow it over time</h3><p class="small" style="margin:.1rem 0">Trajectory from observations and care delivery at each visit.</p><pre>POST /v1/trajectory</pre><small>Also: <code>/v1/cohort/rank</code>, <code>/v1/validate</code>, <code>/v1/registry</code></small></div>
</div>

<h2 id="try">Try the formula</h2>
<p class="small">Computed in your browser with the published equation. No API call is made, and the numbers are illustrative.</p>
<div class="try">
<div>
<div class="sl"><label for="sL">L likelihood</label><input id="sL" type="range" min="0" max="1" step="0.05" value="0.30"><b id="vL"></b></div>
<div class="sl"><label for="sE">E exposure</label><input id="sE" type="range" min="0" max="1" step="0.05" value="0.65"><b id="vE"></b></div>
<div class="sl"><label for="sV">V vulnerability</label><input id="sV" type="range" min="0" max="1" step="0.05" value="0.40"><b id="vV"></b></div>
<div class="sl"><label for="sRb">ρ bio</label><input id="sRb" type="range" min="0" max="0.9" step="0.05" value="0.30"><b id="vRb"></b></div>
<div class="sl"><label for="sRc">ρ care</label><input id="sRc" type="range" min="0" max="0.95" step="0.05" value="0.20"><b id="vRc"></b></div>
<div class="out"><div>R<b id="oR"></b></div><div>ρ combined<b id="oRho"></b></div><div>Band<b id="oBand"></b></div></div>
<p class="small" id="oNote"></p>
</div>
<div>
<button class="cp" data-t="cc">Copy</button><h3>cURL</h3><pre id="cc"></pre>
<button class="cp" data-t="cpy">Copy</button><h3>Python</h3><pre id="cpy"></pre>
</div></div>

<h3 style="margin-top:1.6rem">Endpoints</h3>
<div class="tw"><table>
<tr><th>Method</th><th>Path</th><th>Purpose</th></tr>
<tr><td><span class="m">POST</span></td><td><code>/v1/snapshot</code></td><td>Scores one case at one point in time</td></tr>
<tr><td><span class="m">POST</span></td><td><code>/v1/trajectory</code></td><td>Scores a case across visits from observations and care delivery</td></tr>
<tr><td><span class="m">POST</span></td><td><code>/v1/cohort/rank</code></td><td>Ranks patients in a cohort (pseudonymous names only)</td></tr>
<tr><td><span class="m">POST</span></td><td><code>/v1/oncoclastics/two-sense</code></td><td>Biological sense and care-system sense</td></tr>
<tr><td><span class="m">POST</span></td><td><code>/v1/oncoclastics/trajectory</code></td><td>Time-indexed two-sense run with descriptive events (flags are not alerts)</td></tr>
<tr><td><span class="m">POST</span></td><td><code>/v1/fhir/risk-assessment</code></td><td>FHIR RiskAssessment output</td></tr>
<tr><td><span class="m">POST</span></td><td><code>/v1/validate</code></td><td>Retrospective validation</td></tr>
<tr><td><span class="m">GET</span></td><td><code>/v1/registry</code></td><td>Registry status, parameters, evidence and cohorts</td></tr>
<tr><td><span class="m">GET</span></td><td><code>/health</code></td><td>Health</td></tr>
</table></div>
<p class="small">API keys are issued by the maintainer. To ask for access, write through the ORCID profile <a href="https://orcid.org/0000-0001-8498-7380">0000-0001-8498-7380</a>.</p>

<h2 id="evidence">Evidence behind the case studies</h2>
<div class="grid">
<div class="panel"><h3>Liver</h3><p>Lau-Min et al., <i>JAMA Netw Open</i> 2025. 4,198 patients on systemic therapy; median survival 8.1 months; 20.7% received second-line therapy.</p></div>
<div class="panel"><h3>Lung</h3><p>Sabakhtarishvili et al., <i>JTO Clin Res Rep</i> 2025. 3,647 screened people; stage 4 at diagnosis 13% with screening versus 35–44% under usual care.</p></div>
<div class="panel"><h3>Breast</h3><p>O’Shaughnessy et al., <i>Breast Cancer Res Treat</i> 2026. 5,041 women with metastatic HR+/HER2− disease; 13.5 months; 30% died before a second-line regimen.</p></div>
<div class="panel"><h3>Chronic liver disease to HCC</h3><p>Johnson et al., <i>BJC Reports</i> 2024: 28% of HCC arose without passing through cirrhosis. Cucchetti et al., <i>Br J Cancer</i> 2023: 18.3% cure fraction after ablation. Independent RMTI case study; the authors did not review it.</p></div>
</div>
<p class="small">Published figures are quoted as reported. The mapping onto L, E, V and ρ and every trajectory value are illustrative and uncalibrated.</p>

<footer>Oncoclastics Platform · Risk Mechanism Theory Index (RMTI) engine v2.4.0 · Apache-2.0<br>
For research use only. Not for clinical or diagnostic use. © 2026 Dr. Cesar Marolla · ORCID 0000-0001-8498-7380</footer>
</div>
<script>
(function(){
function $(i){return document.getElementById(i)}
function upd(){
var L=+$('sL').value,E=+$('sE').value,V=+$('sV').value,rb=+$('sRb').value,rc=+$('sRc').value;
var rho=1-(1-rb)*(1-rc),R=L*E*V*(1-rho),b=[0.05,0.15,0.35,0.60],band=1;
for(var i=0;i<b.length;i++){if(R>=b[i])band=i+2}
$('vL').textContent=L.toFixed(2);$('vE').textContent=E.toFixed(2);$('vV').textContent=V.toFixed(2);$('vRb').textContent=rb.toFixed(2);$('vRc').textContent=rc.toFixed(2);
$('oR').textContent=R.toFixed(4);$('oRho').textContent=rho.toFixed(3);$('oBand').textContent=band+' of 5';
$('oNote').textContent='Raising ρ care alone scales R by (1 − ρ care): at '+rc.toFixed(2)+' the care term leaves '+(100*(1-rc)).toFixed(0)+'% of the risk unabsorbed.';
var j='{"L": '+L+', "E": '+E+', "V": '+V+', "rho_bio": '+rb+', "rho_care": '+rc+', "C": 3}';
$('cc').textContent='curl -X POST localhost:8000/v1/oncoclastics/two-sense \\\n  -H "Content-Type: application/json" \\\n  -H "X-API-Key: YOUR_KEY" \\\n  -d \''+j+'\'';
$('cpy').textContent='import requests\n\nr = requests.post(\n    "http://localhost:8000/v1/oncoclastics/two-sense",\n    headers={"X-API-Key": "YOUR_KEY"},\n    json='+j+',\n)\nprint(r.json())';
}
['sL','sE','sV','sRb','sRc'].forEach(function(i){$(i).addEventListener('input',upd)});
document.querySelectorAll('button.cp').forEach(function(b){b.addEventListener('click',function(){
var t=$(b.getAttribute('data-t')).textContent;
try{navigator.clipboard.writeText(t).then(function(){b.textContent='Copied'},function(){b.textContent='Select and copy'})}catch(e){b.textContent='Select and copy'}
setTimeout(function(){b.textContent='Copy'},1800)})});
upd();
})();
</script></body></html>
'''

_FIT = r'''<script>(function(){var fe=window.frameElement;
function fit(){try{var h=document.documentElement.scrollHeight;if(fe&&h>0){fe.style.height=(h+10)+'px';}}catch(x){}}
window.addEventListener('load',function(){fit();setTimeout(fit,500);setTimeout(fit,1800);});window.addEventListener('resize',fit);
document.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('a[href^="#"]');if(!a)return;
var el=document.getElementById(a.getAttribute('href').slice(1));if(!el)return;e.preventDefault();
try{var y=el.getBoundingClientRect().top+(fe?fe.getBoundingClientRect().top:0)-70;
var sc=parent.document.querySelector('[data-testid="stMain"], section.main')||parent.document.scrollingElement;sc.scrollBy({top:y,behavior:'smooth'});}
catch(x){el.scrollIntoView({behavior:'smooth'});}});})();</script></body>'''


ANIM_HTML = r'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RMTI – tumor events to trajectory: liver, lung, breast</title>
<style>
:root{color-scheme:dark;--bg:#0a0f18;--ink:#e8edf2;--mut:#98a4b3;--amb:#f0b45a;--red:#e0583f;--blu:#5aa9e6;--line:#26334a}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:system-ui,-apple-system,'Segoe UI',Roboto,Arial,sans-serif;padding:env(safe-area-inset-top,0) 0 env(safe-area-inset-bottom,0)}
.w{max-width:980px;margin:0 auto;padding:14px}
h1{font:300 clamp(18px,3.6vw,26px) system-ui;margin:0 0 8px}
#st{position:relative;aspect-ratio:16/9;min-height:300px;background:#05080e;border-radius:6px;overflow:hidden;border:1px solid var(--line)}
canvas{position:absolute;inset:0;width:100%;height:100%}
#ov{position:absolute;inset:0;padding:3.5% 5% 17%;display:flex;flex-direction:column;justify-content:center}
#cap{position:absolute;left:50%;bottom:8%;transform:translateX(-50%);background:rgba(10,10,10,.85);padding:3px 10px;font-size:clamp(12px,2.2vw,21px);text-align:center;width:max-content;max-width:92%}
#bar{position:absolute;left:0;bottom:0;height:4px;background:var(--amb);width:0}
.ctl{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:10px 0}
button,select{background:#141c2b;color:var(--ink);border:1px solid var(--line);border-radius:6px;padding:7px 12px;font-size:14px;cursor:pointer}
button.on{border-color:var(--amb);color:var(--amb)}
.big{font-size:clamp(24px,5.5vw,52px);font-weight:300}
.row{display:flex;align-items:center;gap:10px;margin:5px 0;font-size:clamp(11px,1.9vw,16px)}
.row b{width:34%;flex:none;font-weight:500}.row .tr{width:26%;flex:none}
.tr{height:12px;background:#141c2b;border-radius:6px;overflow:hidden}.tr i{display:block;height:100%;width:0}
.ev{display:flex;gap:6px;flex-wrap:wrap}.ev span{padding:5px 10px;border:1px solid var(--line);border-radius:14px;font-size:clamp(11px,1.8vw,15px);color:var(--mut);transition:.4s}
.ev span.on{color:#fff;border-color:var(--red);background:rgba(224,88,63,.22)}
.card{background:rgba(20,28,43,.92);border:1px solid var(--line);border-radius:10px;padding:14px 16px;font-size:clamp(12px,2vw,17px);line-height:1.5}
.card h3{margin:0 0 4px;color:var(--amb);font-size:clamp(14px,2.3vw,20px);font-weight:500}.card li{margin:4px 0;opacity:0;transition:.6s}.card li.on{opacity:1}.card ul{margin:8px 0 0;padding-left:18px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px}.cards div{background:rgba(20,28,43,.92);border:1px solid var(--line);border-radius:8px;padding:10px;font-size:clamp(11px,1.7vw,14px);opacity:0;transition:.6s}
.cards div.on{opacity:1}.cards h3{margin:0 0 4px;color:var(--amb);font-size:clamp(13px,2vw,17px)}
.note{color:var(--mut);font-size:12px;margin-top:8px}svg text{fill:var(--mut);font-size:11px}
</style></head><body><div class="w">
<h1>RMTI – from tumor events to trajectory</h1>
<div id="st"><canvas id="cv"></canvas><div id="ov"></div><div id="cap"></div><div id="bar"></div></div>
<div class="ctl"><button data-o="liver" class="on">Liver (HCC)</button><button data-o="lung">Lung</button><button data-o="breast">Female breast</button>
<select id="sp" aria-label="Pace"><option value="1.4">Slow</option><option value="1" selected>Medium-slow</option><option value=".7">Medium</option></select><button id="snd" title="Narration in Dr. Marolla’s voice with Adagio over the Rainbow">🔊 Sound on</button>
<span style="flex:1"></span><button id="pv">◀</button><button id="pp">Pause</button><button id="nx">▶</button><span id="sc" class="note"></span></div>
<p class="note">Research prototype. Published figures are quoted as reported by the cited studies; the mapping of those figures onto L, E, V and ρ and every trajectory value are illustrative and uncalibrated, not validated, not a medical device, not for patient-care decisions. Stage descriptions are simplified. Independent academic work (Apache-2.0).</p>
</div>
<script>
const O={
liver:{n:'Liver (HCC)',met:['Lung','Bone'],L:.30,E:.65,V:[.52,.42,.36,.30],r:[.20,.35,.50,.58],
st:['Stage 1 – single small tumor, no vessel invasion or spread; surgery, ablation or transplant possible','Stage 2 – single tumor involving blood vessels, or several small tumors confined to the liver','Stage 3 – larger or multiple tumors, or major portal/hepatic vein invasion; regional lymph nodes may be involved','Stage 4 – distant spread (lungs, bones, distant nodes); systemic therapy, immunotherapy or palliative care'],
cs:{a:'Lau-Min KS et al. JAMA Netw Open 2025;8(12):e2551665',n:'4198 patients on systemic therapy for HCC (Flatiron database, 2011–2023)',f:['Median overall survival 8.1 months; median progression-free survival 3.9 months','Only 20.7% received second-line systemic therapy','Liver function matters: ALBI grade 3 vs 1, OS HR 2.65; atezolizumab-bevacizumab vs sorafenib, PFS HR 0.84']},
an:[['V','Liver function (ALBI grade 3 vs 1): OS HR 2.65'],['E','Concomitant liver disease documented in 75.6%'],['ρ','Second-line therapy delivered to 20.7%']]},
lung:{n:'Lung',met:['Brain','Bone'],L:.35,E:.70,V:[.50,.46,.40,.36],r:[.20,.30,.42,.50],
st:['Stage 1 – small tumor confined to the lung, no lymph-node spread','Stage 2 – larger tumor and/or nearby lymph-node involvement','Stage 3 – spread to central chest lymph nodes or adjacent structures','Stage 4 – distant metastasis (for example brain, bone, liver, other lung)'],
cs:{a:'Sabakhtarishvili G et al. JTO Clin Res Rep 2025;6:100899',n:'3647 low-dose CT screening participants, 13% Black (one US center, 2021–2023)',f:['Lung cancer found in 3.4% of Black and 3.7% of White participants within 2 years','Stage 4 at diagnosis, screened vs usual care: 13% vs 44% (Black), 13% vs 35% (White)','Lung-RADS 4 results: 5.2% vs 4.1% (p = 0.32)']},
an:[['E','Smoking: mean 37.7 (Black) vs 41.8 (White) pack-years'],['L','Cancer found in 3.4–3.7% within 2 years of first scan'],['ρ','Screening delivered: stage 4 at diagnosis 13% vs 35–44% usual care']]},
breast:{n:'Female breast',met:['Bone','Liver'],L:.25,E:.60,V:[.48,.44,.38,.34],r:[.25,.35,.45,.55],
st:['Stage 1 – small invasive tumor, lymph nodes clear or minimally involved','Stage 2 – larger tumor and/or axillary lymph-node involvement','Stage 3 – extensive nodal disease or chest-wall/skin involvement','Stage 4 – distant metastasis (for example bone, liver, lung, brain)'],
cs:{a:'O’Shaughnessy J et al. Breast Cancer Res Treat 2026;219:19',n:'5041 women with HR+/HER2− metastatic breast cancer after endocrine therapy (Flatiron, 2015–2024)',f:['Median real-world OS 13.5 months from first post-endocrine chemotherapy; 10.7, 8.5, 7.5, 7.4 months at lines 2–5','30% died before receiving a second-line regimen','Died vs alive: ECOG 2+ 24% vs 12%; liver metastases 59% vs 50%']},
an:[['L','84% had prior CDK4/6 inhibitor; time to next treatment or death 5.1 → 3.3 months by line 5'],['V','ECOG 2+ 24% vs 12%; 3+ metastatic sites 45% vs 38% (died vs alive)'],['ρ','30% died before second line; rwOS 13.5 → 7.4 months by line 5']]}};
const B=[0,.05,.15,.35,.60,1],band=R=>B.findIndex((b,i)=>R<B[i+1])+1,Rt=(o,i)=>o.L*o.E*o.V[i]*(1-o.r[i]),f3=x=>x.toFixed(3);
let k='liver',o=O[k],s=0,t0=performance.now(),pause=false,P=0,spd=1;
const ov=document.getElementById('ov'),cap=document.getElementById('cap'),bar=document.getElementById('bar'),cv=document.getElementById('cv'),x=cv.getContext('2d');
const $=id=>document.getElementById(id);
const S=[
{d:16,c:()=>'Risk Mechanism Theory Index – '+o.n,h:()=>`<div class="big">R = L · E · V · (1 − ρ)</div><p style="color:var(--mut)">Likelihood · Exposure · Vulnerability · Resilience – followed across review cycles</p><p style="color:var(--amb)">Case studies: liver · lung · breast</p><p style="color:var(--mut);font-size:clamp(12px,1.9vw,16px)">Dr. Cesar Marolla, PhD., ALM · Instructor, Harvard University Division of Continuing Education</p>`},
{d:16,c:()=>'Published case study – '+o.cs.a,h:()=>`<div class="card"><h3>${o.cs.a}</h3>${o.cs.n}<ul>${o.cs.f.map((t,i)=>`<li id="f${i}">${t}</li>`).join('')}</ul></div>`,u:p=>o.cs.f.forEach((t,i)=>$('f'+i).classList.toggle('on',p>.12+i*.25))},
{d:28,tum:1,c:p=>o.st[Math.min(3,p*4|0)],h:()=>`<div class="ev" style="margin-bottom:auto">${[1,2,3,4].map((n,i)=>`<span id="e${i}">Stage ${n}</span>`).join('')}</div>`,u:p=>[0,1,2,3].forEach(i=>$('e'+i).classList.toggle('on',i===Math.min(3,p*4|0)))},
{d:14,c:()=>'Data assessing – published anchors feed L, E, V, ρ',h:()=>`<div style="color:var(--amb);font-size:12px;margin-bottom:6px">Illustrative mapping – not calibrated</div>`+[['L  likelihood',o.L,'--blu'],['E  exposure',o.E,'--blu'],['V  vulnerability',o.V[0],'--red'],['ρ  resilience',o.r[0],'--amb']].map((r,i)=>`<div class="row"><b>${r[0]}</b><div class="tr"><i id="g${i}" style="background:var(${r[2]})"></i></div><span>${r[1].toFixed(2)}</span></div>`).join('')+`<div class="card" style="margin-top:8px">${o.an.map(a=>`<div><b style="color:var(--amb)">${a[0]}</b> ← ${a[1]}</div>`).join('')}</div>`,u:p=>[o.L,o.E,o.V[0],o.r[0]].forEach((v,i)=>$('g'+i).style.width=Math.min(1,p*1.8)*v*100+'%')},
{d:14,c:()=>'RMTI formula analytics',h:()=>`<div class="big" style="font-size:clamp(18px,4vw,36px)">${o.L.toFixed(2)} × ${o.E.toFixed(2)} × ${o.V[0].toFixed(2)} × (1 − ${o.r[0].toFixed(2)})</div><div class="big" id="rv" style="color:var(--amb)"></div><svg viewBox="0 0 600 50" width="100%"><rect x="0" y="14" width="600" height="14" fill="#141c2b"/>${B.slice(1,-1).map(b=>`<line x1="${b*600}" x2="${b*600}" y1="8" y2="34" stroke="#98a4b3"/><text x="${b*600-10}" y="46">${b}</text>`).join('')}<circle id="mk" cx="0" cy="21" r="8" fill="#e0583f"/></svg><div class="note" id="bd"></div>`,u:p=>{const R=Rt(o,0)*Math.min(1,p*1.6);$('rv').textContent='R = '+f3(R);$('mk').setAttribute('cx',R*600);$('bd').textContent='Fixed five-band scale (0 · 0.05 · 0.15 · 0.35 · 0.60 · 1.0): band '+band(R)+'  ·  EAL = L · C · (1 − ρ) adds the loss layer'}},
{d:18,c:()=>'Trajectory – V(t) and ρ(t) across review cycles',h:()=>`<svg viewBox="0 0 600 230" width="100%"><line x1="40" y1="200" x2="580" y2="200" stroke="#26334a"/><polyline id="pl" fill="none" stroke="#f0b45a" stroke-width="3"/><g id="pt"></g>${[0,1,2,3].map(i=>`<text x="${68+i*150}" y="218">cycle ${i}</text>`).join('')}<text x="40" y="14">R(t)</text></svg><div class="note" id="tn"></div>`,u:p=>{const n=Math.min(4,Math.floor(p*5)+1),X=i=>90+i*150,Y=i=>200-Rt(o,i)/0.12*180;let a='',g='';for(let i=0;i<n;i++){a+=X(i)+','+Y(i)+' ';g+=`<circle cx="${X(i)}" cy="${Y(i)}" r="6" fill="#e0583f"/><text x="${X(i)-20}" y="${Y(i)-12}">${f3(Rt(o,i))}</text>`}$('pl').setAttribute('points',a);$('pt').innerHTML=g;$('tn').textContent='Synthetic example: V '+o.V[0]+' → '+o.V[3]+', ρ '+o.r[0]+' → '+o.r[3]+'; R moves from band '+band(Rt(o,0))+' to band '+band(Rt(o,3))+'.'}},
{d:16,c:()=>'What RMTI quantifies, assesses and helps manage',h:()=>`<div class="cards"><div><h3>Quantify</h3>One score R and an Expected Annual Loss index from L, E, V, ρ.</div><div><h3>Assess</h3>Fixed bands and a surveillance-posture reading for a clinical team to discuss.</div><div><h3>Track</h3>V(t) and ρ(t) each cycle: is risk drifting, or is delivery closing the gap?</div><div><h3>Manage</h3>Shows which driver (vulnerability or delivery) to work on; treatment decisions stay with clinicians.</div></div>`,u:p=>document.querySelectorAll('.cards div').forEach((d,i)=>d.classList.toggle('on',p>.08+i*.2))},
{d:12,c:()=>'Research prototype – not validated',h:()=>`<div style="font-size:clamp(13px,2.2vw,20px);line-height:1.6">Parameters (α, β, κ·H, λ, anchors) are uncalibrated placeholders.<br>Published figures belong to the cited studies; RMTI mappings are illustrative.<br>Open question: does trajectory add information beyond a well-measured current level?</div>`}];
const rn=i=>{const v=Math.sin(i*127.1)*43758.5;return v-Math.floor(v)};
function blob(cx,cy,n,R,sd,r){for(let i=0;i<n;i++){const a=rn(sd+i)*6.28,d=Math.sqrt(rn(sd+i+99))*R;x.fillStyle=`rgba(${205+rn(i)*40|0},${70+rn(i+5)*40|0},50,.85)`;x.beginPath();x.arc(cx+Math.cos(a)*d,cy+Math.sin(a)*d,r,0,7);x.fill()}}
function flow(ax,ay,bx,by,n,q,r){for(let i=0;i<n;i++){const t=(q*1.5+i/n)%1;x.fillStyle='rgba(240,120,90,.95)';x.beginPath();x.arc(ax+(bx-ax)*t,ay+(by-ay)*t+Math.sin(t*9+i)*6,r,0,7);x.fill()}}
function tumor(W,H,st,q){const u=H/100;x.fillStyle='rgba(150,70,60,.35)';x.strokeStyle='rgba(220,150,130,.6)';x.beginPath();x.ellipse(W*.28,H*.45,W*.2,H*.28,0,0,7);x.fill();x.stroke();
x.strokeStyle='rgba(120,160,230,.7)';x.lineWidth=5;x.beginPath();x.moveTo(W*.14,H*.64);x.lineTo(W*.4,H*.6);x.lineTo(W*.62,H*.45);x.stroke();x.lineWidth=1;
x.fillStyle=st>=3?'rgba(224,88,63,.8)':st===2?`rgba(224,88,63,${.25+q*.55})`:'rgba(90,120,170,.5)';x.beginPath();x.arc(W*.56,H*.28,u*5,0,7);x.fill();
const sites=[[W*.86,H*.24],[W*.86,H*.74]];x.fillStyle='rgba(90,120,170,.4)';sites.forEach((p,i)=>{x.beginPath();x.arc(p[0],p[1],u*9,0,7);x.fill();x.fillStyle='#98a4b3';x.font=u*3.2+'px system-ui';x.fillText(o.met[i],p[0]-u*5,p[1]+u*13);x.fillStyle='rgba(90,120,170,.4)'});
x.fillStyle='#98a4b3';x.font=u*3.2+'px system-ui';x.fillText('Primary organ',W*.2,H*.8);x.fillText('Vessel',W*.2,H*.7);x.fillText('Lymph node',W*.5,H*.2);
const tx=W*.25,ty=H*.42;
if(st===0)blob(tx,ty,3+q*10|0,u*(5+q*4),1,u*1.1);
else if(st===1){blob(tx,ty,18+q*22|0,u*(10+q*5),1,u*1.3);flow(tx,ty,W*.4,H*.6,8,q,u*.9)}
else{blob(tx,ty,42,u*15,1,u*1.4);blob(W*.17,H*.55,10+(st===2?q*10:20)|0,u*6,50,u*1.2);blob(W*.36,H*.33,10+(st===2?q*10:20)|0,u*6,80,u*1.2);flow(tx,ty,W*.56,H*.28,9,q,u*.9);
if(st===3){sites.forEach((p,i)=>{flow(W*.4,H*.6,p[0],p[1],9,q,u*.9);blob(p[0],p[1],q*16|0,u*7,200+i*40,u*1.2)})}}}
function draw(p){const W=cv.width=cv.clientWidth,H=cv.height=cv.clientHeight;x.fillStyle='#0b1b2b';x.fillRect(0,0,W,H);
cells.forEach(c=>{c.x=(c.x+c.vx+1)%1;c.y=(c.y+c.vy+1)%1;const g=x.createRadialGradient(c.x*W,c.y*H,1,c.x*W,c.y*H,c.r);g.addColorStop(0,'rgba(120,180,240,.4)');g.addColorStop(1,'rgba(40,90,170,.1)');x.fillStyle=g;x.beginPath();x.arc(c.x*W,c.y*H,c.r,0,7);x.fill()});
if(S[s].tum){const i=Math.min(3,p*4|0);tumor(W,H,i,p*4-i)}}
const cells=Array.from({length:40},()=>({x:Math.random(),y:Math.random(),r:6+Math.random()*14,vx:(Math.random()-.5)*.0003,vy:(Math.random()-.5)*.0003}));
const dur=()=>S[s].d*1000*spd;
function go(i){s=(i+S.length)%S.length;t0=performance.now();P=0;ov.innerHTML=S[s].h();$('sc').textContent=(s+1)+' / '+S.length}
function setScene(i){s=i;ov.innerHTML=S[s].h();$('sc').textContent=(s+1)+' / '+S.length}
document.querySelectorAll('[data-o]').forEach(b=>b.onclick=()=>{if(snd)sndOff();k=b.dataset.o;o=O[k];document.querySelectorAll('[data-o]').forEach(z=>z.classList.toggle('on',z===b));go(s)});
$('sp').onchange=e=>{spd=+e.target.value;t0=performance.now()-P*dur()};
$('pv').onclick=()=>{if(snd&&vOK)voice.currentTime=starts[(s+7)%8];else go(s-1)};$('nx').onclick=()=>{if(snd&&vOK)voice.currentTime=starts[(s+1)%8];else go(s+1)};
$('pp').onclick=()=>{pause=!pause;$('pp').textContent=pause?'Play':'Pause';if(!pause)t0=performance.now()-P*dur();if(snd){[voice,bed].forEach(a=>{if(a){pause?a.pause():a.play().catch(()=>{})}})}};
function loop(n){const vp=snd&&vOK&&starts&&!voice.paused&&!voice.ended;if(bed){const tg=vp?.14:(snd?.4:0);bed.volume=Math.max(0,Math.min(1,bed.volume+(tg-bed.volume)*.06))}if(vp){const t=voice.currentTime;let i=0;for(let j=0;j<8;j++)if(t>=starts[j])i=j;if(i!==s)setScene(i);const e=i<7?starts[i+1]:voice.duration;P=Math.max(0,Math.min(1,(t-starts[i])/Math.max(.5,e-starts[i])))}else if(!pause){P=Math.min(1,(n-t0)/dur());if(P>=1)go(s+1)}const c=S[s];cap.textContent=c.c(P);if(c.u)c.u(P);bar.style.width=P*100+'%';draw(P);requestAnimationFrame(loop)}

const WORDS={"liver": [35, 38, 61, 29, 31, 39, 29, 27], "lung": [35, 36, 47, 26, 31, 39, 29, 27], "breast": [35, 39, 47, 28, 31, 39, 29, 27]},SB='/app/static/';
let voice=null,bed=null,snd=false,vOK=false,starts=null,tj=null;
function est(dur){const w=WORDS[k],tot=w.reduce((a,b)=>a+b,0);let c=0;return w.map(x=>{const t=(dur-.3)*c/tot;c+=x;return t})}
function sndOff(){snd=false;vOK=false;starts=null;$('snd').textContent='\uD83D\uDD0A Sound on';$('snd').classList.remove('on');if(voice){voice.pause();voice=null}if(bed){bed.pause();bed=null}}
function sndOn(){
 snd=true;$('snd').textContent='\uD83D\uDD07 Sound off';$('snd').classList.add('on');
 bed=new Audio(SB+'adagio_bed_134s.mp3');bed.loop=true;bed.volume=.4;bed.play().catch(()=>{});
 voice=new Audio(SB+'narration_'+k+'.mp3');vOK=false;starts=null;tj=null;
 voice.onloadedmetadata=()=>{vOK=true;starts=(tj&&tj.length===8)?tj:est(voice.duration)};
 voice.onended=()=>{if(bed){setTimeout(()=>{if(bed&&(!voice||voice.ended))bed.pause()},4000)}};
 voice.onerror=()=>{vOK=false};
 fetch(SB+'timing_'+k+'.json').then(r=>r.ok?r.json():null).then(j=>{tj=j;if(vOK&&j&&j.length===8)starts=j}).catch(()=>{});
 pause=false;$('pp').textContent='Pause';go(0);voice.play().catch(()=>{});
}
$('snd').onclick=()=>{snd?sndOff():sndOn()};
go(0);requestAnimationFrame(loop);
</script></body></html>
'''

JOHNSON_SRC = r'''st.markdown('<div class="rm-kicker">Case study · biological and care-system oncoclastics</div>', unsafe_allow_html=True)
st.title("From chronic liver disease to HCC")
st.markdown("**Built on published work led by Dr. Philip J. Johnson, University of Liverpool.** "
            "Elasticity analysis of the Risk Mechanism Theory Index (RMTI) with the biological and care-system "
            "components of resilience, ρ<sub>bio</sub> and ρ<sub>care</sub>.", unsafe_allow_html=True)
st.markdown('<div class="rm-note">Independent RMTI case study. Dr. Johnson and his co-authors did not review it and are not '
            'responsible for the mapping or the calculations. Research prototype: not validated, not a medical device, '
            'not for patient-care decisions. Study figures are quoted as reported; everything derived is illustrative.</div>',
            unsafe_allow_html=True)

st.header("The two studies")
c1, c2 = st.columns(2)
for col, key in ((c1, "johnson2024"), (c2, "cucchetti2023")):
    s = jc.SOURCES[key]
    with col:
        st.markdown(f'<div class="rm-card"><b>{s["title"]}</b><br>{s["authors"]}<br><i>{s["journal"]}</i><br>'
                    f'<a href="https://doi.org/{s["doi"]}">doi:{s["doi"]}</a></div>', unsafe_allow_html=True)
        for k, v in jc.PUBLISHED[key]:
            st.markdown(f"- **{k}:** {v}")
st.caption(f"The authors' own cure calculator: {jc.LIVERPOOL_CALCULATOR}")

st.header("How RMTI reads them")
st.markdown("""
| RMTI term | Reading in this case study | Source |
|---|---|---|
| **L** | Cumulative HCC risk over the horizon, 1 − exp(−rate × years), from the incidence per 1000 patient-years | Johnson et al. 2024 (derived here) |
| **E**, **V** | Placeholders you can set below. V can be driven by Fib-4 or ALBI grade | Fib-4 and ALBI from both studies |
| **ρ<sub>bio</sub>** | Biological reserve, kept apart from care delivery (placeholder) | Not scored in the papers |
| **ρ<sub>care</sub>** | Delivery of surveillance and follow-up (placeholder; the studies describe programme-level detection) | Context in both studies |
| **C** | Not modified. Cure after ablation depends on tumour size and liver function at detection, which overlaps with ρ<sub>care</sub>: a stated limitation | Cucchetti et al. 2023 |
""", unsafe_allow_html=True)

st.header("Interactive elasticity analysis")
a, b, c, d = st.columns(4)
E = a.slider("E, exposure", 0.05, 1.0, 0.60, 0.05)
V = b.slider("V, vulnerability", 0.05, 1.0, 0.50, 0.05)
rb = c.slider("ρ_bio", 0.0, 0.9, 0.30, 0.05)
yrs = d.slider("Horizon (years)", 3, 20, 10)
e, f = st.columns(2)
low = e.slider("ρ_care, low delivery", 0.0, 0.9, 0.20, 0.05)
high = f.slider("ρ_care, high delivery", 0.0, 0.95, 0.70, 0.05)

rows = jc.case_table(E=E, V=V, rho_bio=rb, rho_care_low=low, rho_care_high=high, years=float(yrs))
st.table([{"Pathway": r["pathway"], "Care delivery": r["care"], "L": f"{r['L']:.3f}", "ρ_care": f"{r['rho_care']:.2f}",
           "ρ (combined)": f"{r['rho']:.3f}", "R": f"{r['R']:.4f}", "ε of R to ρ_care": f"{r['eps_rho_care']:+.2f}"} for r in rows])
st.markdown("ε<sub>L</sub> = ε<sub>E</sub> = ε<sub>V</sub> = 1, and ε<sub>ρcare</sub> = −ρ<sub>care</sub> / (1 − ρ<sub>care</sub>): "
            "the more delivery is already in place, the more a further point of ρ<sub>care</sub> is worth.", unsafe_allow_html=True)

dec = jc.pathway_comparison(rows)
be = jc.breakeven_rho_care(rows[0]["L"], rows[2]["L"], low)
g1, g2 = st.columns(2)
with g1:
    st.subheader("What moves R")
    st.caption("Change in ln R from (non-cirrhotic, low delivery) to (cirrhosis, high delivery)")
    import pandas as pd
    st.bar_chart(pd.DataFrame({"Change in ln R": [dec["dln_L"], dec["dln_E"], dec["dln_V"], dec["dln_1-rho"]]},
                              index=["L", "E", "V", "1 − ρ"]))
    st.write(f"R changes by {dec['pct_change_R']:+.0f}% in total.")
with g2:
    st.subheader("Break-even delivery")
    if be is None:
        st.write("No ρ_care in [0, 1) makes the cirrhosis pathway match the non-cirrhotic R at the low-delivery level.")
    else:
        st.write(f"For cirrhosis to match the non-cirrhotic R at ρ_care = {low:.2f}, ρ_care would have to reach **{be:.2f}** "
                 "(E, V and ρ_bio equal). Delivery alone has to offset the whole difference in L.")

st.subheader("V driven by Fib-4 (placeholder anchors)")
st.table([{"Fib-4": r["fib4"], "V*": f"{r['V_star']:.3f}", "ε of V* to Fib-4": f"{r['eps_d']:.2f}"} for r in jc.fib4_v_elasticity()])
st.caption("Fib-4 values are the published medians at baseline (1.52 without HCC, 2.4 with HCC) and the 3.25 cirrhosis threshold. "
           "The mapping (V* from 0.35 to 0.85 over Fib-4 0 to 6) is a placeholder, not calibrated.")

st.header("Limits")
st.markdown("""
- Elasticities are local and assume the other terms are fixed and independent; R is a relative index, not a probability.
- ρ_bio and ρ_care are assumed to act independently on the same inherent risk, and ρ_bio must not contain care delivery: propositions to be tested.
- Placeholders for E, V, ρ_bio and ρ_care are not taken from the papers. Whether trajectory adds information beyond a well-measured current level is an open question.
""")
st.caption("Code: rmti_johnson_case.py, rmti_elasticity.py, rmti_resilience_components.py (Apache-2.0).")
'''


def home():
    page = HOME_HTML.replace("__ANIM__", _html.escape(ANIM_HTML, quote=True))
    components.html(page.replace("</body>", _FIT, 1), height=3600, scrolling=True)


def johnson():
    import rmti_johnson_case as jc
    exec(compile(JOHNSON_SRC, "johnson_case_study", "exec"), {"st": st, "jc": jc, "__name__": "johnson_case_study"})


_GROUPS = [
    ("Foundation & evidence", ("step", "case", "evidence", "overview", "oncoclastics")),
    ("Calculators", ("calculator", "sandbox", "cohort")),
    ("4D simulations", ("4d", "matrix", "lab", "progression", "live")),
    ("Developers", ("developer", "portal", "api")),
]
_ICONS = {"calculator": "\U0001F9EE", "hcc": "\U0001FA7A", "cohort": "\U0001F465", "4d": "\U0001F9CA", "lab": "\U0001F52C", "live": "\U0001F4CA",
          "progression": "\U0001F4C8", "step": "\U0001F4D0", "case": "\U0001F3AC", "developer": "\U0001F50C"}


def _discover():
    """Every .py file in pages/ becomes a menu entry, so no existing page is lost whatever it is called."""
    found, seen = {}, set()
    for base in BASES:
        folder = base / "pages"
        if not folder.is_dir():
            continue
        for f in sorted(folder.glob("*.py")):
            clean = re.sub(r"^\d+[_\- ]*", "", f.stem)
            key = clean.lower()
            if f.stem.startswith("_") or key in seen or key in ("home", "init") or "johnson" in key:
                continue
            seen.add(key)
            group = next((g for g, words in _GROUPS if any(w in key for w in words)), "More")
            icon = next((i for w, i in _ICONS.items() if w in key), "\U0001F4C4")
            found.setdefault(group, []).append(st.Page(str(f), title=clean.replace("_", " "), icon=icon, url_path=re.sub(r"[^A-Za-z0-9_\-]", "_", clean)))
    return found


try:
    _debug = "debug" in st.query_params
except Exception:
    _debug = False

if not hasattr(st, "navigation"):
    st.warning("This Streamlit version has no grouped navigation (needs 1.36 or newer). Showing the home page only. Streamlit version: " + st.__version__)
    apply(first_page=True)
    home()
    st.stop()

_found = _discover()
nav = {"Overview": [st.Page(home, title=HOME_TITLE, icon="\U0001F9EC", default=True)]}
nav["Foundation & evidence"] = [st.Page(johnson, title="Johnson Case Study (HCC)", icon="\U0001F4DA", url_path="Johnson_Case_Study")] + _found.pop("Foundation & evidence", [])
for _g in ("Calculators", "4D simulations", "Developers", "More"):
    if _g in _found:
        nav[_g] = _found.pop(_g)
for _g, _v in _found.items():
    nav[_g] = _v

st.session_state["rmti_nav"] = True
pg = st.navigation(nav)
with st.sidebar:
    st.caption(f"RMTI engine {ENGINE_VERSION} \u00b7 research prototype \u00b7 build {BUILD}")
is_home = pg.title == HOME_TITLE
apply(first_page=is_home)
if not is_home:
    governance_bar()
if _debug:
    st.json({"build": BUILD, "streamlit": st.__version__, "entry_file": str(Path(__file__).resolve()), "bases": [str(b) for b in BASES],
             "pages": {g: [(p.title, getattr(p, "url_path", "")) for p in v] for g, v in nav.items()}})
pg.run()
apply(first_page=is_home)
