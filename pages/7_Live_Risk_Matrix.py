"""Live Risk Matrix page: runs the script 7_Live_Risk_Matrix.py that sits in the repository root, unchanged."""
import runpy
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "7_Live_Risk_Matrix.py"
if TARGET.exists():
    runpy.run_path(str(TARGET), run_name="__main__")
else:
    st.error("7_Live_Risk_Matrix.py was not found in the repository root.")
