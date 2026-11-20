"""Developer Portal: a live "Try it out" sandbox, the written reference and the OpenAPI spec. Research prototype, synthetic values only."""
import json
import os
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

try:
    st.set_page_config(page_title="RMTI Developer Portal", layout="wide")
except Exception:          # already set by the router
    pass

ROOT = Path(__file__).resolve().parent.parent
import sys  # noqa: E402
sys.path.insert(0, str(ROOT))
import ui_api as A  # noqa: E402

st.title("Developer Portal")
st.markdown("One bounded equation, **R = L · E · V · (1 − ρ)**, behind a small JSON API. Change the levers below and watch the request, "
            "the code and the response update. Use **Request API access** (top right) to ask for a key.")

tab_try, tab_ref, tab_spec = st.tabs(["Try it out", "Reference", "OpenAPI spec"])

# ------------------------------------------------------------------------------------------------ Try it out
with tab_try:
    left, right = st.columns([5, 7], gap="large")
    with left:
        st.markdown("##### Request: `POST /v1/snapshot`")
        label = st.selectbox("Domain", list(A.DOMAINS), key="try_domain")
        domain, site = A.DOMAINS[label]
        L = st.slider("L: likelihood", 0.0, 1.0, 0.30, 0.01, key="try_L")
        E = st.slider("E: exposure", 0.0, 1.0, 0.65, 0.01, key="try_E")
        V = st.slider("V: vulnerability", 0.0, 1.0, 0.55, 0.01, key="try_V")
        rho = st.slider("ρ now: resilience", 0.0, 0.95, 0.20, 0.01, key="try_rho")
        use_after = st.checkbox("Compare with an improved ρ (rho_after)", value=True, key="try_after")
        rho2 = st.slider("ρ after", 0.0, 0.95, 0.50, 0.01, key="try_rho2", disabled=not use_after)
        c1, c2 = st.columns(2)
        N = c1.number_input("N: population", min_value=1, value=100_000, step=1000, key="try_N")
        C = c2.number_input("C: confidence 1 to 5", min_value=1, max_value=5, value=5, step=1, key="try_C")
        bad = st.checkbox("Send invalid input (L = 1.4) to see validation", key="try_bad")
        st.caption("Allowed: 0 ≤ L, E, V ≤ 1 and 0 ≤ ρ < 1. Anything else returns HTTP 422 with the field that failed.")

    payload = A.build_payload(domain, site, int(N), L, E, V, rho, rho2 if use_after else None, int(C))
    if bad:
        payload["L"] = 1.4
    status, body = A.run_snapshot(payload)

    with right:
        t_req, t_curl, t_py, t_js, t_resp = st.tabs(["JSON payload", "cURL", "Python", "JavaScript", "Response"])
        t_req.code(A.pretty(payload), language="json")
        t_curl.code(A.curl_snippet(payload), language="bash")
        t_py.code(A.python_snippet(payload), language="python")
        t_js.code(A.js_snippet(payload), language="javascript")
        with t_resp:
            ok = status == 200
            st.markdown(f"<span class='rm-tc' style='background:{'#1d6fd0' if ok else '#d9262c'};color:#fff'>HTTP {status} · {'OK' if ok else 'Validation error' if status == 422 else 'Error'}</span>",
                        unsafe_allow_html=True)
            st.code(A.pretty(body), language="json")
        if A.base_url() == A.PLACEHOLDER_BASE:
            st.caption("The base URL is a placeholder: replace `YOUR-API-HOST` with your deployment. The response above comes from the same scoring engine "
                       "running inside this app; it is not a call to a remote server and it does not use a key.")
        else:
            st.caption(f"Snippets point at `{A.base_url()}`. The response above is computed in this app with the same engine, with no key sent.")
        st.caption("Header name is `X-API-Key` (not Bearer). Research prototype: synthetic or published aggregate values only.")

# ------------------------------------------------------------------------------------------------ Reference
with tab_ref:
    HTML = ROOT / "developer_portal.html"
    if not HTML.exists():
        st.info("developer_portal.html was not found in the repository root.")
    else:
        FIX = """<script>document.addEventListener('click',function(e){var a=e.target.closest('a[href^="#"]');
if(a){e.preventDefault();location.hash=a.getAttribute('href');}});</script></body>"""
        PORTAL = ":root,:root:not([data-theme=light]){--surface:#eaf4ff!important;--line:#b9d9f7!important;--muted:#1e3a5f!important;--ink:#0b2545!important;--code:#0b2545!important;--accent:#1d6fd0!important;--bg:#fff!important}.m{background:#d9262c!important}.m.get{background:#1d6fd0!important}.copy{background:#1d6fd0!important;color:#fff!important}"
        page = HTML.read_text(encoding="utf-8").replace("</head>", "<style>" + PORTAL + "</style></head>", 1).replace("</body>", FIX, 1)
        components.html(page, height=1100, scrolling=True)


# ------------------------------------------------------------------------------------------------ OpenAPI
@st.cache_data(show_spinner=False)
def load_spec():
    """Prefer the live schema generated from the FastAPI app (always matches the code); fall back to docs/openapi.json."""
    try:
        import api
        return api.app.openapi(), "generated from api.py"
    except Exception as e:  # noqa: BLE001
        f = ROOT / "docs" / "openapi.json"
        if f.exists():
            return json.loads(f.read_text(encoding="utf-8")), f"read from docs/openapi.json (live generation unavailable: {type(e).__name__})"
        return None, f"{type(e).__name__}: {e}"


with tab_spec:
    spec, src = load_spec()
    if spec is None:
        st.info("The OpenAPI document could not be built here. Run `python tools/export_openapi.py` where the API dependencies are installed, "
                "or open `/docs` on the deployed API.")
        st.caption(src)
    else:
        st.caption(f"OpenAPI {spec.get('openapi', '3.x')} · {spec.get('info', {}).get('title', '')} v{spec.get('info', {}).get('version', '')} · {src}")
        rows = []
        for path, ops in spec.get("paths", {}).items():
            for m, op in ops.items():
                if isinstance(op, dict):
                    rows.append({"Method": m.upper(), "Path": path, "Summary": op.get("summary", ""), "Tag": ", ".join(op.get("tags", []))})
        st.dataframe(rows, use_container_width=True, hide_index=True)
        schemas = spec.get("components", {}).get("schemas", {})
        names = sorted(n for n in schemas if n not in ("HTTPValidationError", "ValidationError"))
        if names:
            pick = st.selectbox("Request schema", names, index=names.index("SnapshotIn") if "SnapshotIn" in names else 0, key="spec_pick")
            st.json(schemas[pick], expanded=2)
        d1, d2 = st.columns(2)
        d1.download_button("Download openapi.json", json.dumps(spec, indent=2), "rmti_openapi.json", "application/json", use_container_width=True)
        base = os.environ.get("RMTI_API_URL", "").rstrip("/")
        if base:
            d2.link_button("Open Swagger UI (/docs)", base + "/docs", use_container_width=True)
        else:
            d2.caption("Swagger UI (`/docs`) and `/openapi.json` are served by the FastAPI service (`uvicorn api:app`). Set `RMTI_API_URL` to show a link here.")
