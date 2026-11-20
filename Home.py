"""Oncoclastics / RMTI home page. Runs inside streamlit_app.py (grouped navigation) or on its own."""
import sys
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Oncoclastics \u00b7 RMTI", page_icon="\U0001F9EC", layout="wide", initial_sidebar_state="collapsed")
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import oncoclastic_style as ui  # noqa: E402

ui.apply(first_page=True)
DOI = "10.5281/zenodo.24254220"
nav_mode = st.session_state.get("rmti_nav", False)
FIT = ("<script>(function(){function f(){try{var h=document.documentElement.scrollHeight;var e=window.frameElement;"
       "if(e&&h>0){e.style.height=(h+8)+'px';}}catch(x){}}window.addEventListener('load',function(){f();setTimeout(f,400);setTimeout(f,1500);});})();</script></body>")

ui.hero_lp(
    "Risk intelligence \u203a Oncoclastics",
    "Quantify systemic risk.<br><em>Before it fragments care.</em>",
    "Oncoclastics applies hazard\u2013exposure\u2013vulnerability\u2013resilience assessment from disaster-risk reduction to cancer: "
    "one equation, four levers, real case studies in liver, lung and breast oncology, floods and heat.",
    ("Explore the tools", "#pathways"), ("Watch the case study", "#trajectory"))
ui.stats([(4, "levers in one equation", "", ui.RED), (3, "cancer sites: liver, lung, breast", "", ui.BLUE_A),
          (2, "domains: oncology and disaster science", "", ui.RED_L), (3, "narrated video walkthroughs", "", ui.BLUE_L)])

ui.benefits("Key benefits of the RMTI platform", "One method, <b>clear answers</b> from risk to trajectory", [
    dict(icon="target", title="One equation, four levers", text="Likelihood, exposure, vulnerability and resilience combine into a single score, R = L \u00b7 E \u00b7 V \u00b7 (1 \u2212 \u03c1).", color=ui.RED),
    dict(icon="gauge", title="Fixed risk tiers", text="A fixed five-band scale (0, 0.05, 0.15, 0.35, 0.60, 1.0) so a score means the same thing every time.", color=ui.BLUE_A),
    dict(icon="trend", title="Trajectory over time", text="Track V(t) and \u03c1(t) across review cycles: is risk drifting, or is delivery closing the gap?", color=ui.RED),
    dict(icon="wave", title="Expected annual loss", text="EAL = L \u00b7 C \u00b7 (1 \u2212 \u03c1) adds a loss layer on top of the score for planning and comparison.", color=ui.BLUE_D),
    dict(icon="liver", title="Liver, lung and breast", text="Published cohorts followed from Stage 1 to Stage 4 and scored with RMTI, with the sources cited.", color=ui.BLUE_A),
    dict(icon="pulse", title="Floods and heat", text="The same four levers score disaster hazards, the field the method comes from.", color=ui.RED),
    dict(icon="code", title="Open API", text="Eight scoring and validation endpoints plus an evidence registry. JSON in, JSON out.", color=ui.BLUE_D),
    dict(icon="shield", title="Transparent by design", text="Research prototype on synthetic or published values. Not validated, not a medical device. Apache-2.0.", color=ui.RED),
])

ui.section("Platform", "Choose a tool to get started", "Every tool runs on synthetic or published aggregate data.", anchor="pathways")
ui.path_cards([
    dict(icon="calculator", title="Risk Calculator", text="Snapshot, trajectory, cohort ranking and validation in one place.", tag="Calculator", color=ui.RED, href="/Risk_Calculator"),
    dict(icon="liver", title="HCC Calculator", text="Chronic liver injury toward hepatocellular carcinoma, including non-cirrhotic HCC.", tag="Oncology", color=ui.BLUE_A, href="/HCC_Calculator"),
    dict(icon="users", title="Cohort Sandbox", text="Rank a cohort and see how the tiers relate to outcomes.", tag="Simulation", color=ui.RED, href="/Cohort_Sandbox"),
    dict(icon="cube", title="4D Risk Matrix", text="See how L, E, V and \u03c1 combine into risk.", tag="Visual", color=ui.BLUE_D, href="/4D_Risk_Matrix"),
    dict(icon="pulse", title="Live Risk Matrix", text="Sliders with the formula and four matrices updating live.", tag="Interactive", color=ui.RED, href="/Live_Risk_Matrix"),
    dict(icon="route", title="Step by Step", text="Walk through the RMTI method one step at a time.", tag="Learn", color=ui.BLUE_A, href="/RMTI_Step_by_Step"),
    dict(icon="film", title="Case Studies and Videos", text="Liver, flood and heat case studies with narrated 3D/4D walkthroughs.", tag="Evidence", color=ui.RED, href="/Case_Studies_and_Videos"),
    dict(icon="code", title="Developer Portal", text="Score the four levers through the API or in your browser.", tag="API", color=ui.BLUE_D, href="/Developer_Portal"),
])
ui.equation_banner()
ui.industries("Fields", "Supporting <b>oncology and disaster science</b> with one method",
              "RMTI began in disaster-risk reduction, where hazard, exposure, vulnerability and resilience are scored together. "
              "Oncoclastics applies the same logic to cancer care, from chronic liver injury toward HCC to lung and breast cancer.")

