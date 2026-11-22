# How to make this release replace the old versions

GitHub's web uploader does not unzip. Unzip this file, then drag the *contents* into the repo root
(same names overwrite). Or, from a terminal (recommended):

```bash
git clone https://github.com/drmarolla/<your-repo>.git && cd <your-repo>
unzip -o ../RMTI_v3_release.zip -d .
bash clean_old_files.sh          # removes stale duplicates only (see below)
git add -A && git commit -m "RMTI v3: renamed to Risk Mechanism Theory Index, new Developer API v1" && git push
```

## What gets overwritten
`app.py`, `api.py`, `requirements.txt`, `README.md`, `.streamlit/config.toml`, `tests/test_api.py`.

## What clean_old_files.sh removes
Only duplicates and abandoned drafts: `Home*.py`, `app.py.py`, `app.py (1).py`, `streamlit_app*.py`,
`PASTE_*.txt`, the `oncoclastics_*` redesign/override/fixpack folders, and any file with `(1)` or `(2)` in the name.
It keeps `rmti_engine/`, media, narration, voice, zips, the numbered calculator/matrix/case-study pages,
and the helper modules they import (`ui_*.py`, `rmti_theme.py`, `style.py`, etc.).

## Streamlit Community Cloud
1. Main file path: `app.py` (Settings > General).
2. The browser-tab title is now "Risk Mechanism Theory Index (RMTI)" (set in code).
3. The app's URL name is set in the Streamlit dashboard, not in code: Settings > General > App URL.
4. Add `RMTI_API_KEYS` (and optionally `RMTI_API_URL`) under Settings > Secrets / environment.
5. Reboot the app after the push.

## Known follow-ups
* Your existing calculator/matrix pages still use their old internal styling. They are loaded unchanged inside the new navigation.
* `rmti_client.py` / `ui_api.py` were written for the old API routes. If any page calls them, point it at `rmti_sdk.py` and `/v1/...`.
* On Streamlit Cloud, access requests saved to `data/` are lost on reboot. Send them to a sheet, database or email for production.
