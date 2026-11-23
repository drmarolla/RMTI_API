"""Developer API portal. Shows HTTP requests and JSON only; no source code is displayed."""
import json
import os
import re
import time
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

from engine import DISCLAIMER
from rmti_ui import badge, disclaimer, kpi

BASE = os.getenv("RMTI_PUBLIC_API_URL") or os.getenv("RMTI_API_URL") or "https://YOUR-API-HOST"
DATA = Path(os.getenv("RMTI_DATA_DIR", "data"))
SANDBOX_KEY = "rmti_sandbox_demo"
TIERS = {"sandbox": (20, 25, "Public demo key. Shared, low limits."), "research": (120, 250, "Academic and research use."),
         "enterprise": (600, 1000, "Hospital systems and integrators.")}
SAMPLE = {"L": 0.8, "E": 0.85, "V": 0.75, "rho_now": 0.20, "rho_after": 0.58, "C": 4, "N": 4500000, "domain": "general"}


def _save(rec):
    try:
        DATA.mkdir(parents=True, exist_ok=True)
        with open(DATA / "api_requests.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
        return True
    except OSError:
        return False


def access_form(key):
    with st.form(key, clear_on_submit=True, border=False):
        name = st.text_input("Full name and credentials")
        org = st.text_input("Institution")
        email = st.text_input("Institutional email")
        tier = st.selectbox("Access level", ["research", "enterprise"])
        use = st.text_area("What will you build? (no patient information)", height=90)
        if st.form_submit_button("Request API access", type="primary", width="stretch"):
            if not (name.strip() and org.strip() and re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email.strip())):
                st.error("Enter your name, institution and a valid email address.")
            elif _save({"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "name": name.strip(), "org": org.strip(),
                        "email": email.strip(), "tier": tier, "use": use.strip()}):
                st.success("Thanks. Your request is logged for review.")
            else:
                st.warning("We could not store your request on this server. Please email the team directly.")


@st.dialog("Request API access")
def request_access_dialog():
    st.caption("Keys are issued after a short review. The sandbox key works immediately.")
    access_form("access_form_dialog")


