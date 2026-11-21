# Changelog
## 3.2.0
- Multi-tile / multi-UTM-zone mosaics: every scene is warped onto one AOI grid (`stac.target_grid`, `read_on_grid`).
- xarray/Dask time series (`stac.fetch_timeseries`, lazy option) and `rmti.timeseries` (indices, water frequency,
  anomaly, trend, flood-from-series).
- SAR flood mapping (`rmti.sar`, `stac.fetch_sar`, `flood_run(sar_pre=, sar_post=)`).
- Google Earth Engine backend (`rmti.gee`): optical composites and Sentinel-1.
- Failed scenes are reported in `BandStack.skipped` instead of silently dropped.
## 3.1.0
- Satellite ingestion (STAC), spectral indices, pixel-wise and zonal RMTI on rasters, COG export, Folium maps.
- Area-of-interest pipelines (`flood_run`, `dryness_run`).
- Oncology: registry batch scoring (`hcc.score_table`), spatial surveillance-access exposure (`hcc_geo`).
- Streamlit app (`streamlit_app.py`) and REST API (`rmti.api`); bundled synthetic sample data.
## 3.0.0
- Package restructure: core, stochastic (Beta / Gaussian copula), geospatial, MILP optimiser, elasticity, urban and HCC domains.
