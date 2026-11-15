"""Home page entry inside the menu: runs the real home page, Home.py in the repository root, unchanged.
Works whichever file is set as the Main file path, so https://oncoclastics.streamlit.app/Home always shows it."""
import runpy
from pathlib import Path

import streamlit as st

TARGET = Path(__file__).resolve().parent.parent / "Home.py"
if TARGET.exists():
    runpy.run_path(str(TARGET), run_name="__main__")
else:
    st.error("Home.py was not found in the repository root.")
