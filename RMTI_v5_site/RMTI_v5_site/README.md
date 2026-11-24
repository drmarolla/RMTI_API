# Risk Mechanism Theory Index (RMTI)

Streamlit site and REST API built on the hash-locked RMTI engine (`rmti_python/core`, v2.2.1).
Research prototype. Not validated, not a medical device, not for patient-care or emergency decisions.

Videos: tools/make_videos.py renders the three case-study videos (private tooling, not shown on the site).

Run:  `pip install -r requirements.txt`  then  `streamlit run app.py`
API:  `uvicorn api:app --port 8000`  (docs at /docs)  ·  Tests: `python -m unittest discover -s tests`

Keep the GitHub repository PRIVATE. Visitors see only the running site; no source code is rendered on any page.
Videos: put .mp4 files in the repo root or `media/`; they appear automatically (file names containing liver, lung or breast
also fill the matching case-study page).
Env vars: RMTI_API_KEYS, RMTI_DISABLE_SANDBOX, RMTI_API_URL, RMTI_PUBLIC_API_URL, RMTI_CORS_ORIGINS, RMTI_DATA_DIR.
