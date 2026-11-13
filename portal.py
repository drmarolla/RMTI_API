"""
portal.py  --  developer portal, themed API reference and embeddable widget for the RMTI API.

Mounts, WITHOUT changing any scoring route:
    GET /          developer portal (overview, quickstart, endpoints, levers, widget docs, safety)
    GET /docs      Swagger UI with the RMTI theme (Authorize button for X-API-Key)
    GET /widget    embeddable 3D/4D RMTI viewer (pure client-side; nothing is sent or stored)
These pages carry no data, so they are public even when RMTI_API_KEYS is set. Every /v1 route still needs the key.
Research prototype. Not validated, not a medical device.
"""
import html, json, os
from fastapi import Response
from fastapi.responses import HTMLResponse
from fastapi.security import APIKeyHeader
from fastapi.openapi.docs import get_swagger_ui_html

TITLE = "Risk Mechanism Theory Index (RMTI) API"
BYLINE = "Core Logic Created and Formulated by Dr. Cesar Marolla"
TAGLINE = "Quantifying Systemic Risk in Disaster Science and Oncology"
APP_URL = os.environ.get("RMTI_APP_URL", "https://oncoclastics.streamlit.app")
PUBLIC_PATHS = {"/", "/health", "/docs", "/redoc", "/openapi.json", "/widget", "/favicon.ico"}
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False,
                              description="Your API key. Not needed for /health, /docs, /redoc or /widget.")


def is_public(path):
    return path in PUBLIC_PATHS or path.rstrip("/") in PUBLIC_PATHS


DESCRIPTION = f"""
**{BYLINE}** | {TAGLINE}

One bounded equation scores systemic risk in oncology (cancer surveillance) and disaster science (urban hazard and resilience):

`R = L · E · V · (1 − ρ)`

| Factor | Meaning | Oncology (HCC) | Disaster science |
|---|---|---|---|
| **L** likelihood | how probable the hazard is | annual cancer probability from a validated score | annual probability the hazard materially strikes |
| **E** exposure | who or what is in harm's way | share of the at-risk population in the surveillance footprint | share of people and assets in the hazard zone |
| **V** vulnerability | how badly those exposed are hurt | liver reserve (ALBI grade) | housing, services, poverty, governance |
| **ρ** resilience | fraction of inherent risk the system absorbs | surveillance effectiveness | coping capacity: warning, infrastructure, health care |

R is placed on five **fixed** tiers (1 Low < 0.05 · 2 Moderate 0.05–0.15 · 3 High 0.15–0.35 · 4 Severe 0.35–0.60 · 5 Critical ≥ 0.60), identical for every patient, city and year.

**Research prototype. Not validated, not a medical device, not for patient-care or emergency decisions.
R is a relative, rubric-based index, not a probability, forecast or loss estimate. Do not send identifiable data.**

Interactive explainer videos, case studies and an embeddable 3D/4D widget: see the [developer portal](/).
"""

TAGS = [
    {"name": "Scoring", "description": "Core RMTI engine: single assessment, time-indexed trajectory, cohort ranking."},
    {"name": "Oncology", "description": "Cancer-site modules (HCC, lung, breast), two-sense resilience, retrospective validation."},
    {"name": "Interoperability", "description": "FHIR R4 RiskAssessment export (status 'preliminary', research use)."},
    {"name": "Registry and governance", "description": "Evidence, parameters, cohorts, ladder checks and reviewed proposals. Constants change only by reviewed release."},
    {"name": "Health", "description": "Liveness, versions and disclaimer."},
]
META = {
    ("POST", "/v1/snapshot"): ("Scoring", "Score one assessment, with optional before/after intervention"),
    ("POST", "/v1/trajectory"): ("Scoring", "Time-indexed run: level-and-slope filter over review cycles"),
    ("POST", "/v1/cohort/rank"): ("Scoring", "Rank a cohort by tier, then by expected annual loss"),
    ("POST", "/v1/validate"): ("Oncology", "Retrospective validation on serial pseudonymous rows"),
    ("POST", "/v1/hcc/patient"): ("Oncology", "HCC score from routine labs (refuses L/V variable overlap)"),
    ("POST", "/v1/lung/inputs"): ("Oncology", "Turn raw lung inputs into L, V and rho_bio"),
    ("POST", "/v1/oncoclastics/two-sense"): ("Oncology", "Biological and care-system senses of resilience"),
    ("POST", "/v1/oncoclastics/trajectory"): ("Oncology", "Two-sense trajectory with descriptive events"),
    ("POST", "/v1/fhir/risk-assessment"): ("Interoperability", "Export a reading as a FHIR R4 RiskAssessment"),
    ("GET", "/v1/registry"): ("Registry and governance", "Registry version, hash, lock state and consistency"),
    ("GET", "/v1/registry/evidence"): ("Registry and governance", "Evidence table"),
    ("GET", "/v1/registry/parameters"): ("Registry and governance", "Parameter file and hash"),
    ("GET", "/v1/registry/ladder-check"): ("Registry and governance", "Ladder face-validity check"),
    ("GET", "/v1/registry/cohorts"): ("Registry and governance", "Registered cohorts"),
    ("POST", "/v1/registry/ladder-support"): ("Registry and governance", "Does a dataset separate each ECOG step?"),
    ("POST", "/v1/registry/cohorts/check"): ("Registry and governance", "Preview cohort overlap (writes nothing)"),
    ("POST", "/v1/registry/proposals"): ("Registry and governance", "Queue a change for human review (admin key)"),
    ("GET", "/v1/registry/proposals"): ("Registry and governance", "List queued proposals (admin key)"),
    ("GET", "/health"): ("Health", "Liveness, engine and registry stamp"),
}
OPERATIONS = [(m, p, META[(m, p)][0], META[(m, p)][1]) for (m, p) in META]


