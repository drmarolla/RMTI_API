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

if not nav_mode:    # old layout: no grouped sidebar, so keep a compact link row
    st.markdown(f'<div style="width:230px;margin-bottom:.4rem">{ui.logo_svg()}</div>', unsafe_allow_html=True)
    st.markdown("""<div class="rm-tools">
<a href="/Risk_Calculator" target="_self">Risk Calculator</a><a href="/HCC_Calculator" target="_self">HCC Calculator</a>
<a href="/Cohort_Sandbox" target="_self">Cohort Sandbox</a><a href="/4D_Risk_Matrix" target="_self">4D Risk Matrix</a>
<a href="/RMTI_Step_by_Step" target="_self">Step by Step</a><a href="/Case_Studies_and_Videos" target="_self">Case Studies</a>
<a href="/Johnson_Case_Study" target="_self">Johnson Case Study</a><a href="/Live_Risk_Matrix" target="_self">Live Risk Matrix</a></div>""",
                unsafe_allow_html=True)
else:
    st.markdown(f'<div style="width:230px;margin-bottom:.6rem">{ui.logo_svg()}</div>', unsafe_allow_html=True)

st.markdown('<div class="rm-kicker">Oncology and disaster science</div>', unsafe_allow_html=True)
st.title("Oncoclastics")
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

st.header("From tumor events to trajectory")
st.caption("Liver (Lau-Min 2025), lung (Sabakhtarishvili 2025) and breast (O\u2019Shaughnessy 2026) cohorts, followed from Stage 1 to Stage 4 "
           "and scored with RMTI. Switch organ and pace under the player. Research prototype; mappings are illustrative.")
_anim = next((c for c in (ROOT / "animation" / "index.html", ROOT / "index.html")
              if c.exists() and "tumor events to trajectory" in c.read_text(encoding="utf-8", errors="ignore")), None)
if _anim:
    components.html(_anim.read_text(encoding="utf-8").replace("</body>", FIT, 1), height=820, scrolling=True)
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
