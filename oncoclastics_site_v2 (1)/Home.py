"""Oncoclastics / RMTI home page. Main file path in Streamlit Cloud: Home.py."""
import sys
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Oncoclastics · RMTI", page_icon="🧬", layout="wide", initial_sidebar_state="collapsed")
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import oncoclastic_style as ui  # noqa: E402

ui.apply(first_page=True)
DOI = "10.5281/zenodo.24254220"

st.markdown(f'<div style="width:230px;margin-bottom:.4rem">{ui.logo_svg()}</div>', unsafe_allow_html=True)
st.markdown("""<div class="rm-tools">
<a href="/Risk_Calculator" target="_self">Risk Calculator</a><a href="/HCC_Calculator" target="_self">HCC Calculator</a>
<a href="/Cohort_Sandbox" target="_self">Cohort Sandbox</a><a href="/4D_Risk_Matrix" target="_self">4D Risk Matrix</a>
<a href="/RMTI_Step_by_Step" target="_self">Step by Step</a><a href="/Case_Studies_and_Videos" target="_self">Case Studies</a>
<a href="/Johnson_Case_Study" target="_self">Johnson Case Study</a><a href="/Live_Risk_Matrix" target="_self">Live Risk Matrix</a></div>""",
            unsafe_allow_html=True)

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
interest; the care-system sense enters only through the care-system component of ρ. The same framing applies to oncology in general,
including lung and breast cancer.</div>""", unsafe_allow_html=True)

with st.expander("Use of the RMTI domains in the two senses of oncoclastics", expanded=True):
    st.markdown("""
| Term | Definition in this article | Biological oncoclastics (used here) | Care-system oncoclastics (through ρ) |
|---|---|---|---|
| **Unit** | Individual patient, rescored over successive assessments | Individual patient; progression from chronic injury toward HCC | Care pathway of the same patient (surveillance and follow-up) |
| **L** | Likelihood of the outcome over a defined horizon, from a stage-anchored or validated model, rescaled to a bounded score | Probability of progression to cancer (for example, HCC) over the horizon | Not changed by disruption of care; remains the outcome probability |
| **E** | Cumulative burden imposed on the liver (magnitude, duration, frequency) | Burden of metabolic, inflammatory, toxic or hemodynamic insults on the liver | Not changed by disruption of care |
| **V** | Accumulated cost of prior injury and incomplete adaptation (allostatic load) | Allostatic load carried forward across cycles | Not scored separately in this article |
| **ρ** | Adaptive reserve: the fraction of inherent risk that is absorbed. (1 − ρ) is the unabsorbed fraction | Biological adaptive reserve, ρ<sub>bio</sub> | Care-system capacity, ρ<sub>care</sub> (delivery of surveillance, access to follow-up); ρ = 1 − (1 − ρ<sub>bio</sub>)(1 − ρ<sub>care</sub>) (Supplementary Material S5) |
""", unsafe_allow_html=True)
    st.caption("Definitions follow Table 1 and Supplementary Material S5.")

with st.expander("Analogy and limits"):
    st.markdown("""
The analogy to disaster risk is structural, not literal. It holds where the architecture does the work: hazard, exposure, vulnerability and
absorptive capacity are separable terms with distinct directions of effect, accumulated cost carries forward, and the index is built for
repeated reassessment. It does not hold in other respects. A neoplastic process is not an exogenous hazard, L and E are partly intrinsic to
the patient, the scores are relative and uncalibrated, and the vocabulary of disaster should not be read as a description of any patient’s
experience. The index decomposes the surveillance cascade into separately scored domains, using transparent, bounded, multiplicative
arithmetic, with inputs scored on bounded scales from stated anchors (Supplementary Tables S3 and S4). It is a transparent, rule-based,
auditable layer that may support prioritization within risk-stratified surveillance. The limitations of this article apply in full: tier
cut-points are inherited and uncalibrated, the measures of V and ρ are immature proxies, rubric scoring involves analyst judgment, and no
clinical action is attached to any tier. If validated, the approach may help identify patients whose trajectories warrant closer follow-up or
earlier prioritization of surveillance; whether it does is a proposition to be tested against the criteria in Table 4.
""")

with st.expander("Attribution, naming and archive"):
    st.markdown(f"""
The Risk Mechanism Theory Index, including its adaptation to oncology, was developed by Marolla (2018, 2026a, 2026b); the term oncoclastics
is introduced in this article. In every use, RMTI denotes the Risk Mechanism Theory Index. Because the acronym has unrelated uses elsewhere,
the full name is given at first use and is recommended in search terms and keywords. A definition note for the term (version 1.0.0) is
archived within the same Zenodo record as the time-indexed software (Marolla, 2026d). Evaluation of the oncoclastic perspective on
retrospective clinical data is the subject of a separate study in preparation.

**Zenodo DOI:** [{DOI}](https://doi.org/{DOI})
""")

st.header("From tumor events to trajectory")
_anim = None
for _c in (ROOT / "animation" / "index.html", ROOT / "index.html", ROOT / "media" / "index.html"):
    if _c.exists() and "tumor events to trajectory" in _c.read_text(encoding="utf-8", errors="ignore"):
        _anim = _c
        break
st.caption("Liver (Lau-Min 2025), lung (Sabakhtarishvili 2025) and breast (O’Shaughnessy 2026) cohorts, followed from Stage 1 to Stage 4 "
           "and scored with RMTI. Switch organ and pace under the player. Research prototype; mappings are illustrative.")
if _anim:
    components.html(_anim.read_text(encoding="utf-8"), height=780, scrolling=True)
else:
    st.info("The case-study animation file was not found. Upload animation/index.html to the repository.")

_vids = {}
for _d in (ROOT / "media", ROOT):
    if _d.is_dir():
        for _f in sorted(_d.glob("*.mp4")):
            _vids.setdefault(_f.stem, _f)
if _vids:
    st.header("More RMTI videos")
    _name = st.radio("Video", list(_vids), horizontal=True, label_visibility="collapsed",
                     format_func=lambda n: n.replace("rmti_", "").replace("_", " ").title())
    _vid = _vids[_name]
    if _vid.stat().st_size < 10_000:
        st.warning("This video file is only a few KB. It is probably a Git LFS pointer, not the real video. Upload the MP4 again without LFS.")
    _subs = next((str(c) for e in (".vtt", ".srt") for c in (_vid.with_suffix(e), ROOT / "media" / (_vid.stem + e)) if c.exists()), None)
    try:
        st.video(str(_vid), subtitles=_subs) if _subs else st.video(str(_vid))
    except TypeError:
        st.video(str(_vid))

st.header("Developer portal and API")
HTML = ROOT / "developer_portal.html"
if HTML.exists():
    FIX = """<script>document.addEventListener('click',function(e){var a=e.target.closest('a[href^="#"]');
if(a){e.preventDefault();location.hash=a.getAttribute('href');}});</script></body>"""
    components.html(HTML.read_text(encoding="utf-8").replace("</body>", FIX, 1), height=1100, scrolling=True)
else:
    st.info("developer_portal.html was not found next to Home.py.")

st.caption("Research prototype. Not validated; not a medical device; not for patient-care decisions. Synthetic examples. Apache-2.0.")
