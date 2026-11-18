"""RMTI home page: website-style landing (nav, hero, tool cards, 3D models, API docs). Saved under the name app.py.py so it is the start page without changing Streamlit settings."""
import sys
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="RMTI Oncoclastics", page_icon="🧬", layout="wide", initial_sidebar_state="collapsed")
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import oncoclastic_style as ui
SRC = ROOT / "developer_portal.html"
if not SRC.exists():
    st.error("developer_portal.html was not found next to Home.py. Upload it to the repository root.")
    st.stop()

LOGO = ('<svg viewBox="0 0 40 32" width="34" height="28"><rect x="0" y="16" width="7" height="16" rx="1.5" fill="#6cb4f5"/>'
        '<rect x="10" y="8" width="7" height="24" rx="1.5" fill="#1d6fd0"/><rect x="20" y="0" width="7" height="9" rx="1.5" fill="#d9262c"/>'
        '<rect x="20" y="12" width="7" height="6" rx="1.5" fill="#d9262c"/><rect x="20" y="21" width="7" height="11" rx="1.5" fill="#d9262c"/>'
        '<rect x="30" y="12" width="7" height="20" rx="1.5" fill="#0f2a4a"/></svg>')
TOOLS = [("Risk Calculator", "Risk_Calculator", "Snapshot, trajectory, cohort ranking and validation in one place."),
         ("HCC Calculator", "HCC_Calculator", "The liver cancer module, the published application."),
         ("Cohort Sandbox", "Cohort_Sandbox", "Try cohort ranking with sample data."),
         ("4D Risk Matrix", "4D_Risk_Matrix", "See how L, E, V and ρ combine into risk."),
         ("Live Risk Matrix", "Live_Risk_Matrix", "New: sliders with the formula and four matrices updating live."),
         ("RMTI Step by Step", "RMTI_Step_by_Step", "Walk through the method one step at a time."),
         ("Case Studies and Videos", "Case_Studies_and_Videos", "Liver, flood and heat case studies.")]
ICO = {"Risk_Calculator": "calculator", "HCC_Calculator": "liver", "Cohort_Sandbox": "users", "4D_Risk_Matrix": "cube",
       "Live_Risk_Matrix": "pulse", "RMTI_Step_by_Step": "route", "Case_Studies_and_Videos": "film"}
COL = ["#d9262c", "#a93f48", "#4fa095", "#1d6fd0", "#f2a100", "#e8553d", "#d9262c"]
ART = ui._hero_art()
STATS = "".join(f'<div class="st" style="--to:{v};--c:{c}"><div class="num"></div><div class="lb">{l}</div></div>'
                for v, l, c in [(4, "levers in one equation", "#d9262c"), (3, "cancer sites: liver, lung, breast", "#1d6fd0"),
                                (2, "domains: oncology and disaster science", "#4fa095"), (8, "scoring and validation endpoints", "#f2a100")])
nav = "".join(f'<a href="/{s}" target="_self">{t}</a>' for t, s, _ in TOOLS[:5])
cards = "".join(f'<a class="card" style="--c:{COL[i]}" href="/{s}" target="_self"><div class="ico"><svg viewBox="0 0 24 24">{ui._ICONS[ICO[s]]}</svg></div>'
                f'<h4>{t}</h4><p>{d}</p><span>Open →</span></a>' for i, (t, s, d) in enumerate(TOOLS))