def apply_metadata(app):
    """Group and describe the existing routes for the reference docs. Does not touch behaviour."""
    for r in app.routes:
        for m in getattr(r, "methods", None) or []:
            if (m, r.path) in META:
                r.tags, r.summary = [META[(m, r.path)][0]], META[(m, r.path)][1]


# ----------------------------------------------------------------------------------------------- shared CSS
_CSS = """
:root{--bg:#ffffff;--fg:#10262b;--mute:#5b7075;--line:#dfe7ea;--card:#f5f8f9;--brand:#0b3b40;--brand2:#0b5c63;--acc:#e8a317;--code:#0f1f23;--codefg:#d7ecef}
@media (prefers-color-scheme:dark){:root{--bg:#0d1a1d;--fg:#e4f0f2;--mute:#9bb2b7;--line:#223a40;--card:#12262a;--brand:#0b3b40;--brand2:#7cc7cf;--code:#08130f;--codefg:#d7ecef}}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 -apple-system,"Segoe UI",Inter,Roboto,Helvetica,Arial,sans-serif}
a{color:var(--brand2)}code,pre{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
.top{position:sticky;top:0;z-index:20;background:var(--brand);color:#fff;display:flex;gap:18px;align-items:center;padding:10px 24px}
.top b{font-size:15px;letter-spacing:.2px}.top a{color:#cfe6e9;text-decoration:none;font-size:14px}.top a:hover{color:#fff}.top .sp{flex:1}
.pill{font-size:12px;font-weight:700;border-radius:999px;padding:3px 10px;border:1px solid #b45309;background:#fff7ed;color:#7c2d12}
.wrap{display:grid;grid-template-columns:240px minmax(0,1fr);max-width:1240px;margin:0 auto}
nav.side{position:sticky;top:52px;align-self:start;height:calc(100vh - 52px);overflow:auto;padding:28px 18px;border-right:1px solid var(--line)}
nav.side a{display:block;padding:6px 10px;border-radius:8px;color:var(--mute);text-decoration:none;font-size:14.5px}nav.side a:hover{background:var(--card);color:var(--fg)}
main{padding:36px 40px 80px}
.hero{background:linear-gradient(135deg,#0b3b40 0%,#0b5c63 100%);color:#fff;border-radius:18px;padding:40px 40px 34px;margin-bottom:30px}
.hero h1{margin:0 0 6px;font-size:38px;line-height:1.15;letter-spacing:-.02em}.hero .by{font-size:18px;color:#d0e8ea;margin:4px 0}.hero .tag{font-size:16px;color:#9bd1d6}
.hero .eq{font:600 30px/1.3 ui-monospace,Menlo,Consolas,monospace;margin:22px 0 18px;color:#fff}
.btn{display:inline-block;margin:6px 10px 0 0;padding:10px 18px;border-radius:10px;font-weight:600;text-decoration:none;background:var(--acc);color:#1d1400}.btn.alt{background:transparent;color:#fff;border:1px solid #8fc2c8}
h2{margin:46px 0 10px;font-size:27px;letter-spacing:-.01em;padding-top:8px;border-top:1px solid var(--line)}h3{margin:26px 0 6px;font-size:19px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px;margin:14px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px 18px}.card h4{margin:0 0 6px;font-size:16px}.card p{margin:4px 0;color:var(--mute);font-size:14.5px}
table{border-collapse:collapse;width:100%;font-size:14.5px;margin:12px 0}th,td{border:1px solid var(--line);padding:8px 10px;text-align:left;vertical-align:top}th{background:var(--card)}
pre{background:var(--code);color:var(--codefg);border-radius:12px;padding:16px 18px;overflow:auto;font-size:13.5px;line-height:1.5;margin:8px 0}
.tabs button{border:1px solid var(--line);background:var(--card);color:var(--fg);padding:6px 14px;border-radius:8px 8px 0 0;cursor:pointer;font-weight:600}.tabs button.on{background:var(--code);color:#fff;border-color:var(--code)}
.tier{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;margin:12px 0}.tier div{border-radius:10px;padding:12px;color:#fff;text-align:center;font-weight:700}.tier small{display:block;font-weight:400;opacity:.9}
.note{border-left:4px solid var(--acc);background:var(--card);padding:12px 16px;border-radius:0 10px 10px 0;margin:14px 0;font-size:15px}
.warn{border:2px solid #b45309;background:#fff7ed;color:#7c2d12;padding:12px 16px;border-radius:10px;margin:14px 0;font-size:15px}
.m{font-weight:700;font-size:12px;padding:2px 8px;border-radius:6px;color:#fff}.m.g{background:#2e7d57}.m.p{background:#4A6FA5}
iframe.w{width:100%;height:560px;border:1px solid var(--line);border-radius:14px;background:var(--card)}
footer{margin-top:50px;color:var(--mute);font-size:14px;border-top:1px solid var(--line);padding-top:18px}
@media(max-width:900px){.wrap{grid-template-columns:1fr}nav.side{display:none}main{padding:22px 18px 60px}.hero h1{font-size:28px}.tier{grid-template-columns:1fr 1fr}}
"""


