# Copyright 2026 Cesar Marolla. Licensed under the Apache License, Version 2.0.
"""Shared look for the Oncoclastics / RMTI site: soft red, light blue and white, readable type.

Use in a page, after st.set_page_config:
    import oncoclastic_style as ui
    ui.apply()                    # every page after the first: adds the RMTI logo at the bottom
    ui.apply(first_page=True)     # the home page: no bottom logo
To use your own logo, put an SVG (with xmlns) at assets/rmti_logo.svg.
"""
import base64
from pathlib import Path

import streamlit as st

_ROOT = Path(__file__).resolve().parent
_DEFAULT_LOGO = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 250 64">'
    '<rect x="6" y="38" width="9" height="18" rx="1.5" fill="#5b9bd5"/>'
    '<rect x="19" y="26" width="9" height="30" rx="1.5" fill="#c9505a"/>'
    '<rect x="32" y="34" width="9" height="22" rx="1.5" fill="#5b9bd5"/>'
    '<circle cx="23.5" cy="15" r="4.5" fill="#c9505a"/>'
    '<text x="54" y="37" font-family="Arial,Helvetica,sans-serif" font-size="27" fill="#26364a">RMTI</text>'
    '<text x="55" y="54" font-family="Arial,Helvetica,sans-serif" font-size="10" letter-spacing="3" fill="#5d6d80">ONCOCLASTICS</text>'
    '</svg>')

_CSS = """
.stApp,[data-testid="stAppViewContainer"]{background:#ffffff;color:#26364a}
html,body,.stApp{font-size:17px;line-height:1.65}
h1,h2,h3,h4{color:#26364a;font-weight:600;letter-spacing:-.01em}
h1{font-size:2.05rem}h2{font-size:1.5rem;margin-top:1.6rem}h3{font-size:1.2rem}
p,li{color:#2f4157}
a{color:#3b78b4}
.block-container,[data-testid="stMainBlockContainer"]{max-width:1080px;padding-top:2.2rem}
[data-testid="stSidebar"]{background:#eef5fb;border-right:1px solid #d9e4ef}
[data-testid="stSidebarNav"]{padding-top:.4rem}
[data-testid="stSidebarNav"] ul{padding:0;margin:0;gap:0}
[data-testid="stSidebarNav"] li{margin:0}
[data-testid="stSidebarNavLink"]{padding:.28rem .7rem;margin:1px 0;min-height:0;border-radius:6px;font-size:.95rem}
[data-testid="stSidebarNavLink"] span{line-height:1.25}
[data-testid="stSidebarNavLink"][aria-current="page"]{background:#d6e6f4;font-weight:600}
.stButton>button,.stDownloadButton>button{background:#c9505a;color:#fff;border:0;border-radius:8px;padding:.45rem 1.1rem}
.stButton>button:hover,.stDownloadButton>button:hover{background:#a93f48;color:#fff}
[data-testid="stExpander"]{border:1px solid #d9e4ef;border-radius:10px;background:#fff}
[data-testid="stExpander"] summary{font-weight:600;color:#26364a}
table{border-collapse:collapse;width:100%;font-size:.93rem}
th{background:#eaf3fb;color:#26364a;text-align:left}
th,td{border:1px solid #d9e4ef;padding:.5rem .65rem;vertical-align:top}
.rm-card{background:#eef5fb;border:1px solid #d9e4ef;border-radius:12px;padding:1.1rem 1.3rem;margin:.6rem 0}
.rm-note{background:#fdf1f2;border-left:4px solid #c9505a;border-radius:6px;padding:.7rem 1rem;color:#4a3338;font-size:.95rem}
.rm-kicker{color:#c9505a;font-weight:700;letter-spacing:.12em;font-size:.8rem;text-transform:uppercase}
.rm-tools{display:flex;flex-wrap:wrap;gap:.45rem;margin:.3rem 0 1rem}
.rm-tools a{padding:.3rem .85rem;border:1px solid #c5d6e6;border-radius:999px;text-decoration:none;color:#26364a;font-size:.92rem;background:#fff}
.rm-tools a:hover{background:#d6e6f4;border-color:#9fbbd6}
footer{visibility:hidden}
"""


def logo_svg() -> str:
    custom = _ROOT / "assets" / "rmti_logo.svg"
    return custom.read_text(encoding="utf-8") if custom.exists() else _DEFAULT_LOGO


def apply(first_page: bool = False) -> None:
    css = _CSS
    if not first_page:
        b64 = base64.b64encode(logo_svg().encode("utf-8")).decode("ascii")
        css += ('.block-container::after,[data-testid="stMainBlockContainer"]::after{content:"";display:block;'
                'height:58px;margin:3rem auto 0;background:url(data:image/svg+xml;base64,' + b64 +
                ') center/contain no-repeat}')
    st.markdown("<style>" + css + "</style>", unsafe_allow_html=True)