st.markdown(f"""<style>
.block-container{{padding:0 !important;max-width:100% !important}}footer{{display:none}}[data-testid="stSidebarNav"]{{display:none}}
header[data-testid="stHeader"]{{background:transparent}}
.r{{font-family:Inter,"Segoe UI",system-ui,sans-serif;color:#0f2a4a}}
.r a{{text-decoration:none}}
.nav{{display:flex;align-items:center;gap:1.4rem;padding:.9rem 2rem;border-bottom:1px solid #d9e6f2;background:#fff;flex-wrap:wrap;margin-top:2.2rem}}
.nav .lg{{display:flex;align-items:center;gap:.5rem;color:#0f2a4a}}.nav .wm{{display:flex;flex-direction:column;line-height:1}}
.nav .wm b{{font-size:1.35rem;letter-spacing:.02em}}.nav .wm small{{font-size:.5rem;letter-spacing:.3em;font-weight:600;color:#4a6482;margin-top:.2rem}}
.nav .links{{display:flex;gap:1.2rem;flex:1;flex-wrap:wrap}}.nav .links a{{color:#0f2a4a;font-weight:600;font-size:.95rem}}.nav .links a:hover{{color:#1d6fd0}}
.btn{{background:#d9262c;color:#fff !important;padding:.6rem 1.2rem;border-radius:8px;font-weight:700;display:inline-block}}.btn:hover{{background:#b81e24}}
.btn.o{{background:#fff;color:#1d6fd0 !important;border:1.5px solid #1d6fd0}}
.hero{{background:linear-gradient(180deg,#eaf4ff 0%,#fff 100%);padding:3.5rem 2rem 2.5rem}}
.hi{{max-width:1180px;margin:auto;display:grid;grid-template-columns:1.05fr 1fr;gap:2.5rem;align-items:center}}
.eb{{color:#d9262c;font-weight:700;letter-spacing:.14em;font-size:.8rem}}
.hero h1{{font-size:clamp(2rem,4vw,3.2rem);line-height:1.12;margin:.6rem 0 1rem;font-weight:800;color:#0f2a4a}}
.hero p{{color:#3b5877;font-size:1.1rem;line-height:1.65;max-width:52ch}}.hero .row{{display:flex;gap:.8rem;margin-top:1.4rem;flex-wrap:wrap}}
.dash{{background:#fff;border:1px solid #d9e6f2;border-radius:14px;box-shadow:0 16px 40px rgba(29,111,208,.16);padding:14px 16px}}
.dash .t{{font-weight:700;font-size:.85rem;display:flex;gap:6px;align-items:center}}.dash .t i{{width:9px;height:9px;border-radius:50%;background:#d9262c}}.dash .t i+i{{background:#6cb4f5}}.dash .t i+i+i{{background:#1d6fd0;margin-right:6px}}
.ln{{stroke-dasharray:1;stroke-dashoffset:1;animation:dr 4.5s ease-in-out infinite}}@keyframes dr{{0%{{stroke-dashoffset:1}}70%,100%{{stroke-dashoffset:0}}}}
.dash table{{width:100%;border-collapse:collapse;font-size:.82rem;margin-top:6px}}.dash td{{padding:5px 4px;border-top:1px solid #eef3f9}}
.pill{{padding:2px 9px;border-radius:99px;font-weight:600;font-size:.74rem;background:#eaf4ff;color:#1d6fd0}}.pill.h{{background:#fde3e4;color:#a3161b}}.pill.l{{background:#f3f8fd;color:#4a6482}}
.sec{{max-width:1180px;margin:auto;padding:2.5rem 2rem 0}}.sec h2{{font-size:1.8rem;font-weight:800;margin:0 0 .3rem}}.sec .sub{{color:#4a6482;margin:0 0 1.2rem}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:1rem}}
.card{{display:block;background:#fff;border:1px solid #d9e6f2;border-radius:12px;padding:1.1rem 1.2rem;color:#0f2a4a;transition:all .15s}}
.card:hover{{border-color:#1d6fd0;box-shadow:0 8px 24px rgba(29,111,208,.15);transform:translateY(-2px)}}
.card h4{{margin:0 0 .3rem;font-size:1.08rem}}.card p{{margin:0 0 .7rem;color:#4a6482;font-size:.93rem;line-height:1.5}}.card span{{color:#d9262c;font-weight:700;font-size:.9rem}}
.foot{{margin-top:2.5rem;background:#0f2a4a;color:#cfe0f3;padding:1.6rem 2rem;font-size:.9rem;text-align:center}}
@media(max-width:860px){{.hi{{grid-template-columns:1fr}}}}
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@200;300;400;500;600&family=Inter:wght@400;500;600&display=swap');
.r{{font-family:Inter,"Segoe UI",system-ui,sans-serif}}
.hero h1,.sec h2,.card h4{{font-family:Outfit,Inter,sans-serif;font-weight:300;letter-spacing:-.015em}}
.hero h1{{font-size:clamp(2.2rem,4.4vw,3.6rem);line-height:1.08}}.sec h2{{font-size:clamp(1.6rem,2.6vw,2.2rem)}}.card h4{{font-size:1.2rem;font-weight:400}}
.hero{{position:relative;overflow:hidden;background:linear-gradient(120deg,#fff 0%,#f6f8fb 55%,#eaf4ff 100%)}}
.hero>.art{{position:absolute;right:-60px;top:0;height:100%;width:52%;min-width:380px;opacity:.55;pointer-events:none}}
.hi{{position:relative;z-index:2}}
.btn{{border-radius:999px;transition:transform .15s,box-shadow .15s}}.btn:hover{{transform:translateY(-2px);box-shadow:0 10px 24px rgba(217,38,44,.3)}}
.dash{{border-radius:22px;animation:rise .8s ease both}}
.art .f1{{animation:fa 7s ease-in-out infinite}}.art .f2{{animation:fb 9s ease-in-out infinite}}.art .f3{{animation:fa 11s ease-in-out infinite reverse}}
.art .spin{{transform-origin:300px 220px;animation:sp 26s linear infinite}}.art .pls{{transform-box:fill-box;transform-origin:center;animation:pl 3.6s ease-in-out infinite}}
.art .dsh{{stroke-dasharray:6 10;animation:ds 3s linear infinite}}
@keyframes fa{{0%,100%{{transform:translate(0,0)}}50%{{transform:translate(-18px,14px)}}}}@keyframes fb{{0%,100%{{transform:translate(0,0)}}50%{{transform:translate(16px,-16px)}}}}
@keyframes sp{{to{{transform:rotate(360deg)}}}}@keyframes pl{{0%,100%{{transform:scale(1)}}50%{{transform:scale(1.18)}}}}@keyframes ds{{to{{stroke-dashoffset:-64}}}}
@keyframes rise{{from{{opacity:0;transform:translateY(16px)}}to{{opacity:1;transform:none}}}}
@property --n{{syntax:'<integer>';initial-value:0;inherits:false}}
.stats{{max-width:1180px;margin:-1.2rem auto 0;padding:0 2rem;display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:1rem;position:relative;z-index:3}}
.st{{background:#fff;border:1px solid #d9e6f2;border-radius:18px;padding:1.1rem 1.3rem;position:relative;overflow:hidden;box-shadow:0 10px 28px rgba(15,42,74,.08);transition:transform .2s;animation:rise .7s ease both}}
.st:hover{{transform:translateY(-4px)}}.st:before{{content:"";position:absolute;left:0;top:0;width:100%;height:4px;background:var(--c)}}
.st .num{{font-family:Outfit;font-weight:300;font-size:2.6rem;line-height:1.1;counter-reset:n var(--n);animation:cnt 1.8s cubic-bezier(.2,.7,.2,1) forwards}}
.st .num:after{{content:counter(n)}}.st .lb{{font-size:.86rem;color:#4a6482;margin-top:.2rem}}
@keyframes cnt{{from{{--n:0}}to{{--n:var(--to)}}}}
.card{{border-radius:20px;padding:1.4rem;position:relative;animation:rise .7s ease both}}
.card:hover{{border-color:var(--c);transform:translateY(-6px);box-shadow:0 18px 38px rgba(15,42,74,.12)}}
.card .ico{{width:52px;height:52px;border-radius:15px;display:grid;place-items:center;background:color-mix(in srgb,var(--c) 12%,white);margin-bottom:.9rem}}
.card .ico svg{{width:28px;height:28px;stroke:var(--c);fill:none;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}}
.card:hover .ico svg{{animation:wg .7s ease}}@keyframes wg{{0%,100%{{transform:rotate(0)}}30%{{transform:rotate(-10deg) scale(1.08)}}60%{{transform:rotate(8deg)}}}}
.card span{{color:var(--c)}}
.foot{{background:linear-gradient(135deg,#0f2a4a,#17406e)}}
@media (prefers-reduced-motion:reduce){{*{{animation:none !important;transition:none !important}}.st .num{{--n:var(--to)}}}}
</style>
<div class="r">
<div class="nav"><a class="lg" href="/" target="_self">{LOGO}<span class="wm"><b>RMTI</b><small>ONCOCLASTICS</small></span></a>
<div class="links">{nav}</div><a class="btn" href="https://orcid.org/0000-0001-8498-7380" target="_blank">Request API access</a></div>
<div class="hero">{ART}<div class="hi"><div><div class="eb">RISK INTELLIGENCE</div>
<h1>Time-indexed risk scoring for cancer care and disaster science</h1>
<p>Score hazard, exposure, vulnerability and resilience for liver, lung and breast cancer and for floods and heat. Use the tools in your browser or call the API.</p>
<div class="row"><a class="btn" href="/Risk_Calculator" target="_self">Open the Risk Calculator</a><a class="btn o" href="/Live_Risk_Matrix" target="_self">See the live matrix</a></div></div>
<div class="dash"><div class="t"><i></i><i></i><i></i>Risk trajectory · synthetic data</div>
<svg viewBox="0 0 360 140" width="100%"><g stroke="#e3edf7"><line x1="0" y1="30" x2="360" y2="30"/><line x1="0" y1="70" x2="360" y2="70"/><line x1="0" y1="110" x2="360" y2="110"/></g>
<polyline class="ln" pathLength="1" points="0,110 60,96 120,102 180,64 240,50 300,38 360,22" fill="none" stroke="#d9262c" stroke-width="3.5" stroke-linecap="round"/>
<polyline points="0,118 60,112 120,108 180,100 240,92 300,88 360,80" fill="none" stroke="#1d6fd0" stroke-width="3" stroke-linecap="round" opacity=".8"/></svg>
<table><tr><td>P-01</td><td>Liver</td><td><span class="pill">moderate</span></td></tr><tr><td>P-02</td><td>Lung</td><td><span class="pill h">high</span></td></tr><tr><td>P-03</td><td>Breast</td><td><span class="pill l">low</span></td></tr></table></div></div></div>
<div class="stats">{STATS}</div>
<div class="sec"><h2>Choose a tool to get started</h2><p class="sub">Every tool opens in its own page. Use the top menu to move between them at any time.</p><div class="grid">{cards}</div></div>
<div class="sec"><h2>Cancer-site and disaster models</h2><p class="sub">Drag to turn a model. Liver, lung, breast and disaster science each have their own module.</p></div></div>""", unsafe_allow_html=True)

