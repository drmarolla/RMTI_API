"""rmti_theme.py  --  light look-and-feel upgrade shared by the app and pages (CSS only; no data, no network)."""
import streamlit as st

_CSS = """
<style>
html, body, [class*="css"] { font-family: "Inter", "Segoe UI", system-ui, -apple-system, Roboto, Helvetica, Arial, sans-serif; }
.block-container { padding-top: 2.2rem; max-width: 1400px; }
h1 { font-weight: 800; letter-spacing: -0.02em; color: #0b3b40; }
h2, h3 { letter-spacing: -0.01em; color: #0b3b40; }
div[data-testid="stMetric"] { background: rgba(11,92,99,0.06); border: 1px solid rgba(11,92,99,0.18); border-radius: 12px; padding: 12px 16px; }
.stTabs [data-baseweb="tab-list"] { gap: 6px; }
.stTabs [data-baseweb="tab"] { font-weight: 600; border-radius: 8px 8px 0 0; padding: 8px 14px; }
section[data-testid="stSidebar"] { border-right: 1px solid rgba(11,92,99,0.15); }
div[data-testid="stExpander"] { border-radius: 12px; border: 1px solid rgba(11,92,99,0.18); }
</style>
"""


def apply():
    st.markdown(_CSS, unsafe_allow_html=True)
