"""RMTI home page: navy, white and red landing page. Menu with grouped pages, showreel hero, organ cards, tool cards, API docs. Set as Main file path.

Needs next to this file: developer_portal.html (API docs, optional) and media/rmti_showreel.mp4, media/poster_liver.jpg, media/poster_lungs.jpg,
media/poster_breast.jpg (the showreel and its stills). Research prototype. Illustrative synthetic data; not a medical device.
"""
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="RMTI Oncoclastics", page_icon="🧬", layout="wide", initial_sidebar_state="collapsed")
ROOT = Path(__file__).resolve().parent
MEDIA = ROOT / "media"
SRC = ROOT / "developer_portal.html"

LOGO = ('<svg viewBox="0 0 40 32" width="34" height="28"><rect x="0" y="16" width="7" height="16" rx="1.5" fill="#6cb4f5"/>'
        '<rect x="10" y="8" width="7" height="24" rx="1.5" fill="#2d78dc"/><rect x="20" y="0" width="7" height="9" rx="1.5" fill="#d9262c"/>'
        '<rect x="20" y="12" width="7" height="6" rx="1.5" fill="#d9262c"/><rect x="20" y="21" width="7" height="11" rx="1.5" fill="#d9262c"/>'
        '<rect x="30" y="12" width="7" height="20" rx="1.5" fill="#ffffff"/></svg>')

# group, [(title, url name, what it is for)]. The URL name is the page file name without its number and .py.
GROUPS = [
    ("Calculators", "Enter values, get a score", [
        ("Risk Calculator", "Risk_Calculator", "Score one case or a whole cohort. Four tabs: snapshot, trajectory, cohort ranking and retrospective validation, each with the tier and its posture."),
        ("HCC Calculator", "HCC_Calculator", "The liver cancer module, the published application, with the HCC inputs laid out as in the paper."),
        ("Cohort Sandbox", "Cohort_Sandbox", "Rank a sample cohort and see which patients to reach first. Sample data only.")]),
    ("Matrices", "See where risk sits in the L, E, V cube", [
        ("4D Risk Matrix", "4D_Risk_Matrix", "Plot cases in the cube with ρ as colour, and follow one patient's path through time."),
        ("Live Risk Matrix", "Live_Risk_Matrix", "Drag the sliders and watch the formula and four matrices update as you move.")]),
    ("Animations", "Watch the calculation unfold", [
        ("RMTI Step by Step", "RMTI_Step_by_Step", "Play R = L · E · V · (1 − ρ) one factor at a time."),
        ("Live 4D Lab", "Live_4D_Lab", "Move the levers on seven case studies: Faria et al. liver cohorts, Lilongwe, Lagos, Bamako, Pacific Palisades and Altadena."),
        ("Liver Progression 4D", "Liver_Progression_4D", "A rotating liver driven by the time-indexed trajectory, cycle by cycle."),
        ("Case Studies and Videos", "Case_Studies_and_Videos", "Narrated videos and the Lever Lab for liver, flood and heat.")]),
]
ORGANS = [("Liver", "poster_liver.jpg", "Liver_Progression_4D", "Open the liver animation",
           "Hepatocellular carcinoma surveillance. The surface follows vulnerability V*(t); the red sphere's volume follows R(t)."),
          ("Lungs", "poster_lungs.jpg", "Risk_Calculator", "Open the Risk Calculator",
           "Lung cancer risk and screening. Airways and a red sphere sized by R(t), from the same time-indexed engine."),
          ("Breast", "poster_breast.jpg", "Risk_Calculator", "Open the Risk Calculator",
           "Female breast cancer. A ductal-anatomy schematic with a red sphere sized by R(t). A proposed module, not validated.")]

nav = "".join('<div class="dd"><span>%s ▾</span><div class="menu">%s</div></div>' % (g, "".join('<a href="/%s" target="_self">%s</a>' % (s, t) for t, s, _ in items))
              for g, _, items in GROUPS) + '<a class="plain" href="#api" target="_self">API</a>'

