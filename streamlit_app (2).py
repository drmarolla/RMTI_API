"""Oncoclastics / RMTI: ONE-FILE site entry. Main file path in Streamlit Cloud: streamlit_app.py
Self-contained: look, new home page, grouped navigation. Uses your existing pages if they are in the repository
(root pages/ folder), and animation/index.html if present. Nothing else is required."""
import html as _html
import runpy
import sys
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

BUILD = "2026-11-21-c"
REPO = Path(__file__).resolve().parent
_ROOT = REPO
for _p in (REPO,):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

# page config once; pages call it again, so make later calls harmless
_orig = getattr(st, "_rmti_set_page_config", None) or st.set_page_config
st._rmti_set_page_config = _orig
_orig(page_title="Oncoclastics \u00b7 RMTI", page_icon="\U0001F9EC", layout="wide", initial_sidebar_state="expanded")
st.set_page_config = lambda *a, **k: None

import base64  # noqa: E402

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
    st.markdown("<style>" + css + "</style>", unsafe_allow_html=True)


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
.hero{padding:44px 0 18px}
.kick{color:var(--red);font-weight:700;letter-spacing:.12em;font-size:.8rem;text-transform:uppercase}
h1{font-size:clamp(32px,6.4vw,50px);line-height:1.12;color:var(--ink);margin:.15em 0 .35em;letter-spacing:-.015em}
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


def home():
    anim_file = next((p for p in (REPO / "animation" / "index.html", REPO / "index.html")
                      if p.exists() and "tumor events to trajectory" in p.read_text(encoding="utf-8", errors="ignore")), None)
    page = HOME_HTML
    if anim_file:
        frame = _html.escape(anim_file.read_text(encoding="utf-8"), quote=True)
        page = page.replace("__ANIM__", frame)
    else:
        page = page.replace('<iframe title="From tumor events to trajectory" allow="autoplay" srcdoc="__ANIM__"></iframe>',
                            '<p class="small">The animation file animation/index.html was not found in the repository.</p>')
    components.html(page.replace("</body>", _FIT, 1), height=3600, scrolling=True)


def _find(rel):
    bases = [REPO] + sorted(d for d in REPO.iterdir() if d.is_dir() and d.name.startswith(("oncoclastics", "root_files")))
    bases += [c for d in list(bases[1:]) for c in sorted(d.iterdir()) if c.is_dir()]
    for b in bases:
        if (b / rel).exists():
            return str(b / rel)
    return None


GROUPS = {
    "Foundation & evidence": [
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

try:
    _debug = "debug" in st.query_params
except Exception:
    _debug = False

if not hasattr(st, "navigation"):
    st.warning("This Streamlit version has no grouped navigation (needs 1.36 or newer). Showing the home page only. Streamlit version: " + st.__version__)
    apply(first_page=True)
    home()
    st.stop()

nav = {"Overview": [st.Page(home, title=HOME_TITLE, icon="\U0001F9EC", default=True)]}
for group, items in GROUPS.items():
    pages = []
    for rel, title, icon, url in items:
        path = _find(rel)
        if path:
            pages.append(st.Page(path, title=title, icon=icon, url_path=url))
    if pages:
        nav[group] = pages

st.session_state["rmti_nav"] = True
pg = st.navigation(nav)
with st.sidebar:
    st.caption(f"RMTI engine {ENGINE_VERSION} \u00b7 research prototype \u00b7 build {BUILD}")
is_home = pg.title == HOME_TITLE
apply(first_page=is_home)
if not is_home:
    governance_bar()
if _debug:
    st.json({"build": BUILD, "streamlit": st.__version__, "entry_file": str(Path(__file__).resolve()), "repo_root": str(REPO),
             "pages": {g: [(p.title, getattr(p, "url_path", "")) for p in v] for g, v in nav.items()},
             "animation_found": (REPO / "animation" / "index.html").exists()})
pg.run()
apply(first_page=is_home)
