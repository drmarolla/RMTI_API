"""RMTI home page: opens on the developer portal, with tool links and the explainer video.
Set this file as the Main file path in Streamlit Cloud settings."""
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="RMTI Developer", page_icon="🧬", layout="wide", initial_sidebar_state="collapsed")
ROOT = Path(__file__).resolve().parent
HTML = ROOT / "developer_portal.html"
if not HTML.exists():
    st.error("developer_portal.html was not found next to Home.py. Upload it to the repository root.")
    st.stop()

st.markdown("""<style>
.block-container{padding:2.6rem 0 0 0 !important;max-width:100% !important}footer{display:none}
.tools{display:flex;flex-wrap:wrap;gap:.6rem;padding:.5rem 1.25rem .9rem;font-family:"Source Sans 3",sans-serif;align-items:center}
.tools b{margin-right:.3rem;color:#14163a}
.tools a{padding:.5rem 1.1rem;border-radius:8px;text-decoration:none;font-weight:600;background:#f4f3fd;color:#3b2fc9;border:1px solid #dcdcf0}
.tools a:first-of-type{background:#d9262c;color:#fff;border-color:#d9262c}
.tools a:hover{background:#3b2fc9;color:#fff;border-color:#3b2fc9}
</style>
<div class="tools"><b>Open a tool:</b>
<a href="/Risk_Calculator" target="_self">Risk Calculator</a>
<a href="/HCC_Calculator" target="_self">HCC Calculator</a>
<a href="/Cohort_Sandbox" target="_self">Cohort Sandbox</a>
<a href="/4D_Risk_Matrix" target="_self">4D Risk Matrix</a>
<a href="/RMTI_Step_by_Step" target="_self">Step by Step</a>
<a href="/Case_Studies_and_Videos" target="_self">Case Studies</a></div>""", unsafe_allow_html=True)

VIDEO = ROOT / "rmti_1_explained.mp4"
if VIDEO.exists():
    with st.expander("▶ Watch: RMTI explained"):
        st.video(str(VIDEO))

FIX = """<script>document.addEventListener('click',function(e){var a=e.target.closest('a[href^="#"]');
if(a){e.preventDefault();location.hash=a.getAttribute('href');}});</script></body>"""
components.html(HTML.read_text(encoding="utf-8").replace("</body>", FIX, 1), height=1100, scrolling=True)