CSS = """<style>
.block-container{padding:0 !important;max-width:100% !important}footer{display:none}
header[data-testid="stHeader"]{background:transparent}
.r{font-family:Inter,"Segoe UI",system-ui,sans-serif;color:#0b2545}.r a{text-decoration:none}
.nav{display:flex;align-items:center;gap:1.6rem;padding:.85rem 2rem;background:#0b2545;flex-wrap:wrap;margin-top:2.2rem;position:relative;z-index:50}
.nav .lg{display:flex;align-items:center;gap:.55rem;color:#fff}.nav .wm{display:flex;flex-direction:column;line-height:1}
.nav .wm b{font-size:1.35rem;letter-spacing:.02em;color:#fff}.nav .wm small{font-size:.5rem;letter-spacing:.3em;font-weight:600;color:#9fb3c8;margin-top:.2rem}
.nav .links{display:flex;gap:1.5rem;flex:1;flex-wrap:wrap;align-items:center}
.nav .dd{position:relative;padding:.4rem 0}.nav .dd>span,.nav .plain{color:#fff;font-weight:600;font-size:1rem;cursor:pointer}
.nav .dd:hover>span,.nav .plain:hover{color:#ff7074}
.nav .menu{display:none;position:absolute;top:100%;left:-.8rem;min-width:230px;background:#fff;border-radius:10px;box-shadow:0 14px 34px rgba(11,37,69,.28);padding:.5rem;border:1px solid #d6e2f2}
.nav .dd:hover .menu{display:block}.nav .menu a{display:block;padding:.55rem .8rem;border-radius:7px;color:#0b2545;font-weight:600;font-size:.95rem}
.nav .menu a:hover{background:#eef3fa;color:#d9262c}
.btn{background:#d9262c;color:#fff !important;padding:.65rem 1.25rem;border-radius:8px;font-weight:700;display:inline-block}.btn:hover{background:#b81e24}
.btn.o{background:#fff;color:#0b2545 !important;border:1.5px solid #0b2545}.btn.o:hover{background:#eef3fa}
.eb{color:#d9262c;font-weight:700;letter-spacing:.14em;font-size:.82rem}
.hero h1{font-size:clamp(2rem,3.6vw,3.1rem);line-height:1.12;margin:.6rem 0 1rem;font-weight:800;color:#0b2545}
.hero p{color:#34506f;font-size:1.12rem;line-height:1.65;max-width:50ch}.hero .row{display:flex;gap:.8rem;margin-top:1.4rem;flex-wrap:wrap}
.sec{max-width:1180px;margin:auto;padding:2.8rem 2rem 0}.sec h2{font-size:1.85rem;font-weight:800;margin:0 0 .3rem;color:#0b2545}.sec .sub{color:#34506f;margin:0 0 1.2rem;font-size:1.02rem}
.sec h3{font-size:1.15rem;font-weight:800;margin:1.6rem 0 .1rem;color:#0b2545;border-left:4px solid #d9262c;padding-left:.7rem}.sec h3 small{display:block;font-weight:500;color:#5b7391;font-size:.9rem;margin-top:.1rem}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:1rem;margin-top:.9rem}
.card{display:block;background:#fff;border:1px solid #d6e2f2;border-radius:12px;padding:1.1rem 1.2rem;color:#0b2545;transition:all .15s}
.card:hover{border-color:#0b2545;box-shadow:0 8px 24px rgba(11,37,69,.14);transform:translateY(-2px)}
.card h4{margin:0 0 .35rem;font-size:1.08rem;color:#0b2545}.card p{margin:0 0 .7rem;color:#34506f;font-size:.95rem;line-height:1.5}.card span{color:#d9262c;font-weight:700;font-size:.92rem}
.oc h4{margin:.7rem 0 .2rem;font-size:1.25rem;color:#0b2545}.oc p{margin:0 0 .6rem;color:#34506f;font-size:.95rem;line-height:1.5}
.oc a{color:#d9262c;font-weight:700;font-size:.95rem}
.foot{margin-top:2.5rem;background:#0b2545;color:#d6e2f2;padding:1.6rem 2rem;font-size:.92rem;text-align:center}
[data-testid="stHorizontalBlock"]{max-width:1180px;margin-left:auto;margin-right:auto;padding:0 2rem;align-items:center}
[data-testid="stVideo"]{border-radius:14px;overflow:hidden;box-shadow:0 16px 40px rgba(11,37,69,.25)}
[data-testid="stImage"] img{border-radius:12px;box-shadow:0 8px 22px rgba(11,37,69,.18)}
[data-testid="stExpander"]{max-width:1116px;margin:1rem auto 0}
</style>"""


