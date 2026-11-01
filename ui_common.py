"""Shared helpers for the extra Streamlit pages: the same access gate and API-or-in-process call pattern as app.py.py."""
import hmac, os
import streamlit as st

API = os.environ.get("RMTI_API_URL")


def gate():
    """Same optional shared access codes as app.py.py (RMTI_ACCESS_CODES). session_state['ok'] is shared with the main page."""
    codes = [c for c in os.environ.get("RMTI_ACCESS_CODES", "").split(",") if c]
    if not codes or st.session_state.get("ok"):
        return
    st.title("Oncoclastics Platform")
    entered = st.text_input("Access code", type="password")
    if entered and any(hmac.compare_digest(entered, c) for c in codes):
        st.session_state["ok"] = True
        st.rerun()
    elif entered:
        st.error("Invalid code")
    st.stop()


def call(path, payload, local):
    """POST to the REST API if RMTI_API_URL is set (sending RMTI_API_KEY as X-API-Key when provided), else run the same engine in-process."""
    if API:
        import requests
        key = os.environ.get("RMTI_API_KEY")
        r = requests.post(f"{API}{path}", json=payload, headers={"X-API-Key": key} if key else {}, timeout=120)
        if r.status_code != 200:
            raise ValueError(r.json().get("detail", r.text))
        return r.json()
    return local()
