"""
demo_mode.py  --  one switch for the public sandbox.

DEMO is ON by default (public deployment). Set RMTI_DEMO_MODE=0 (environment variable or a top-level Streamlit
secret) ONLY on a private, approved instance. In demo mode the pages show a banner and hide CSV upload, so the
public site can only ever be fed synthetic data or the published/aggregate case studies in rmti_cases.py.
"""
import os
import streamlit as st

DEMO = os.environ.get("RMTI_DEMO_MODE", "1").strip() != "0"

_DEMO_HTML = (
    '<div style="border:2px solid #b45309;background:#fff7ed;color:#7c2d12;padding:10px 16px;border-radius:8px;'
    'margin:4px 0 12px 0;font-size:0.95rem;line-height:1.45">'
    '<b>DEMO MODE</b> · public sandbox. Synthetic, illustrative or published aggregate values only. '
    '<b>Do not enter patient data</b> or any identifying information. Not validated · not a medical device · '
    'not for patient-care or emergency decisions.</div>'
)
_PRIVATE_HTML = (
    '<div style="border:2px solid #1e40af;background:#eff6ff;color:#1e3a8a;padding:10px 16px;border-radius:8px;'
    'margin:4px 0 12px 0;font-size:0.95rem">'
    '<b>PRIVATE MODE</b> · approved instance only. Pseudonymous, ethics-approved data only. '
    'Research prototype, not for patient-care decisions.</div>'
)


def banner():
    st.markdown(_DEMO_HTML if DEMO else _PRIVATE_HTML, unsafe_allow_html=True)
