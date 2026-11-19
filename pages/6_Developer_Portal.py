"""Developer Portal page: shows the new RMTI developer portal (developer_portal.html, repo root) inside Streamlit."""
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

try:
    st.set_page_config(page_title="RMTI Developer Portal", layout="wide")
except Exception:          # already set by the main app
    pass

HTML = Path(__file__).resolve().parent.parent / "developer_portal.html"
if not HTML.exists():
    st.error("developer_portal.html was not found in the repository root. Upload it next to app.py.")
    st.stop()

# Links such as #ep-trajectory must stay inside the embedded page, so route them through location.hash.
FIX = """<script>document.addEventListener('click',function(e){var a=e.target.closest('a[href^="#"]');
if(a){e.preventDefault();location.hash=a.getAttribute('href');}});</script></body>"""
PORTAL = ":root,:root:not([data-theme=light]){--surface:#eaf4ff!important;--line:#b9d9f7!important;--muted:#1e3a5f!important;--ink:#0b2545!important;--code:#0b2545!important;--accent:#1d6fd0!important;--bg:#fff!important}.m{background:#d9262c!important}.m.get{background:#1d6fd0!important}.copy{background:#1d6fd0!important;color:#fff!important}"
html = HTML.read_text(encoding="utf-8").replace("</head>", "<style>" + PORTAL + "</style></head>", 1).replace("</body>", FIX, 1)
components.html(html, height=1100, scrolling=True)
