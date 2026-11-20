# Developer Portal, OpenAPI and API access

- **Try it out** (Developer Portal page): sliders for L, E, V, rho build the JSON payload, cURL, Python and JavaScript snippets and show the response.
  The response is computed inside the app with the same engine; no key is sent. Invalid input (for example L = 1.4) shows the real HTTP 422.
- **Strict validation** (`api.py`): 0 <= L, E, V <= 1; 0 <= rho_now, rho_after < 1; C in 1..5; unknown fields in `/v1/snapshot` are rejected.
- **OpenAPI**: the portal builds the spec from `api.app.openapi()`. Run `python tools/export_openapi.py` to write `docs/openapi.json` as a fallback.
  Live Swagger UI (`/docs`) and `/openapi.json` come from the FastAPI service (`uvicorn api:app`, see CLOUD_RUN.md); Streamlit Cloud cannot host it.
- **Request API access** (top-right button on every page): a form that offers a ready-to-send request. Keys are not provisioned automatically.

Settings (environment variable or Streamlit secret):
| Name | Effect |
|---|---|
| `RMTI_API_URL` | Base URL shown in snippets and a Swagger link in the portal |
| `RMTI_CONTACT_EMAIL` | Enables the "Send by email" button in the access form |
| `RMTI_DEMO_MODE=0` | Private instance label in the bottom bar |