ui.section("Definition", "Oncoclastics")
st.markdown("""<div class="rm-card">
We use the term <b>oncoclastics</b> (adjective: <i>oncoclastic</i>; from <i>onco-</i>, tumor, and <i>-clastic</i>, broken or fragmented,
from the Greek <i>klastos</i>) for the application of hazard–exposure–vulnerability–resilience assessment, as developed in
disaster-risk reduction, to the fragmentation of cancer-related trajectories, whether biological (the progression from chronic injury
to cancer; <i>biological oncoclastics</i>) or systemic (the disruption of surveillance and care; <i>care-system oncoclastics</i>).
To our knowledge the term is new. Its closest relatives point elsewhere: an oncolytic agent destroys tumor cells (Russell et al., 2012)
and an osteoclast resorbs bone (Teitelbaum, 2000), whereas what is broken here is the continuity of a trajectory or care pathway,
not the tumor.<br><br>
We use the biological sense, with the path from chronic liver injury toward HCC, including noncirrhotic HCC, as the trajectory of
interest; the care-system sense enters only through the care-system component of <span class="rm-sym">ρ</span>. The same framing
applies to oncology in general, including lung and breast cancer.</div>""", unsafe_allow_html=True)

st.markdown("""
| RMTI term | Biological oncoclastics | Care-system oncoclastics (through <span class="rm-sym">ρ</span>) |
|---|---|---|
| **Unit** | Individual patient; progression from chronic injury toward cancer | Care pathway of the same patient (surveillance and follow-up) |
| <span class="rm-sym">L</span> likelihood | Probability of progression to cancer over the horizon | Not changed by disruption of care |
| <span class="rm-sym">E</span> exposure | Burden of metabolic, inflammatory, toxic or hemodynamic insults | Not changed by disruption of care |
| <span class="rm-sym">V</span> vulnerability | Allostatic load carried forward across cycles | Not scored separately |
| <span class="rm-sym">ρ</span> resilience | Biological adaptive reserve, <span class="rm-sym">ρ<sub>bio</sub></span> | Care-system capacity, <span class="rm-sym">ρ<sub>care</sub></span> |
""", unsafe_allow_html=True)
st.markdown(f'<div class="rm-card soft"><b>Cite:</b> Marolla C. <i>Oncoclastics: definition note, version 1.0.0.</i> Zenodo; 2026. '
            f'<a href="https://doi.org/{DOI}">doi:{DOI}</a></div>', unsafe_allow_html=True)

st.markdown('<a id="trajectory"></a>', unsafe_allow_html=True)
_anim = next((c for c in (ROOT / "animation" / "index.html", ROOT / "index.html")
              if c.exists() and "tumor events to trajectory" in c.read_text(encoding="utf-8", errors="ignore")), None)
if _anim:
    components.html(_anim.read_text(encoding="utf-8").replace("</body>", FIT, 1), height=1100, scrolling=True)
    # The music plays through Streamlit's own audio element (reliable on Streamlit Cloud, unlike files in static/).
    # The red Play button inside the animation controls this element; the native controls stay as a fallback.
    _mp3 = ROOT / "static" / "concerto_santa_lucia.mp3"
    if _mp3.exists():
        st.caption("Music player: if the red Play button inside the animation does not start the music, press play here.")
        try:
            st.audio(str(_mp3), format="audio/mpeg", loop=True)
        except TypeError:                  # older Streamlit without the loop option
            st.audio(str(_mp3), format="audio/mpeg")
    st.caption("Liver (Lau-Min 2025), lung (Sabakhtarishvili 2025) and breast (O\u2019Shaughnessy 2026) cohorts, followed from Stage 1 to Stage 4 "
               "and scored with RMTI. Music: Concerto di Santa Lucia by Dr. Cesar Marolla. Research prototype; mappings are illustrative.")
else:
    st.info("The case-study animation file was not found. Upload animation/index.html to the repository.")

_vids = {}
for _d in (ROOT / "media", ROOT):
    if _d.is_dir():
        for _f in sorted(_d.glob("*.mp4")):
            _vids.setdefault(_f.stem, _f)
if _vids:
    st.header("RMTI videos")
    _labels = list(_vids)
    _fmt = lambda n: n.replace("rmti_", "").replace("_", " ").title()  # noqa: E731
    if hasattr(st, "segmented_control"):
        _name = st.segmented_control("Video", _labels, default=_labels[0], format_func=_fmt, label_visibility="collapsed") or _labels[0]
    else:
        _name = st.radio("Video", _labels, horizontal=True, format_func=_fmt, label_visibility="collapsed")
    _vid = _vids[_name]
    if _vid.stat().st_size < 10_000:
        st.warning("This video file is only a few KB. It is probably a Git LFS pointer, not the real video. Upload the MP4 again without LFS.")
    _subs = next((str(c) for e in (".vtt", ".srt") for c in (_vid.with_suffix(e), ROOT / "media" / (_vid.stem + e)) if c.exists()), None)
    try:
        st.video(str(_vid), subtitles=_subs) if _subs else st.video(str(_vid))
    except TypeError:
        st.video(str(_vid))

st.header("Developers")
st.markdown('<div class="rm-card soft">Score hazard, exposure, vulnerability and resilience for liver, lung and breast cancer and for '
            'floods and heat, in your browser or through the API. <a href="/Developer_Portal" target="_self"><b>Open the developer portal</b></a></div>',
            unsafe_allow_html=True)
st.caption("Research prototype. Not validated; not a medical device; not for patient-care decisions. Synthetic examples. Apache-2.0.")