def _esc(s):
    return html.escape(str(s), quote=True)


def _cases():
    try:
        import rmti_cases as K
        out = {}
        for c in K.PRESETS.values():
            out[c["key"]] = {k: c[k] for k in ("label", "name", "L", "E", "V", "rho_now", "rho_after", "domain", "source")}
            out[c["key"]]["V"] = round(c["V"], 4)
        return out
    except Exception:       # noqa: BLE001
        return {"example": dict(label="Example", name="Illustrative example", L=0.30, E=0.65, V=0.55, rho_now=0.20, rho_after=0.50, domain="demo",
                                source="Illustrative values")}


# ----------------------------------------------------------------------------------------------- landing page
def landing_html(version):
    base = "https://YOUR-API-HOST"
    curl = f"""curl -X POST {base}/v1/snapshot \\
  -H "X-API-Key: $RMTI_KEY" -H "Content-Type: application/json" \\
  -d '{{"domain":"oncoclastics","site":"hcc","N":100000,"L":0.30,"E":0.65,"V":0.55,"rho_now":0.20,"rho_after":0.50,"C":5}}'"""
    py = """import os, requests

r = requests.post(
    "https://YOUR-API-HOST/v1/snapshot",
    headers={"X-API-Key": os.environ["RMTI_KEY"]},
    json={"domain": "oncoclastics", "site": "hcc", "N": 100000,
          "L": 0.30, "E": 0.65, "V": 0.55, "rho_now": 0.20, "rho_after": 0.50, "C": 5},
    timeout=30,
)
r.raise_for_status()
print(r.json()["R_now"], r.json()["tier_now"])"""
    js = """// Call from YOUR server code. Never put the API key in a public web page.
const res = await fetch("https://YOUR-API-HOST/v1/snapshot", {
  method: "POST",
  headers: { "X-API-Key": process.env.RMTI_KEY, "Content-Type": "application/json" },
  body: JSON.stringify({ domain: "oncoclastics", site: "hcc", N: 100000,
                         L: 0.30, E: 0.65, V: 0.55, rho_now: 0.20, rho_after: 0.50, C: 5 }),
});
const out = await res.json();
console.log(out.R_now, out.tier_now);"""
    resp = """{
  "R_now": 0.086,          // 0.30 × 0.65 × 0.55 × (1 − 0.20)
  "tier_now": "2 Moderate",
  "R_after": 0.054,        // with ρ after = 0.50
  ...                      // more fields: EAL index, risk reduction, posture (see /docs)
}"""
    rows = "".join(f"<tr><td><span class='m {'g' if m == 'GET' else 'p'}'>{m}</span></td><td><code>{_esc(p)}</code></td><td>{_esc(t)}</td><td>{_esc(s)}</td></tr>" for m, p, t, s in OPERATIONS)
    embed = f"""<iframe src="{base}/widget?case=lilongwe" width="100%" height="560" style="border:0" title="RMTI viewer"></iframe>"""
    pm = """// Optional: drive the widget from the host page (values never travel in the URL)
const w = document.querySelector("iframe").contentWindow;
w.postMessage({ type: "rmti.set", values: { L: 0.4, E: 0.8, V: 0.6, rho_now: 0.2, rho_after: 0.35 } }, "*");
window.addEventListener("message", (e) => {
  if (e.data?.type === "rmti.ready")  console.log("widget ready");
  if (e.data?.type === "rmti.result") console.log(e.data.R_now, e.data.tier_now, e.data.R_after, e.data.tier_after);
});"""
    case_keys = ", ".join(f"<code>{_esc(k)}</code>" for k in _cases())
    tiers = [("1 Low", "R &lt; 0.05", "#7F8FA6"), ("2 Moderate", "0.05–0.15", "#4A6FA5"), ("3 High", "0.15–0.35", "#C9A227"), ("4 Severe", "0.35–0.60", "#C2662D"), ("5 Critical", "R ≥ 0.60", "#9B2C2C")]
    tier_html = "".join(f"<div style='background:{c}'>{n}<small>{r}</small></div>" for n, r, c in tiers)
    nav = [("overview", "Overview"), ("quickstart", "Quickstart"), ("auth", "Authentication"), ("endpoints", "Endpoints"), ("model", "The model"),
           ("levers", "Levers and case studies"), ("widget", "Embeddable widget"), ("safety", "Safety and limits")]
    nav_html = "".join(f"<a href='#{i}'>{t}</a>" for i, t in nav)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_esc(TITLE)}</title><meta name="description" content="{_esc(BYLINE)} | {_esc(TAGLINE)}"><style>{_CSS}</style></head><body>
