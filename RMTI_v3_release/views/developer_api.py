"""Developer API portal: quickstart, live playground, reference, limits, access request."""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

import rmti_core as core
from rmti_ui import kpi, tier_badge

BASE_URL = os.getenv("RMTI_PUBLIC_API_URL") or os.getenv("RMTI_API_URL") or "https://YOUR-API-HOST"
DATA_DIR = Path(os.getenv("RMTI_DATA_DIR", "data"))
SAMPLE = {"L": 0.7, "E": 0.6, "V": 0.8, "rho": 0.35, "site": "liver", "label": "case-001"}


# ----------------------------------------------------------------------------- access request
def _save_request(rec: dict) -> bool:
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(DATA_DIR / "api_requests.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
        return True
    except OSError:
        return False


def access_form(key: str) -> None:
    with st.form(key, clear_on_submit=True, border=False):
        name = st.text_input("Full name and credentials", placeholder="Dr. Jane Doe, MD")
        org = st.text_input("Institution", placeholder="Memorial Oncology Center")
        email = st.text_input("Institutional email", placeholder="jane.doe@institution.org")
        tier = st.selectbox("Access level", ["research", "enterprise"],
                            format_func=lambda t: f"{t.title()} ({core.ACCESS_TIERS[t]['rpm']} req/min)")
        use = st.text_area("What will you build?", height=90,
                           help="Describe the workflow and expected volume. Do not include patient information.")
        if st.form_submit_button("Request API access", type="primary", width="stretch"):
            if not (name.strip() and org.strip() and re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email.strip())):
                st.error("Enter your name, institution and a valid email address.")
            elif _save_request({"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "name": name.strip(),
                                "org": org.strip(), "email": email.strip(), "tier": tier, "use": use.strip()}):
                st.success(f"Thanks, {name.split()[0] if name.split() else 'there'}. Your request is logged for review.")
            else:
                st.warning("We could not store your request on this server. Please email the team directly.")


@st.dialog("Request API access")
def request_access_dialog() -> None:
    st.caption("Keys are issued after a short review. Sandbox access is available immediately.")
    access_form("access_form_dialog")


# ----------------------------------------------------------------------------- call helpers
def _snippets(base: str, key: str) -> dict[str, str]:
    body = json.dumps({k: SAMPLE[k] for k in ("L", "E", "V", "rho", "site")})
    return {
        "curl": f"""curl -X POST {base}/v1/risk/score \\
  -H "X-API-Key: {key}" \\
  -H "Content-Type: application/json" \\
  -d '{body}'""",
        "Python": f"""from rmti_sdk import RMTIClient

client = RMTIClient("{base}", "{key}")
result = client.score(L=0.7, E=0.6, V=0.8, rho=0.35, site="liver")
print(result["risk"], result["tier"], result["priority_lever"])""",
        "JavaScript": f"""const res = await fetch("{base}/v1/risk/score", {{
  method: "POST",
  headers: {{ "X-API-Key": "{key}", "Content-Type": "application/json" }},
  body: JSON.stringify({body}),
}});
if (!res.ok) throw new Error((await res.json()).detail);
const result = await res.json();""",
    }


def _remote(path: str, payload: dict, key: str):
    r = requests.post(os.environ["RMTI_API_URL"].rstrip("/") + path, json=payload,
                      headers={"X-API-Key": key}, timeout=10)
    return r.status_code, r.json()