def show_video(path, **kw):
    try:
        st.video(str(path), **kw)
    except TypeError:                                  # older Streamlit: no autoplay/loop/muted arguments
        st.video(str(path))


def show_image(path):
    try:
        st.image(str(path), use_container_width=True)
    except TypeError:
        st.image(str(path))


st.markdown(CSS + """<div class="r"><div class="nav"><a class="lg" href="/" target="_self">%s<span class="wm"><b>RMTI</b><small>ONCOCLASTICS</small></span></a>
<div class="links">%s</div><a class="btn" href="https://orcid.org/0000-0001-8498-7380" target="_blank">Request API access</a></div></div>""" % (LOGO, nav), unsafe_allow_html=True)

left, right = st.columns([1.05, 1], gap="large")
with left:
    st.markdown("""<div class="r hero" style="padding:2.4rem 0 1rem"><div class="eb">RISK INTELLIGENCE</div>
<h1>Time-indexed risk scoring for cancer care and disaster science</h1>
<p>Score hazard, exposure, vulnerability and resilience for liver, lung and breast cancer and for floods, heat and wildfire. Use the tools in your browser or call the API.</p>
<div class="row"><a class="btn" href="/Risk_Calculator" target="_self">Open the Risk Calculator</a><a class="btn o" href="/Live_4D_Lab" target="_self">Try the Live 4D Lab</a></div></div>""", unsafe_allow_html=True)
with right:
    reel = MEDIA / "rmti_showreel.mp4"
    if reel.exists():
        show_video(reel, autoplay=True, muted=True, loop=True)
    else:
        st.info("The showreel (media/rmti_showreel.mp4) has not been uploaded yet.")

st.markdown('<div class="r"><div class="sec"><h2>Liver, lungs and breast, in motion</h2><p class="sub">A stylised model for each site, drawn from the engine\'s own numbers. '
            'Illustrative synthetic data, not images of patients.</p></div></div>', unsafe_allow_html=True)
cols = st.columns(3, gap="medium")
for col, (name, poster, slug, label, text) in zip(cols, ORGANS):
    with col:
        if (MEDIA / poster).exists():
            show_image(MEDIA / poster)
        st.markdown('<div class="r oc"><h4>%s</h4><p>%s</p><a href="/%s" target="_self">%s →</a></div>' % (name, text, slug, label), unsafe_allow_html=True)

body = ['<div class="r"><div class="sec"><h2>Choose a tool to get started</h2><p class="sub">Three kinds of page. Calculators give you a score, matrices show where it sits, animations show how it moves. '
        'Use the top menu to switch at any time.</p>']
for g, blurb, items in GROUPS:
    body.append('<h3>%s<small>%s</small></h3><div class="grid">%s</div>' % (g, blurb, "".join(
        '<a class="card" href="/%s" target="_self"><h4>%s</h4><p>%s</p><span>Open →</span></a>' % (s, t, d) for t, s, d in items)))
body.append('<h2 id="api" style="margin-top:2.6rem">API documentation</h2><p class="sub">Scoring, validation, evidence-registry, scene and liver-progression endpoints. JSON in, JSON out.</p></div></div>')
st.markdown("".join(body), unsafe_allow_html=True)

FIX = """<script>document.addEventListener('click',function(e){var a=e.target.closest('a[href^="#"]');
if(a){e.preventDefault();location.hash=a.getAttribute('href');}});</script></body>"""
if SRC.exists():
    css = "header.top,.stage,footer,.notice{display:none!important}aside{top:8px!important}html{scroll-padding-top:8px!important}"
    html = SRC.read_text(encoding="utf-8").replace("</head>", "<style>" + css + "</style></head>", 1).replace("</body>", FIX, 1)
    components.html(html, height=1000, scrolling=True)
else:
    st.warning("developer_portal.html was not found next to Home.py, so the API documentation is not shown. Upload it to the repository root.")

v2 = MEDIA / "rmti_2_liver_case_studies.mp4"
if v2.exists():
    with st.expander("▶ Watch: liver case studies (5 minutes)"):
        show_video(v2)
st.markdown('<div class="r"><div class="foot">Oncoclastics Platform on RMTI engine v2.4.0. Apache-2.0. Research use only. Not a medical device. drmarolla_rmti@2026 · Build 2026-11-15 · navy, white and red</div></div>', unsafe_allow_html=True)
