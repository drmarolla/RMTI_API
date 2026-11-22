# REST API and developer portal (v1)

Run: `pip install "rmti-py[api]"` → `rmti serve` → open `http://127.0.0.1:8000/` (portal), `/docs` (Swagger UI), `/redoc`, `/openapi.json`.

## Issuing keys (operators)
```bash
rmti keys new --name worldbank-pipeline --org "Example Development Bank" --scopes score,batch --rate 120
# prints the key ONCE (give it to the client) and a JSON entry containing only its SHA-256 digest
export RMTI_API_CLIENTS='[{"name":"worldbank-pipeline","org":"Example Development Bank","sha256":"…","scopes":["batch","score"],"rate_per_min":120}]'
rmti serve --host 0.0.0.0
```
There are **no default keys**. With no clients configured the API returns `503` on protected routes (fail-closed). `RMTI_AUTH=disabled` opens everything for local development only.

| Variable | Meaning | Default |
|---|---|---|
| `RMTI_API_CLIENTS` / `RMTI_API_CLIENTS_FILE` | JSON list of client entries (digests, scopes, rate) | none |
| `RMTI_AUTH` | `required` or `disabled` | `required` |
| `RMTI_CORS_ORIGINS` | comma list of origins allowed to call the API from a browser | none |
| `RMTI_CONTACT` | shown in the portal as the access contact | empty |
| `RMTI_MAX_ROWS` / `RMTI_MAX_UPLOAD_BYTES` / `RMTI_MAX_JSON_BYTES` | request limits | 10,000 / 10 MB / 8 MB |

Scopes: `score` (single assessments, simulation, HCC), `batch` (cohorts, uploads, portfolio), `fhir` (FHIR output).

## Endpoints
| | |
|---|---|
| `GET /v1/health`, `GET /v1/methodology` | public |
| `POST /v1/assessments` | score one unit (tier, posture, EAL, scenario, tier margin) |
| `POST /v1/cohorts/score`, `/v1/cohorts/score/upload` | cohort summary + records, JSON or CSV/Parquet |
| `POST /v1/simulations`, `/v1/portfolios/optimize` | Monte Carlo tier probabilities; budgeted selection |
| `POST /v1/hcc/patients/score`, `…/upload`, `/v1/hcc/albi` | HCC surveillance triage (research use) |
| `POST /v1/fhir/RiskAssessment`, `…/_batch` | FHIR R4 `RiskAssessment` / `Bundle` |

## Hosting the portal separately
The portal is static (`src/rmti/portal/`). Copy it to any static host, set the Base URL in its Connection panel to your API, and add the portal's origin to `RMTI_CORS_ORIGINS`.

## What this API deliberately is not
* Not HIPAA-attested; no BAA, SOC 2 or ISO 27001. Do not send PHI. TLS must be provided by the host.
* Not a FHIR server (no read/search/CapabilityStatement/patient store); output structure is checked against `fhir.resources` R4B models, **not** the official HL7 validator.
* No OAuth 2.0 / SMART on FHIR, no key rotation UI, no persistent audit trail. Rate limits are per process: enforce a global limit at your gateway.
* The portal's JavaScript was exercised in Chromium and a DOM test, not across browsers or with assistive-technology audits.