<div class="top"><b>RMTI API</b><a href="#quickstart">Quickstart</a><a href="/docs">API reference</a><a href="#widget">Widget</a><a href="{_esc(APP_URL)}">Live demo</a><span class="sp"></span>
<span class="pill">RESEARCH PROTOTYPE · DEMO · NO PATIENT DATA</span></div>
<div class="wrap"><nav class="side">{nav_html}<hr style="border:0;border-top:1px solid var(--line);margin:16px 0"><a href="/docs">API reference (Swagger)</a><a href="/redoc">API reference (ReDoc)</a><a href="/health">Health</a></nav><main>
<section class="hero"><h1>{_esc(TITLE)}</h1><div class="by">{_esc(BYLINE)}</div><div class="tag">{_esc(TAGLINE)}</div>
<div class="eq">R = L · E · V · (1 − ρ)</div><a class="btn" href="#quickstart">Get started</a><a class="btn alt" href="/docs">API reference</a><a class="btn alt" href="#widget">Embed the 3D/4D widget</a>
<p style="margin:18px 0 0;color:#b9d6d9;font-size:14px">Engine v{_esc(version)} · Apache-2.0 · independent academic work</p></section>

<h2 id="overview" style="border:0;margin-top:10px">Overview</h2>
<p>The Risk Mechanism Theory Index turns <b>a hazard, who is exposed, how fragile they are, and how well a system copes</b> into a single bounded residual-risk score, with the same fixed tiers for every patient, city and year. One engine serves two domains: <b>oncology</b> (cancer surveillance, starting with hepatocellular carcinoma) and <b>disaster science</b> (urban hazard and climate resilience). The API returns scores, tiers, expected-loss indices, time-indexed trajectories, cohort rankings and FHIR exports, each stamped with the registry version that produced it.</p>
<div class="grid"><div class="card"><h4>Auditable</h4><p>Every response carries <code>X-RMTI-Registry</code>: the registry version and hash. Constants change only by reviewed release.</p></div>
<div class="card"><h4>Bounded and fixed</h4><p>Inputs live in 0–1. Five fixed tiers. No hidden recalibration from uploaded data.</p></div>
<div class="card"><h4>Privacy by design</h4><p>No patient identifiers accepted. Pseudonymous study codes only. Public demo runs on synthetic and published aggregate data.</p></div></div>

<h2 id="quickstart">Quickstart</h2>
<p><b>1. Get a key.</b> Send <code>X-API-Key</code> on every <code>/v1</code> call. Keys are issued by the operator of this deployment. <b>2. Call.</b> <b>3. Read R and the tier.</b></p>
<div class="tabs"><button class="on" data-t="t1">curl</button> <button data-t="t2">Python</button> <button data-t="t3">JavaScript (server)</button></div>
<pre id="t1" class="tp">{_esc(curl)}</pre><pre id="t2" class="tp" style="display:none">{_esc(py)}</pre><pre id="t3" class="tp" style="display:none">{_esc(js)}</pre>
<h3>Response (abridged)</h3><pre>{_esc(resp)}</pre>
<div class="note">Replace <code>YOUR-API-HOST</code> with this deployment's address. Try every route interactively in the <a href="/docs">API reference</a>: click <b>Authorize</b>, paste your key, then <b>Try it out</b>.</div>

