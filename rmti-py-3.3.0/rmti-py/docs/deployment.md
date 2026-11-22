# Deployment: GitHub → Streamlit → API → PyPI

## 1. GitHub
```bash
cd rmti-py
git init && git add . && git commit -m "RMTI-Py 3.1.0"
git branch -M main
git remote add origin https://github.com/<you>/rmti-py.git     # create the empty repo on github.com first
git push -u origin main
```
Edit `CITATION.cff` (`repository-code`) and `pyproject.toml` (add `[project.urls]`) with the real URL.
Actions (`.github/workflows/ci.yml`) will run the tests on every push.

## 2. Streamlit Community Cloud (the web app)
1. share.streamlit.io → **New app** → pick the repo, branch `main`, **Main file path: `streamlit_app.py`**.
2. Streamlit reads `requirements.txt` at the repo root (it installs `.[app]`: the library + geopandas/rasterio/folium/streamlit).
3. Deploy. Every `git push` redeploys; that is the "sync".
Optional backends (`[gee]`, `[pc]`, `[sat]`) are not in `requirements.txt`; add them (e.g. `.[app,sat]`) only if the web app should use them, and store Earth Engine credentials in Streamlit *Secrets*, never in the repo.
Notes: the free tier has limited memory; very large uploads/rasters should be processed with the library or API, not the web UI.
Uploaded data is processed in the app's server session; do not upload sensitive patient-level data to a public deployment.

## 3. REST API and developer portal
Full instructions (keys, environment variables, CORS, what the API is not): **`docs/api.md`**.
```bash
pip install -e ".[api]" && rmti keys new --name me --scopes score,batch,fhir   # then set RMTI_API_CLIENTS and run: rmti serve
docker build -t rmti-api . && docker run -p 8000:8000 -e RMTI_API_CLIENTS='[...]' rmti-api
```
Deploy the image to any container host behind TLS (Render, Fly.io, Cloud Run, Azure Container Apps). Streamlit Cloud does not host FastAPI.
Never put keys in the repository; use the host's secret store.

## 4. PyPI
`rmti` is taken on PyPI; this project is **`rmti-py`** (`import rmti`).
1. Create a PyPI account; at pypi.org → *Publishing* → add a **pending trusted publisher**: project `rmti-py`, owner `<you>`,
   repo `rmti-py`, workflow `publish.yml`, environment `pypi`.
2. In GitHub create an environment named `pypi`.
3. Bump `version` in `pyproject.toml` and `src/rmti/__init__.py`, push, then create a **GitHub Release** → the workflow builds and uploads.
Dry run first against TestPyPI if you like (`python -m build && twine upload -r testpypi dist/*`).
