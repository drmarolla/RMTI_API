# RMTI-Py

Python library, web app and REST API for the **Risk Mechanism Theory Index** (Marolla):
`R = L · E · V · (1 − ρ)`, five fixed decision tiers, Expected Annual Loss, and extensions for
**uncertainty**, **geospatial/satellite exposure**, **portfolio optimisation**, in two domains:
urban infrastructure resilience and hepatocellular-carcinoma (HCC) surveillance.

> **Research prototype.** Scores are decision-support indices, not probabilities or monetary losses.
> The oncology domain is not validated against outcomes and is not a medical device. Demo data are synthetic.

```bash
pip install rmti-py                    # core: numpy, scipy
pip install "rmti-py[geo,viz,sat]"     # + GIS, maps, STAC, xarray/Dask   |  [gee] Earth Engine  |  [pc] Planetary Computer
pip install "rmti-py[app]"             # + Streamlit app      |  [api] = REST API   |  [all] = everything
rmti selfcheck                         # reproduces every published R value (paper Tables 4-5; HCC Tables 1-2)
streamlit run streamlit_app.py         # web app
uvicorn rmti.api:app                   # REST API, docs at /docs
```
Import name `rmti` (the PyPI name `rmti` belongs to another project).

## Layout
```
src/rmti/            core, stochastic, geospatial, stac, gee, sar, timeseries, indices, raster_risk, pipeline, webmap, optimizer,
                     elasticity, api, datasets, domains/{urban,hcc,hcc_geo}, data/ (paper inputs + synthetic samples)
tests/               pytest (core, stochastic, optimizer, geospatial, rasters, STAC offline, pipelines, API, app)
examples/            runnable scripts          docs/   deployment, satellite workflow, oncology, FINDINGS
streamlit_app.py     web app (main file for Streamlit Cloud)      requirements.txt   Streamlit Cloud installs
Dockerfile           REST API image            .github/workflows  CI + PyPI publish
```
| Capability | Module |
|---|---|
| Scoring, tiers, tier-boundary margins | `rmti.core` |
| Monte Carlo over L,E,V,ρ → tier probabilities (Beta, optional Gaussian copula) | `rmti.stochastic` |
| E_sel / N from GIS layers and rasters; per-zone E_sel | `rmti.geospatial` |
| Satellite search, multi-tile mosaics, cloud mask, composites; MNDWI/NDMI/NDVI | `rmti.stac`, `rmti.indices` |
| xarray/Dask time series: water frequency, anomaly, trend, flood-from-series | `rmti.timeseries` |
| SAR flood mapping (Sentinel-1) | `rmti.sar` |
| Google Earth Engine backend (optical + SAR) | `rmti.gee` |
| Pixel-wise (block-wise) and zonal risk; COG export | `rmti.raster_risk` |
| AOI → imagery → score → map workflows | `rmti.pipeline` |
| Budgeted project selection (MILP, exclusive packages) | `rmti.optimizer` |
| HCC: ALBI, registry triage, access-to-surveillance exposure | `rmti.domains.hcc`, `hcc_geo` |

## Read before using
* The evidence-grade → variance mapping in `stochastic` is an **assumption**; tier probabilities depend on it.
* Imagery and GIS remove arithmetic subjectivity, **not** analyst judgement (hazard layer, thresholds, L, V, ρ).
* Optimisation sums ΔR across assets and relies on scenario ρ_after values.
* Live services (STAC, Planetary Computer, Earth Engine) were **not** run in the build sandbox; see the verification table in `docs/geospatial-satellite.md`.
* Problems found in the source papers/archives while building this: `docs/FINDINGS.md`.
* Deployment (GitHub, Streamlit Cloud, API, PyPI): `docs/deployment.md`.

Apache-2.0 · cite via `CITATION.cff`.
