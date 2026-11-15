"""RMTI home page: opens on the developer portal (developer_portal.html), with links to the tools.
Set this file as the Main file path in Streamlit Cloud settings."""
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="RMTI Developer", page_icon="🧬", layout="wide", initial_sidebar_state="collapsed")

HTML = Path(__file__).resolve().parent / "developer_portal.html"
if not HTML.exists():
    st.error("developer_portal.html was not found next to Home.py. Upload it to the repository root.")
    st.stop()

st.markdown("""<style>
.block-container{padding:2.6rem 0 0 0 !important;max-width:100% !important}
footer{display:none}
.tools{display:flex;flex-wrap:wrap;gap:.5rem;padding:.4rem 1.25rem .8rem;font-family:"Source Sans 3",sans-serif}
.tools b{margin-right:.4rem;align-self:center}
.tools a{padding:.35rem .9rem;border:1px solid #9aa5b5;border-radius:999px;text-decoration:none;color:inherit;font-size:.92rem}
.tools a:hover{background:#3d5a8a;color:#f4f6fa;border-color:#3d5a8a}
</style>
<div class="tools"><b>Open a tool:</b>
<a href="/Risk_Calculator" target="_self">Risk Calculator</a>
<a href="/HCC_Calculator" target="_self">HCC Calculator</a>
<a href="/Cohort_Sandbox" target="_self">Cohort Sandbox</a>
<a href="/4D_Risk_Matrix" target="_self">4D Risk Matrix</a>
<a href="/RMTI_Step_by_Step" target="_self">Step by Step</a>
<a href="/Case_Studies_and_Videos" target="_self">Case Studies</a></div>""", unsafe_allow_html=True)

# Peer-reviewed case-study animation (animation/index.html): liver, lung and breast studies scored with RMTI.
ROOT = Path(__file__).resolve().parent
_anim = ROOT / "animation" / "index.html"
if _anim.exists():
    _al, _am, _ar = st.columns([1, 5, 1])
    with _am:
        st.markdown("#### From tumor events to trajectory: three peer-reviewed case studies")
        st.caption("Liver (Lau-Min 2025), lung (Sabakhtarishvili 2025) and breast (O\u2019Shaughnessy 2026) cohorts, followed from Stage 1 to Stage 4 and scored with RMTI. "
                   "Use the buttons under the player to switch organ and pace. Research prototype; mappings are illustrative.")
        components.html(_anim.read_text(encoding="utf-8"), height=780, scrolling=True)

# Case-study videos: any .mp4 in media/ or in the repo root. A same-named .vtt/.srt (next to it or in media/) adds captions.
ROOT = Path(__file__).resolve().parent
_vids = {}
for _d in (ROOT / "media", ROOT):
    if _d.is_dir():
        for _f in sorted(_d.glob("*.mp4")):
            _vids.setdefault(_f.stem, _f)
try:
    _debug = "debug" in st.query_params          # open the site with ?debug=1 to list what was found
except Exception:
    _debug = False
if _debug:
    st.write({"app folder": str(ROOT), "videos found": {k: [str(v), v.stat().st_size] for k, v in _vids.items()}})
if _vids:
    _l, _m, _r = st.columns([1, 2, 1])
    with _m:
        st.markdown("#### See RMTI in action")
        st.caption("Tumor events, data assessment, formula analytics and trajectory, with published case studies. Research prototype; mappings are illustrative.")
        _name = st.radio("Case video", list(_vids), horizontal=True, label_visibility="collapsed",
                         format_func=lambda n: n.replace("rmti_", "").replace("_", " ").title())
        _vid = _vids[_name]
        if _vid.stat().st_size < 10_000:
            st.warning("This video file is only a few KB. It is probably a Git LFS pointer, not the real video. Upload the MP4 again without LFS.")
        _subs = next((str(c) for e in (".vtt", ".srt") for c in (_vid.with_suffix(e), ROOT / "media" / (_vid.stem + e)) if c.exists()), None)
        try:
            st.video(str(_vid), subtitles=_subs) if _subs else st.video(str(_vid))
        except TypeError:
            st.video(str(_vid))

# Links such as #ep-trajectory must stay inside the embedded page, so route them through location.hash.
FIX = """<script>document.addEventListener('click',function(e){var a=e.target.closest('a[href^="#"]');
if(a){e.preventDefault();location.hash=a.getAttribute('href');}});</script></body>"""
components.html(HTML.read_text(encoding="utf-8").replace("</body>", FIX, 1), height=1100, scrolling=True)
