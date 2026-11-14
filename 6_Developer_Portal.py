"""API documentation page: the endpoint reference on its own (the 3D models and tool cards are on the home page).
Needs developer_portal.html and rmti_theme.py in the repository root."""
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="RMTI API documentation", page_icon="🧬", layout="wide")
try:
    import rmti_theme
    rmti_theme.apply()                      # white, light blue and red look + slim top menu
except Exception:
    pass

SRC = Path(__file__).resolve().parent.parent / "developer_portal.html"
if not SRC.exists():
    st.error("developer_portal.html was not found in the repository root. Upload it next to the home page file.")
    st.stop()

st.title("API documentation")
st.caption("Scoring and validation endpoints plus the evidence registry. JSON in, JSON out. "
           "[Request API access](https://orcid.org/0000-0001-8498-7380)")

# Hide the portal's own header, 3D hero and footer so only the documentation shows.
CSS = "header.top,.stage,footer,.notice{display:none!important}aside{top:8px!important}html{scroll-padding-top:8px!important}body{background:#fff}"
# Links such as #ep-trajectory must stay inside the embedded page, so route them through location.hash.
FIX = """<script>document.addEventListener('click',function(e){var a=e.target.closest('a[href^="#"]');
if(a){e.preventDefault();location.hash=a.getAttribute('href');}});</script></body>"""
html = SRC.read_text(encoding="utf-8").replace("</head>", "<style>" + CSS + "</style></head>", 1).replace("</body>", FIX, 1)
components.html(html, height=1100, scrolling=True)

st.caption("Oncoclastics Platform on RMTI engine v2.4.0. Apache-2.0. Research use only. Research prototype, not a medical device.")
