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

# Links such as #ep-trajectory must stay inside the embedded page, so route them through location.hash.
FIX = """<script>document.addEventListener('click',function(e){var a=e.target.closest('a[href^="#"]');
if(a){e.preventDefault();location.hash=a.getAttribute('href');}});</script></body>"""
components.html(HTML.read_text(encoding="utf-8").replace("</body>", FIX, 1), height=1100, scrolling=True)
