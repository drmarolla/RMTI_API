# Risk Mechanism Theory Index (RMTI)

Streamlit portal and REST API built around **R = L · E · V · (1 − ρ)**.
Research prototype. Not validated, not a medical device, not for patient-care or emergency decisions.

## Run locally
```
pip install -r requirements.txt
uvicorn api:app --port 8000                      # API, docs at http://localhost:8000/docs
RMTI_API_URL=http://localhost:8000 streamlit run app.py   # portal calling the API
streamlit run app.py                             # portal with the built-in engine
python -m unittest discover -s tests             # API tests
```

## API v1 at a glance
| Endpoint | Purpose |
|---|---|
| `POST /v1/risk/score` | Score one case: risk, tier, elasticity, ranked what-if reductions |
| `POST /v1/risk/score/fhir` | Same, as a FHIR R4-shaped RiskAssessment |
| `POST /v1/risk/batch` | Score many cases (cap depends on tier) |
| `POST /v1/risk/sensitivity` | Sweep one lever from 0 to 1 |
| `GET /v1/usage`, `/v1/meta`, `/health` | Limits, formula and tier bands, liveness |

Auth: `X-API-Key`. Issue keys with `RMTI_API_KEYS="key1:research:Lab A,key2:enterprise:Hospital B"`.
Set `RMTI_DISABLE_SANDBOX=1` in production to turn off the public sandbox key.
Errors are JSON with `code`, `detail` and `request_id`. Request bodies are never logged.

## Wiring the real engine
`rmti_core.compute_core()` is the only place the formula lives. To score with the vendored
`rmti_engine` (v2.4.0), change that one function. Tier bands in `rmti_core.TIER_CUTS` are
default screening bands, not clinically validated cut-offs.

## Environment variables
`RMTI_API_URL` (portal calls a deployed API) · `RMTI_PUBLIC_API_URL` (URL shown in code samples) ·
`RMTI_API_KEYS` · `RMTI_DISABLE_SANDBOX` · `RMTI_CORS_ORIGINS` · `RMTI_DATA_DIR`

License: Apache-2.0