def render():
    with st.container(border=True, key="devhero"):
        a, b = st.columns([1.4, 1], gap="large", vertical_alignment="center")
        with a:
            st.markdown('<span class="pill">Developer API · v2</span>', unsafe_allow_html=True)
            st.markdown('<div class="hero-title" style="font-size:2.8rem">Put RMTI scoring inside your workflow.</div>', unsafe_allow_html=True)
            st.markdown('<div class="hero-sub">One endpoint returns the residual score, tier, posture, EAL, equity rate and before-and-after '
                        'effect of an investment or treatment. The engine runs on our servers and its source is never exposed.</div>', unsafe_allow_html=True)
        with b:
            st.code(f'curl -X POST {BASE}/v1/risk/score \\\n  -H "X-API-Key: {SANDBOX_KEY}" \\\n  -H "Content-Type: application/json" \\\n  -d \'{json.dumps(SAMPLE)}\'', language="bash")
    st.write("")
    k = st.columns(4, gap="medium")
    k[0].markdown(kpi("4", "Scoring endpoints plus usage and metadata", "red"), unsafe_allow_html=True)
    k[1].markdown(kpi("3", "Access tiers: sandbox, research, enterprise", "blue"), unsafe_allow_html=True)
    k[2].markdown(kpi("0", "Request bodies logged or stored", "navy"), unsafe_allow_html=True)
    k[3].markdown(kpi("R4", "FHIR-shaped RiskAssessment output", "sky"), unsafe_allow_html=True)
    st.write("")
    t1, t2, t3, t4, t5 = st.tabs(["Quickstart", "Live playground", "Reference", "Keys and limits", "Request access"])
    with t1:
        c1, c2 = st.columns(2, gap="large")
        with c1:
            st.markdown("**1. Use the sandbox key**")
            st.code(SANDBOX_KEY)
            st.markdown("**2. Send the levers.** Every lever is a number from 0 to 1. ρ must be below 1.")
            st.json(SAMPLE)
        with c2:
            st.markdown("**3. Read the response**")
            from api import ScoreRequest, _score
            st.json(_score(ScoreRequest(**SAMPLE)), expanded=1)
    with t2:
        remote = bool(os.getenv("RMTI_API_URL"))
        st.caption("Mode: " + ("**Remote API**" if remote else "**Built-in engine** (set RMTI_API_URL to call a deployed API)"))
        f, o = st.columns([1, 1.3], gap="large")
        with f:
            L = st.slider("L", 0.0, 1.0, 0.80, 0.01, key="dL")
            E = st.slider("E", 0.0, 1.0, 0.85, 0.01, key="dE")
            V = st.slider("V", 0.0, 1.0, 0.75, 0.01, key="dV")
            r0 = st.slider("ρ now", 0.0, 0.99, 0.20, 0.01, key="dR0")
            r1 = st.slider("ρ after", 0.0, 0.99, 0.58, 0.01, key="dR1")
            C = st.select_slider("C", [1, 2, 3, 4, 5], 4, key="dC")
            dom = st.radio("Domain", ["general", "hcc"], horizontal=True)
        body = {"L": L, "E": E, "V": V, "rho_now": r0, "rho_after": r1, "C": C, "N": 100000, "domain": dom}
        with o:
            try:
                if remote:
                    r = requests.post(os.environ["RMTI_API_URL"].rstrip("/") + "/v1/risk/score", json=body, headers={"X-API-Key": SANDBOX_KEY}, timeout=10)
                    res = r.json()
                    if r.status_code != 200:
                        st.error(res.get("detail", "request failed"))
                        st.stop()
                else:
                    from api import ScoreRequest, _score
                    res = _score(ScoreRequest(**body))
            except requests.RequestException:
                st.error("Could not reach the API.")
                st.stop()
            m = st.columns(3)
            m[0].metric("R now", f"{res['R_now']:.3f}")
            m[1].metric("R after", f"{res['R_after']:.3f}")
            m[2].metric("Reduction", f"{res['risk_reduction_pct']:.1f}%")
            st.markdown(f"{badge(res['tier_now'])} → {badge(res['tier_after'])}", unsafe_allow_html=True)
        with st.expander("Request and response JSON"):
            x, y = st.columns(2)
            x.json(body)
            y.json(res, expanded=1)
    with t3:
        st.dataframe(pd.DataFrame([("GET", "/health", "No", "Liveness"), ("GET", "/v1/meta", "No", "Formula, tiers, consequence scale"),
                                   ("GET", "/v1/usage", "Yes", "Your tier and usage"), ("POST", "/v1/risk/score", "Yes", "Score one case, with optional after-state"),
                                   ("POST", "/v1/risk/score/fhir", "Yes", "Same, as a FHIR RiskAssessment"),
                                   ("POST", "/v1/risk/batch", "Yes", "Rank many cases by tier, then EAL"),
                                   ("POST", "/v1/risk/sensitivity", "Yes", "One-way ± sensitivity with tier-flip detection")],
                                  columns=["Method", "Path", "Key", "Purpose"]), hide_index=True, width="stretch")
        with st.expander("Error format"):
            st.json({"status": 422, "code": "validation_error", "title": "Validation error", "detail": "rho_now: Input should be less than 1", "request_id": "9f2c41ab07d3e5c1"})
        st.caption("Interactive OpenAPI documentation is served by the API itself at /docs.")
    with t4:
        st.dataframe(pd.DataFrame([{"Tier": t, "Requests / min": v[0], "Batch size": v[1], "For": v[2]} for t, v in TIERS.items()]), hide_index=True, width="stretch")
        st.markdown("Send your key in the `X-API-Key` header over HTTPS and never in a URL or in browser code. Every response carries `X-RateLimit-Remaining`; on `429`, wait `Retry-After` seconds. "
                    "The API never logs or stores request bodies. Use `label` only for an opaque reference of your own, and never send names or identifiers.")
    with t5:
        c1, c2 = st.columns(2, gap="large")
        with c1:
            access_form("access_form_tab")
        with c2:
            st.markdown("1. We review your request.\n2. You receive a key scoped to your tier.\n3. Confirm your limits with `/v1/usage`.")
    disclaimer()