<h2 id="auth">Authentication</h2>
<table><tr><th>Route group</th><th>Needs</th></tr><tr><td><code>/</code>, <code>/docs</code>, <code>/redoc</code>, <code>/openapi.json</code>, <code>/widget</code>, <code>/health</code></td><td>nothing: they show schema, versions and a client-side viewer only</td></tr>
<tr><td><code>/v1/*</code></td><td><code>X-API-Key</code> (comma-separated list in <code>RMTI_API_KEYS</code>)</td></tr><tr><td><code>/v1/registry/proposals</code></td><td><code>X-Admin-Key</code> (<code>RMTI_ADMIN_KEYS</code>); disabled if none is set</td></tr></table>
<p>In production (<code>RMTI_ENV=production</code>) the service <b>fails closed</b>: with no API keys configured it refuses to serve. Never place the key in a public web page; call the API from your own server code.</p>

<h2 id="endpoints">Endpoints</h2>
<table><tr><th></th><th>Path</th><th>Group</th><th>What it does</th></tr>{rows}</table>

<h2 id="model">The model</h2>
<table><tr><th>Factor</th><th>Meaning</th><th>Oncology (HCC)</th><th>Disaster science</th></tr>
<tr><td><b>L</b> likelihood</td><td>how probable the hazard is</td><td>annual cancer probability from a validated score (e.g. aMAP); not re-derived</td><td>annual probability the hazard materially strikes</td></tr>
<tr><td><b>E</b> exposure</td><td>who or what is in harm's way</td><td>share of the at-risk population in the surveillance footprint</td><td>share of people and assets in the hazard zone</td></tr>
<tr><td><b>V</b> vulnerability</td><td>how badly those exposed are hurt</td><td>liver reserve from the ALBI grade; fibrosis progression, comorbidity</td><td>housing, services, poverty, governance</td></tr>
<tr><td><b>ρ</b> resilience</td><td>fraction of inherent risk absorbed</td><td>surveillance effectiveness: none 0.15 · usual 0.20 · outreach 0.45 · specialist 0.50 · optimised 0.65</td><td>coping capacity: warning, infrastructure, health care</td></tr></table>
<p><b>Inherent risk</b> R₀ = L·E·V. <b>Residual risk</b> R = R₀·(1−ρ). <b>Expected annual loss</b> EAL = L·C·(1−ρ), which carries consequence C (1–5) through and ranks cases <i>within</i> a tier.</p>
<div class="tier">{tier_html}</div>

<h2 id="levers">Levers and case studies</h2>
<p>Each lever answers a different question: <b>L</b> can we treat or avoid the cause? <b>E</b> who is in harm's way? <b>V</b> how fragile are they? <b>ρ</b> how well does the system cope? The case-study pages sweep each lever on published cohorts and cities and show what it would take to leave a tier.</p>
<div class="grid">
<div class="card"><h4>Video 1 · RMTI explained</h4><p>The equation, four levers in both domains, fixed tiers, sensitivity, expected loss.</p></div>
<div class="card"><h4>Video 2 · Liver (HCC)</h4><p>HBV, viral, alcohol and cured-HCV cirrhosis cohorts; surveillance, treating the cause, liver reserve; Faria et al. ALBI counts.</p></div>
<div class="card"><h4>Video 3 · Flood and heat</h4><p>Lilongwe, Lagos, Bamako: resilience, exposure and vulnerability what-ifs and single-lever thresholds.</p></div></div>
<p><a href="{_esc(APP_URL)}">Open the live demo</a> for the narrated videos (captions toggle in the player) and the interactive Lever Lab.</p>

<h2 id="widget">Embeddable 3D/4D widget</h2>
<p>A self-contained viewer that plays the calculation step by step: the point travels L → E → V through the bounded cube, colour shows ρ, bars show the running product. It computes in the visitor's browser: <b>nothing is sent to the server or stored</b>.</p>
<pre>{_esc(embed)}</pre>
<p>Presets via <code>?case=</code>: {case_keys}. Other options: <code>&amp;autoplay=1</code>, <code>&amp;embed=1</code> (hide header). Custom values are passed with <code>postMessage</code>, never in the URL, so they stay out of logs:</p>
<pre>{_esc(pm)}</pre>
<iframe class="w" src="/widget?case=lilongwe&amp;embed=1" title="RMTI viewer" loading="lazy"></iframe>

<h2 id="safety">Safety and limits</h2>
<div class="warn"><b>Research prototype.</b> Not validated against real outcomes, not a medical device, not for patient-care or emergency decisions. Parameters are uncalibrated placeholders. R is a relative, rubric-based index, not a probability, forecast, engineering assessment or loss estimate. After-values in examples are scenarios, not observations.</div>
<ul><li><b>No identifiable data.</b> Use pseudonymous study codes. The public deployment is for synthetic data and published aggregates only.</li>
<li><b>Interoperability:</b> FHIR exports are <code>preliminary</code>, with R as a tier plus a named extension, never a probability. Validate with the HL7 validator before any exchange.</li>
<li><b>Governance:</b> constants change only by a reviewed release; uploaded data never changes a score.</li></ul>
<footer>{_esc(BYLINE)} · ORCID 0000-0001-8498-7380 · Independent academic work; not an official product of the World Bank Group, Harvard University or any other institution. Apache-2.0, provided "as is", without warranty.<br>Contact: <a href="mailto:cesar.marolla@alumni.harvard.edu">cesar.marolla@alumni.harvard.edu</a></footer>
</main></div>
<script>document.querySelectorAll('.tabs button').forEach(b=>b.onclick=()=>{{document.querySelectorAll('.tabs button').forEach(x=>x.classList.remove('on'));b.classList.add('on');document.querySelectorAll('.tp').forEach(p=>p.style.display=p.id===b.dataset.t?'block':'none')}});</script>
</body></html>"""


# ----------------------------------------------------------------------------------------------- themed Swagger UI
_SWAGGER_CSS = """<style>
body{margin:0;background:#fff}.swagger-ui .topbar{display:none}
.rmti-hero{background:linear-gradient(135deg,#0b3b40,#0b5c63);color:#fff;padding:28px 36px;font-family:-apple-system,"Segoe UI",Inter,Roboto,sans-serif}
.rmti-hero h1{margin:0 0 4px;font-size:30px;letter-spacing:-.02em}.rmti-hero p{margin:2px 0;color:#d0e8ea}.rmti-hero code{background:#0b2d31;padding:2px 8px;border-radius:6px;color:#fff}
.rmti-hero a{color:#ffd37a}.rmti-pill{display:inline-block;margin-top:10px;font-size:12px;font-weight:700;border:1px solid #b45309;background:#fff7ed;color:#7c2d12;border-radius:999px;padding:3px 10px}
.swagger-ui .opblock-tag{font-size:20px;border-bottom:1px solid #dfe7ea}.swagger-ui .info{display:none}
.swagger-ui .opblock.opblock-post{border-color:#4A6FA5;background:rgba(74,111,165,.06)}.swagger-ui .opblock.opblock-get{border-color:#2e7d57;background:rgba(46,125,87,.06)}
.swagger-ui .btn.authorize{border-color:#0b5c63;color:#0b5c63}.swagger-ui .btn.authorize svg{fill:#0b5c63}
</style>"""
_HERO = f"""<div class="rmti-hero"><h1>{TITLE}</h1><p><b>{BYLINE}</b> | {TAGLINE}</p><p><code>R = L · E · V · (1 − ρ)</code> &nbsp; Click <b>Authorize</b> and paste your <code>X-API-Key</code> to try routes. <a href="/">Developer portal</a> · <a href="/redoc">ReDoc</a></p>
<span class="rmti-pill">RESEARCH PROTOTYPE · NOT VALIDATED · NOT A MEDICAL DEVICE · NO PATIENT DATA</span></div>"""


def swagger_html():
    page = get_swagger_ui_html(openapi_url="/openapi.json", title=f"{TITLE} · API reference",
                               swagger_ui_parameters={"docExpansion": "list", "defaultModelsExpandDepth": -1, "displayRequestDuration": True,
                                                      "tagsSorter": "alpha", "operationsSorter": "alpha", "persistAuthorization": False}).body.decode()
    return page.replace("</head>", _SWAGGER_CSS + "</head>").replace("<body>", "<body>" + _HERO, 1)


# ----------------------------------------------------------------------------------------------- widget
_WIDGET = r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>RMTI viewer</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/plotly.js/2.35.2/plotly.min.js"></script>
<style>
:root{--bg:#fff;--fg:#10262b;--mute:#5b7075;--line:#dfe7ea;--card:#f5f8f9;--brand:#0b5c63}
@media (prefers-color-scheme:dark){:root{--bg:#0d1a1d;--fg:#e4f0f2;--mute:#9bb2b7;--line:#223a40;--card:#12262a;--brand:#7cc7cf}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.45 -apple-system,"Segoe UI",Inter,Roboto,sans-serif}
header{display:flex;gap:10px;align-items:center;padding:8px 14px;background:#0b3b40;color:#fff;flex-wrap:wrap}header b{font-size:14px}header .sp{flex:1}
.pill{font-size:11px;font-weight:700;border:1px solid #b45309;background:#fff7ed;color:#7c2d12;border-radius:999px;padding:2px 9px}
.main{display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:12px;padding:10px 14px}
#plot{height:440px;min-width:0}.panel{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px}
label{display:flex;justify-content:space-between;font-size:12.5px;color:var(--mute);margin-top:6px}input[type=range]{width:100%}select,button{font:inherit;padding:6px 10px;border-radius:8px;border:1px solid var(--line);background:var(--bg);color:var(--fg);cursor:pointer}
button.p{background:#e8a317;border-color:#e8a317;color:#1d1400;font-weight:700}.row{display:flex;gap:8px;align-items:center;margin:8px 0}
.big{font-size:26px;font-weight:800}.badge{display:inline-block;padding:3px 10px;border-radius:999px;color:#fff;font-weight:700;font-size:12.5px}
#cap{padding:6px 14px 0;font-size:15px;font-weight:600;min-height:44px}.foot{padding:4px 14px 12px;color:var(--mute);font-size:11.5px}
body.embed header{display:none}@media(max-width:760px){.main{grid-template-columns:1fr}#plot{height:360px}}
</style></head><body>
<header><b>RMTI viewer</b><span style="opacity:.85">R = L · E · V · (1 − ρ)</span><span class="sp"></span><span class="pill">DEMO · RESEARCH PROTOTYPE · NO PATIENT DATA</span></header>
<div id="cap"></div>
<div class="main"><div id="plot"></div><div class="panel">
<div class="row"><select id="preset" style="flex:1"></select></div>
<div class="row"><button class="p" id="play">▶ Play</button><button id="reset">⟲</button><input type="range" id="tau" min="0" max="6" step="0.01" value="0" style="flex:1"></div>
<div id="sl"></div><hr style="border:0;border-top:1px solid var(--line)">
<div>R now <span class="big" id="rn">–</span> <span class="badge" id="tn">–</span></div>
<div>R after <span class="big" id="ra">–</span> <span class="badge" id="ta">–</span></div>
<div id="post" style="color:var(--mute);margin-top:6px;font-size:12.5px"></div><div id="src" style="color:var(--mute);margin-top:8px;font-size:11.5px"></div>
</div></div>
<div class="foot">Computed in your browser. Nothing is sent or stored. Not validated · not a medical device · not for patient-care or emergency decisions. R is a relative index, not a probability.</div>
<script>
const PRESETS=__PRESETS__;
const TIERS=[[0.05,'1 Low','#7F8FA6'],[0.15,'2 Moderate','#4A6FA5'],[0.35,'3 High','#C9A227'],[0.60,'4 Severe','#C2662D'],[Infinity,'5 Critical','#9B2C2C']];
const POSTURE={oncology:{1:'Monitor; usual-care biannual surveillance appropriate',2:'Usual-care biannual surveillance; confirm adherence and recall',3:'Prioritise for surveillance; fixed-interval adherence essential',4:'Structured navigation; close specialist hepatology follow-up',5:'Immediate, resourced pathway; case management'},
 disaster:{1:'Monitor; maintain baseline',2:'Low-regret preventive measures',3:'Structured mitigation; fund soon',4:'Priority capital; act now',5:'Immediate, system-level response'}};
function clamp(x,a,b){return Math.min(b,Math.max(a,x))}
function rmti(L,E,V,rho){return clamp(L,0,1)*clamp(E,0,1)*clamp(V,0,1)*(1-clamp(rho,0,0.99))}
function tierOf(R){for(const t of TIERS){if(R<t[0])return t}}
function ease(t){t=clamp(t,0,1);return t*t*(3-2*t)}
const P={L:0.30,E:0.65,V:0.55,rho_now:0.20,rho_after:0.50,domain:'demo',source:''};
const SL=[['L','L likelihood',1],['E','E exposure',1],['V','V vulnerability',1],['rho_now','ρ now',0.99],['rho_after','ρ after',0.99]];
function keyframes(){const r0=P.L*P.E*P.V;return [[0,0,0,'R = L · E · V · (1 − ρ): four bounded factors'],[1,0,1,'L, likelihood = '+P.L.toFixed(2)+': how probable the hazard is'],
 [2,0,2,'× E, exposure = '+P.E.toFixed(2)+': who is in harm’s way'],[3,0,3,'× V, vulnerability = '+P.V.toFixed(2)+': how badly they are hurt'],
 [3,0,4,'Inherent risk R₀ = '+r0.toFixed(3)+', before resilience'],[3,P.rho_now,5,'× (1 − ρ), ρ = '+P.rho_now.toFixed(2)+': R = '+rmti(P.L,P.E,P.V,P.rho_now).toFixed(3)],
 [3,P.rho_after,6,'Improved state, ρ = '+P.rho_after.toFixed(2)+': R = '+rmti(P.L,P.E,P.V,P.rho_after).toFixed(3)]]}
function stateAt(tau){const K=keyframes();const k=Math.min(Math.floor(tau),5),f=tau-k;const t=ease(f/0.4);const a=K[k],b=K[Math.min(k+1,6)];
 if(tau>=6)return {u:b[0],rho:b[1],rev:b[2],cap:b[3]};return {u:a[0]+(b[0]-a[0])*t,rho:a[1]+(b[1]-a[1])*t,rev:a[2]+(b[2]-a[2])*t,cap:(t>0.5?b[3]:a[3])}}
function pos(u){const w=[[0,0,0],[P.L,0,0],[P.L,P.E,0],[P.L,P.E,P.V]];const i=Math.min(Math.floor(u),2),f=u-i;const p=[0,1,2].map(j=>w[i][j]+(w[i+1][j]-w[i][j])*f);
 const tr=w.slice(0,i+1).concat([p]);return {p,tr}}
function bars(rev){const r0=P.L*P.E*P.V;const fin=[P.L,P.L*P.E,r0,r0,rmti(P.L,P.E,P.V,P.rho_now),rmti(P.L,P.E,P.V,P.rho_after)];return fin.map((v,k)=>v*clamp(rev-k,0,1))}
const LAB=['L','L·E','L·E·V','R₀','R now','R after'],COL=['#607d8b','#607d8b','#607d8b','#b3261e','#e8a317','#1b7f5c'];
let tau=0,playing=false,last=0,ready=false;
function fg(){return getComputedStyle(document.body).color}
function draw(){const s=stateAt(tau),{p,tr}=pos(s.u),b=bars(s.rev);document.getElementById('cap').textContent=s.cap;
 const ax={range:[0,1],dtick:0.25,gridcolor:'#9fb3b8',backgroundcolor:'rgba(0,0,0,0)',color:fg()};
 const data=[{type:'scatter3d',mode:'lines',x:tr.map(q=>q[0]),y:tr.map(q=>q[1]),z:tr.map(q=>q[2]),line:{color:'#607d8b',width:6},hoverinfo:'skip'},
 {type:'scatter3d',mode:'markers',x:[p[0]],y:[p[1]],z:[p[2]],marker:{size:9,color:[s.rho],colorscale:[[0,'#b3261e'],[.5,'#e8a317'],[1,'#1b7f5c']],cmin:0,cmax:1,line:{color:'#263238',width:2},colorbar:{title:'ρ',thickness:10,len:0.5,x:0.55}},hovertemplate:'L=%{x:.2f} E=%{y:.2f} V=%{z:.2f}<extra></extra>'},
 {type:'bar',x:LAB,y:b,marker:{color:COL},text:b.map(v=>v>1e-9?v.toFixed(3):''),textposition:'outside',xaxis:'x',yaxis:'y',hoverinfo:'skip'}];
 const lay={margin:{l:0,r:10,t:10,b:30},showlegend:false,paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(0,0,0,0)',font:{color:fg(),size:11},
  scene:{domain:{x:[0,0.56],y:[0,1]},aspectmode:'cube',xaxis:Object.assign({title:'L'},ax),yaxis:Object.assign({title:'E'},ax),zaxis:Object.assign({title:'V'},ax),camera:{eye:{x:1.6,y:1.5,z:1}}},
  xaxis:{domain:[0.66,1],anchor:'y'},yaxis:{domain:[0.12,0.9],range:[0,1],anchor:'x',gridcolor:'#9fb3b8'}};
 Plotly.react('plot',data,lay,{displayModeBar:false,responsive:true});document.getElementById('tau').value=tau}
function results(){const rn=rmti(P.L,P.E,P.V,P.rho_now),ra=rmti(P.L,P.E,P.V,P.rho_after),tn=tierOf(rn),ta=tierOf(ra);
 document.getElementById('rn').textContent=rn.toFixed(3);document.getElementById('ra').textContent=ra.toFixed(3);
 const bn=document.getElementById('tn'),ba=document.getElementById('ta');bn.textContent=tn[1];bn.style.background=tn[2];ba.textContent=ta[1];ba.style.background=ta[2];
 const dom=P.domain==='disaster'?'disaster':'oncology';document.getElementById('post').textContent='Posture now: '+POSTURE[dom][+tn[1][0]];document.getElementById('src').textContent=P.source||'';
 if(ready)parent.postMessage({type:'rmti.result',R_now:rn,tier_now:tn[1],R_after:ra,tier_after:ta[1]},'*')}
function apply(v){for(const [k,,mx] of SL)if(typeof v[k]==='number'&&isFinite(v[k]))P[k]=clamp(v[k],0,mx);for(const k of ['domain','source'])if(typeof v[k]==='string')P[k]=v[k];
 for(const [k] of SL){document.getElementById('s_'+k).value=P[k];document.getElementById('v_'+k).textContent=P[k].toFixed(3)}results();draw()}
function build(){const sl=document.getElementById('sl');for(const [k,lab,mx] of SL){sl.insertAdjacentHTML('beforeend','<label><span>'+lab+'</span><span id="v_'+k+'"></span></label><input type="range" id="s_'+k+'" min="0" max="'+mx+'" step="0.001">');}
 for(const [k] of SL)document.getElementById('s_'+k).oninput=e=>{P[k]=+e.target.value;document.getElementById('v_'+k).textContent=P[k].toFixed(3);results();draw()};
 const sel=document.getElementById('preset');sel.innerHTML='<option value="">Custom / illustrative</option>'+Object.entries(PRESETS).map(([k,c])=>'<option value="'+k+'">'+c.name.replace(/</g,'&lt;')+'</option>').join('');
 sel.onchange=()=>{if(sel.value){apply(PRESETS[sel.value]);tau=0;draw()}};
 document.getElementById('play').onclick=()=>{playing=!playing;document.getElementById('play').textContent=playing?'⏸ Pause':'▶ Play';if(playing){if(tau>=6)tau=0;last=performance.now();requestAnimationFrame(tick)}};
 document.getElementById('reset').onclick=()=>{tau=0;draw()};document.getElementById('tau').oninput=e=>{tau=+e.target.value;draw()}}
function tick(now){if(!playing)return;tau=Math.min(6,tau+(now-last)/1000*0.55);last=now;draw();if(tau>=6){playing=false;document.getElementById('play').textContent='▶ Play';return}requestAnimationFrame(tick)}
window.addEventListener('message',e=>{const d=e.data;if(d&&d.type==='rmti.set'&&d.values&&typeof d.values==='object'){apply(d.values);document.getElementById('preset').value=''}});
const q=new URLSearchParams(location.search);if(q.get('embed')==='1')document.body.classList.add('embed');
build();const c=q.get('case');if(c&&PRESETS[c]){apply(PRESETS[c]);document.getElementById('preset').value=c}else apply(P);
ready=true;parent.postMessage({type:'rmti.ready'},'*');results();if(q.get('autoplay')==='1'){document.getElementById('play').click()}
</script></body></html>"""


def widget_html():
    return _WIDGET.replace("__PRESETS__", json.dumps(_cases(), ensure_ascii=False).replace("</", "<\\/"))


# ----------------------------------------------------------------------------------------------- mount
def mount(app, version):
    def _home():   # serves developer_portal.html (next to this file) if present, else the built-in landing page
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "developer_portal.html")
        try:
            with open(p, encoding="utf-8") as fh:
                return HTMLResponse(fh.read())
        except OSError:
            return HTMLResponse(landing_html(version))
    app.add_api_route("/", _home, methods=["GET"], include_in_schema=False)
    app.add_api_route("/docs", lambda: HTMLResponse(swagger_html()), methods=["GET"], include_in_schema=False)
    app.add_api_route("/widget", lambda: HTMLResponse(widget_html()), methods=["GET"], include_in_schema=False)
    app.add_api_route("/favicon.ico", lambda: Response(status_code=204), methods=["GET"], include_in_schema=False)
    apply_metadata(app)
