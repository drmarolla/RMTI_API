"""Streamlit page: RMTI tumor-events-to-trajectory animation (liver, lung, breast).

Place this file in your Streamlit app's pages/ folder (or import its body into
an existing page). It embeds the GitHub Pages copy of animation/index.html and
falls back to the local copy in the repository.
"""
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="RMTI animation", layout="wide")
st.title("RMTI: from tumor events to trajectory")

LIVE = "https://drmarolla.github.io/RMTI-time-indexed/animation/"
LOCAL = Path(__file__).resolve().parent.parent / "animation" / "index.html"

source = st.radio("Source", ["Live (GitHub Pages)", "Local file"], horizontal=True)

if source.startswith("Live"):
    components.iframe(LIVE, height=900, scrolling=True)
elif LOCAL.exists():
    components.html(LOCAL.read_text(encoding="utf-8"), height=900, scrolling=True)
else:
    st.warning(f"Local file not found: {LOCAL}. Adjust LOCAL to your repository layout.")

st.caption(
    "Research prototype. Illustrative mapping of published figures onto RMTI; "
    "uncalibrated, not validated, not a medical device."
)
