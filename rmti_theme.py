"""rmti_theme.py  --  shared look-and-feel for the app and pages: navy, white and red (CSS only; no data, no network).

Same interface as before: call apply() once near the top of a page, after st.set_page_config.
NAVY, RED and the other constants are exported so a page can reuse the exact colours in its own charts.
"""
import streamlit as st

NAVY, NAVY_MID, SLATE = "#0b2545", "#1d4e89", "#34506f"
RED, RED_DARK = "#d9262c", "#b81e24"
ICE, LINE = "#eef3fa", "#d6e2f2"
TIERS = ["#6cb4f5", "#1d6fd0", "#ff6b73", "#d9262c", "#8f1519"]       # tier 1 (low) to tier 5 (critical)

_CSS = """
<style>
html, body, [class*="css"] { font-family: "Inter", "Segoe UI", system-ui, -apple-system, Roboto, Helvetica, Arial, sans-serif; }
.block-container { padding-top: 2.2rem; max-width: 1400px; }
h1 { font-weight: 800; letter-spacing: -0.02em; color: #0b2545; }
h2, h3, h4 { letter-spacing: -0.01em; color: #0b2545; }
[data-testid="stCaptionContainer"], .stCaption { color: #34506f !important; opacity: 1 !important; font-size: 0.93rem; line-height: 1.5; }
label, [data-testid="stWidgetLabel"] p { color: #0b2545; font-weight: 600; }
div[data-testid="stMetric"] { background: #ffffff; border: 1px solid #d6e2f2; border-left: 4px solid #d9262c; border-radius: 12px; padding: 12px 16px; box-shadow: 0 2px 8px rgba(11,37,69,0.06); }
[data-testid="stMetricValue"] { color: #0b2545; font-weight: 800; }
[data-testid="stMetricLabel"] p { color: #34506f; font-weight: 600; }
.stTabs [data-baseweb="tab-list"] { gap: 6px; border-bottom: 1px solid #d6e2f2; }
.stTabs [data-baseweb="tab"] { font-weight: 600; border-radius: 8px 8px 0 0; padding: 8px 14px; color: #34506f; }
.stTabs [aria-selected="true"] { color: #d9262c; }
.stTabs [data-baseweb="tab-highlight"] { background-color: #d9262c; }
section[data-testid="stSidebar"] { border-right: 1px solid #d6e2f2; background: #eef3fa; }
div[data-testid="stExpander"] { border-radius: 12px; border: 1px solid #d6e2f2; }
.stButton > button, .stDownloadButton > button { border-radius: 8px; border: 1.5px solid #0b2545; color: #0b2545; font-weight: 600; }
.stButton > button:hover, .stDownloadButton > button:hover { border-color: #d9262c; color: #d9262c; }
.stButton > button[kind="primary"] { background: #d9262c; border-color: #d9262c; color: #ffffff; }
.stButton > button[kind="primary"]:hover { background: #b81e24; border-color: #b81e24; color: #ffffff; }
a { color: #1d4e89; }
a:hover { color: #d9262c; }
</style>
"""


def apply():
    st.markdown(_CSS, unsafe_allow_html=True)
    try:                                      # shared red / light-blue / white look, applied last so it wins
        import oncoclastic_style as _ui
        _ui.apply()
    except Exception:
        pass