FIX = """<script>document.addEventListener('click',function(e){var a=e.target.closest('a[href^="#"]');
if(a){e.preventDefault();location.hash=a.getAttribute('href');}});</script></body>"""
def view(css, height):
    html = SRC.read_text(encoding="utf-8").replace("</head>", "<style>" + css + "</style></head>", 1).replace("</body>", FIX, 1)
    components.html(html, height=height, scrolling=True)

view("header.top,.docs,footer,.notice{display:none!important}body{background:#fff}.stage{padding:.5rem 2rem}", 470)
st.markdown('<div class="r"><div class="sec"><h2>API documentation</h2><p class="sub">Eight scoring and validation endpoints plus the evidence registry. JSON in, JSON out.</p></div></div>', unsafe_allow_html=True)
view("header.top,.stage,footer,.notice{display:none!important}aside{top:8px!important}html{scroll-padding-top:8px!important}", 1000)
video = ROOT / "rmti_1_explained.mp4"
if video.exists():
    with st.expander("▶ Watch: RMTI explained"):
        st.video(str(video))
st.markdown('<div class="r"><div class="foot">Oncoclastics Platform on RMTI engine v2.4.0. Apache-2.0. Research use only. drmarolla_rmti@2026</div></div>', unsafe_allow_html=True)
