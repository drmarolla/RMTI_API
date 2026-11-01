# Calculator and cohort sandboxes (add-on)

Research prototype. Not validated, not a medical device. Adds **no equation**: scoring goes through the vendored engine
(`rmti_hcc_cohort.score_cohort`, `rmti_lung` helpers, `combine_rho`, `core.score`).

## Streamlit (new sidebar pages)
- **HCC_Calculator**: the Excel workbook's Calculator and Parameters sheets (age, sex, albumin, bilirubin, platelets -> ALBI -> V; aMAP-ref -> L; R, tier, EAL).
  aMAP (overlaps ALBI) is refused unless you tick the box; the output is then labelled DIAGNOSTIC.
- **Cohort_Sandbox**: HCC, lung, breast. Bundled Ogaki cohort (HCC), your own upload, or a synthetic demo to test the pipeline.
  Output: tier distribution (rho now and after), by aetiology, observed vs published aMAP incidence, cumulative incidence with a competing
  event (Aalen-Johansen), Harrell C of R with optional bootstrap CI, subgroup C-index, downloads.
- Same access gate as the main page (`RMTI_ACCESS_CODES`), same API mode (`RMTI_API_URL`; `RMTI_API_KEY` is sent as `X-API-Key` if set).

## API (new routes, same `X-API-Key` rule as every /v1 route)
- `GET  /v1/sandbox/templates`: columns, required columns, status text, default options per disease.
- `POST /v1/sandbox/{hcc|lung|breast}/score`: body `{"records":[...]}` or `{"dataset":"ogaki"}`, plus `{"options":{...}}`.
- Existing `POST /v1/hcc/patient` is the single-patient calculator (unchanged).

## Data format
`cause`: 1 event of interest, 2 competing event (e.g. death without the cancer), 0 censored. A 0/1 column named `event` is accepted.
`time_years` > 0. `stratum` optional subgroup. Get the exact columns from the template download or `/v1/sandbox/templates`.
- **HCC**: age_years, male, albumin_g_l, bilirubin_umol_l, platelets_1e9_l (+ etiology).
- **Lung**: risk5 (5-year risk as a fraction), v_count (0-4), optional ecog, rho_care, E. 2-year risks are refused.
- **Breast**: SCAFFOLD. No instruments or anchors exist in the engine and none are invented. Supply L, V (and optional E, rho) on 0-1 from your
  own pre-registered mapping; declare the variables behind L and V and any overlap is refused. Write a disease module before reporting results.

## Managing bundled cohorts (delete, update, add) by changing files only
Every `*.csv` in `cohort_data/` is offered as a bundled cohort (set `RMTI_COHORT_DIR` to read them from a folder outside the repo, e.g. a mounted volume, to keep patient data out of git).
- **Add:** drop `mycohort.csv` into `cohort_data/`. The disease is inferred from the columns (HCC lab columns; lung `risk5` + `v_count`; breast `L` + `V`). Optional `mycohort.meta.json`: `{"id": "...", "disease": "hcc|lung|breast", "label": "...", "description": "...", "reference_file": "..."}`.
- **Update:** replace the CSV (same columns). Results recompute. If a reference file exists for it and the file changed, the workbook comparison is skipped with a note rather than failing; update or delete the reference file to match.
- **Delete:** delete the CSV (and its `.meta.json` / reference file). The cohort disappears from the page and the API.
- Every bundled file passes the identifier guard when loaded; a file with a column such as `patient_name` is refused.
- `GET /v1/sandbox/datasets` lists what the server has. Each result carries the file name, row count and SHA-256 so a run can be traced to the exact data.

## Look and accessibility
`.streamlit/config.toml` sets the site-wide theme (also on the existing main page). `style.py` holds the shared look: no green (as in `app.py.py`), text and graphics meet WCAG 2.2 AA contrast
(tested in `tests/test_sandbox.py`), and a tier is never shown by colour alone (number and name always appear).

## Ogaki cohort
`cohort_data/ogaki_hcc_cohort.csv` (3,101 pseudonymised patients) and `ogaki_reference.json` (values from the workbook's Checks sheet).
At the reference settings the sandbox compares itself with the workbook and shows PASS or CHECK for each value.
Patient-level rows of the bundled cohort are NOT shown or returned unless the server sets `RMTI_ALLOW_COHORT_EXPORT=1`.
To remove the cohort: delete the `cohort_data/` folder. The app and API keep working; the bundled option simply disappears.

## Tests
`python -m pytest tests -q` (your 59 tests + 19 in `tests/test_sandbox.py`; API tests need `httpx`, otherwise they skip).
