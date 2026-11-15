"""Stub: the real home page is Home.py in the repository root (the Main file path). This sends visitors there."""
import streamlit as st

try:
    st.switch_page("Home.py")
except Exception:
    st.markdown("[Go to the home page](/)")