# ----------------------------------------------------------------------------- page
def render() -> None:
    with st.container(border=True, key="devhero"):
        left, right = st.columns([1.5, 1], gap="large", vertical_alignment="center")
        with left:
            st.markdown('<span class="pill">Developer API · v1</span>', unsafe_allow_html=True)
            st.markdown('<div class="hero-title" style="font-size:2.1rem">Put RMTI scoring inside your triage workflow.</div>',
                        unsafe_allow_html=True)
            st.markdown('<div class="hero-sub">One deterministic endpoint returns the risk score, tier, '
                        'per-lever elasticity and the intervention that lowers risk the most. '
                        'Output can be returned as a FHIR RiskAssessment.</div>', unsafe_allow_html=True)
        with right:
            st.code(_snippets(BASE_URL, core.SANDBOX_KEY)["curl"], language="bash")

    st.write("")
    k1, k2, k3, k4 = st.columns(4, gap="medium")
    k1.markdown(kpi("5", "Endpoints: score, batch, sensitivity, FHIR, usage", "red"), unsafe_allow_html=True)
    k2.markdown(kpi("3", "Access tiers: sandbox, research, enterprise", "blue"), unsafe_allow_html=True)
    k3.markdown(kpi("0", "Payloads logged or stored by the API", "navy"), unsafe_allow_html=True)
    k4.markdown(kpi("R4", "FHIR RiskAssessment export", "sky"), unsafe_allow_html=True)
    st.write("")
    st.markdown(f'<div class="note">{core.DISCLAIMER}</div>', unsafe_allow_html=True)
    st.write("")

    t_quick, t_play, t_ref, t_auth, t_access = st.tabs(
        ["Quickstart", "Live playground", "Reference", "Keys and limits", "Request access"])

    # ---- Quickstart
    with t_quick:
        st.subheader("Make your first call in a minute")
        c1, c2 = st.columns([1, 1], gap="large")
        with c1:
            st.markdown("**1. Use the sandbox key**\n\nIt is shared and rate limited, so it is for testing only.")
            st.code(core.SANDBOX_KEY)
            st.markdown("**2. Send the levers**\n\nEach lever is a number from 0 to 1.")
            lang = st.radio("Language", ["curl", "Python", "JavaScript"], horizontal=True, label_visibility="collapsed")
            st.code(_snippets(BASE_URL, core.SANDBOX_KEY)[lang], language={"curl": "bash", "Python": "python",
                                                                          "JavaScript": "javascript"}[lang])
        with c2:
            st.markdown("**3. Read the response**")
            st.json(core.score(**{k: SAMPLE[k] for k in ("L", "E", "V", "rho")}), expanded=2)
        st.caption("Run your own copy: `uvicorn api:app --port 8000`, then open `/docs` for the interactive OpenAPI page.")

    # ---- Playground
    with t_play:
        remote = bool(os.getenv("RMTI_API_URL"))
        mode = "Remote API" if remote else "Built-in engine"
        st.caption(f"Mode: **{mode}**" + ("" if remote else " (set RMTI_API_URL to call a deployed API instead)"))
        form, out = st.columns([1, 1.25], gap="large")
        with form:
            L = st.slider("L · Likelihood", 0.0, 1.0, 0.70, 0.01)
            E = st.slider("E · Exposure", 0.0, 1.0, 0.60, 0.01)
            V = st.slider("V · Vulnerability", 0.0, 1.0, 0.80, 0.01)
            rho = st.slider("ρ · Resilience", 0.0, 1.0, 0.35, 0.01)
            site = st.selectbox("Site", core.SITES)
            sweep_on = st.toggle("Also sweep one lever")
            lever = st.selectbox("Lever to sweep", list(core.LEVER_NAMES), format_func=core.LEVER_NAMES.get) if sweep_on else None
            key = st.text_input("API key", core.SANDBOX_KEY, type="password") if remote else core.SANDBOX_KEY
        payload = {"L": L, "E": E, "V": V, "rho": rho, "site": site}
        with out:
            try:
                if remote:
                    code, res = _remote("/v1/risk/score", payload, key)
                    if code != 200:
                        st.error(f"{res.get('code', 'error')}: {res.get('detail', 'request failed')}")
                        st.stop()
                else:
                    res = core.score(L, E, V, rho)
            except requests.RequestException as e:
                st.error(f"Could not reach the API: {e.__class__.__name__}")
                st.stop()
            m1, m2 = st.columns(2)
            m1.metric("Risk (R)", f"{res['risk']:.4f}")
            m2.markdown("Tier", help="Default screening bands, not clinically validated.")
            m2.markdown(tier_badge(res["tier"]), unsafe_allow_html=True)
            if res["priority_lever"]:
                top = res["what_if"][0]
                st.info(f"Biggest single lever: **{top['name']}** ({top['from']:.2f} → {top['to']:.2f}) "
                        f"cuts risk by {top['relative_reduction']:.0%}.")
            wi = pd.DataFrame(res["what_if"]).set_index("name")[["absolute_reduction"]]
            st.caption("Risk reduction from a 0.10 improvement in each lever")
            st.bar_chart(wi, color="#BE123C", height=200)
            if lever:
                pts = core.sweep(lever, {"L": L, "E": E, "V": V, "rho": rho}, 41)
                st.caption(f"Risk as {core.LEVER_NAMES[lever]} varies from 0 to 1")
                st.line_chart(pd.DataFrame(pts).set_index("value")[["risk"]], color="#2563EB", height=200)
        with st.expander("Request and response JSON"):
            a, b = st.columns(2)
            a.json(payload)
            b.json(res, expanded=1)

    # ---- Reference
    with t_ref:
        st.subheader("Endpoints")
        st.dataframe(pd.DataFrame([
            ("GET", "/health", "No", "Liveness check"),
            ("GET", "/v1/meta", "No", "Formula, tier bands, limits"),
            ("GET", "/v1/usage", "Yes", "Your tier and current usage"),
            ("POST", "/v1/risk/score", "Yes", "Score one case"),
            ("POST", "/v1/risk/score/fhir", "Yes", "Score and return a FHIR RiskAssessment"),
            ("POST", "/v1/risk/batch", "Yes", "Score many cases (tier-capped)"),
            ("POST", "/v1/risk/sensitivity", "Yes", "Sweep one lever from 0 to 1"),
        ], columns=["Method", "Path", "Key", "Purpose"]), hide_index=True, width="stretch")
        with st.expander("Request body for /v1/risk/score"):
            st.json(SAMPLE)
        with st.expander("Batch request"):
            st.json({"items": [SAMPLE, {**SAMPLE, "label": "case-002", "rho": 0.6}]})
        with st.expander("Error format and codes"):
            st.json({"status": 429, "code": "rate_limited", "title": "Rate limited",
                     "detail": "Limit of 20 requests/minute for tier 'sandbox' reached.", "request_id": "9f2c41ab07d3e5c1"})
            st.dataframe(pd.DataFrame([
                (401, "missing_api_key / invalid_api_key", "Send a valid X-API-Key header"),
                (413, "batch_too_large", "Split the batch to fit your tier"),
                (422, "validation_error", "Levers must be numbers between 0 and 1"),
                (429, "rate_limited", "Wait for Retry-After seconds"),
                (500, "internal_error", "Quote the request_id to support"),
            ], columns=["HTTP", "code", "What to do"]), hide_index=True, width="stretch")
        st.caption("Every response carries X-Request-ID. Send your own X-Request-ID and it is echoed back for tracing.")

    # ---- Keys and limits
    with t_auth:
        st.subheader("Access tiers")
        st.dataframe(pd.DataFrame([{"Tier": t, "Requests / min": v["rpm"], "Batch size": v["batch"],
                                    "For": v["description"]} for t, v in core.ACCESS_TIERS.items()]),
                     hide_index=True, width="stretch")
        st.markdown("""
**Authentication.** Send your key in the `X-API-Key` header over HTTPS. Never put keys in URLs or client-side code.

**Rate limits.** Each response includes `X-RateLimit-Limit`, `X-RateLimit-Remaining` and `X-RateLimit-Reset`.
On `429`, wait `Retry-After` seconds. The Python SDK does this automatically.

**Privacy.** The API does not log or store request bodies. Use `label` only for an opaque reference of your own.
Never send names, MRNs or other patient identifiers.
        """)

    # ---- Request access
    with t_access:
        c1, c2 = st.columns([1, 1], gap="large")
        with c1:
            st.subheader("Get a production key")
            access_form("access_form_tab")
        with c2:
            st.subheader("What happens next")
            st.markdown("1. We review your request.\n2. You receive a key scoped to your tier.\n"
                        "3. Start with `/v1/usage` to confirm your limits.\n\n"
                        "Research prototype: keys do not imply clinical validation.")
