# Geospatial and satellite workflow (urban)

```
AOI ─► STAC search ─► bands (scaled, cloud-masked, median) ─► index (MNDWI / NDMI) ─► hazard polygons or V raster
                                                                   │
      assets + population raster ─► E_sel, E_pop, N ◄──────────────┘
                                         │
      analyst inputs L, V, ρ ────────────┴──► R, tier ─► zones / COG rasters / HTML map
```
## Pieces
| Function | Does |
|---|---|
| `stac.search_items(aoi, start, end)` | Query a STAC API (default AWS Earth Search; Sentinel-2 L2A, Landsat C2 L2) |
| `stac.fetch_bands(items, aoi, names)` | Windowed COG reads, scale/offset from asset metadata, SCL/QA cloud mask, median composite (one tile/grid) |
| `stac.bandstack_from_tif` | Offline alternative: load a multiband GeoTIFF |
| `indices.*` | NDVI, NDWI, MNDWI, NDMI, NBR, SAVI; `scale_linear` with **fixed** anchors |
| `geospatial.compute_spatial_exposure` | N, E_log, E_sel (assets in hazard), E_pop (people in hazard) |
| `geospatial.compute_e_sel_by_zone` | E_sel per tract/ward |
| `raster_risk.risk_raster` | Block-wise pixel R and tier (bounded memory); `cogify`, `align_raster`, `tier_histogram`, `zonal_risk` |
| `webmap.risk_map` | Folium map: satellite basemap, tier overlay, zones, hazard, assets |
| `pipeline.flood_run / dryness_run` | The whole loop, writing GeoJSON, COGs, `summary.json`, `map.html` |

```python
from rmti.stac import search_items, fetch_bands
from rmti.pipeline import flood_run
items = search_items(aoi_gdf, "2026-09-01", "2026-09-30", max_cloud=20)
post = fetch_bands(items[:8], aoi_gdf, names=("green", "swir1"))
res = flood_run(aoi_gdf, assets_gdf, "worldpop.tif", "out/", post=post, L=0.9, V=0.8, rho=0.2, rho_after=0.55)
```

## Multi-tile mosaics
`fetch_bands` / `fetch_timeseries` / `fetch_sar` warp **every** scene onto one AOI grid (`target_grid`: the AOI's UTM zone by default, resolution in metres,
default 10 m Sentinel / 30 m Landsat; a 40-million-pixel guard prevents accidental continent-sized grids). Scenes are NaN outside their footprint, so
adjacent MGRS tiles, even in different UTM zones, merge in the composite. Failed scenes appear in `BandStack.skipped`.

## Time series (xarray + Dask)
```python
from rmti.stac import fetch_timeseries
from rmti import timeseries as ts
ds = fetch_timeseries(items, aoi, names=("green", "nir", "swir1"), lazy=True)   # Dask-backed, nothing read yet
ds = ts.add_index(ds, "mndwi")
new = ts.new_water_from_series(ds["mndwi"], baseline=("2026-01-01", "2026-06-30"), event=("2026-09-10", "2026-09-30")).compute()
freq = ts.water_frequency(ds["mndwi"])            # flood-prone vs permanent water
z = ts.climatology_anomaly(ts.add_index(ds, "ndmi")["ndmi"], ("2025-01-01", "2025-12-31"))   # dryness vs. baseline
slope = ts.trend(ds["mndwi"])                     # per-pixel slope per year
```
Same-day scenes are mosaicked into one time step. `ts.to_bandstack(ds, "median", start, end)` feeds `flood_run` / `dryness_run`.

## SAR flood mapping
```python
from rmti.stac import search_items, fetch_sar, PLANETARY
import planetary_computer                              # pip install "rmti-py[pc]"
items_pre = search_items(aoi, "2026-08-01", "2026-08-31", "sentinel-1-rtc", max_cloud=None, endpoint=PLANETARY, modifier=planetary_computer.sign_inplace)
items_post = search_items(aoi, "2026-09-10", "2026-09-25", "sentinel-1-rtc", max_cloud=None, endpoint=PLANETARY, modifier=planetary_computer.sign_inplace)
res = flood_run(aoi, assets, pop_raster, "out/", sar_pre=fetch_sar(items_pre, aoi), sar_post=fetch_sar(items_post, aoi),
                L=0.9, V=0.8, rho=0.2, rho_after=0.55)
```
Method: Lee speckle filter → dark now (< −15 dB) **and** ≥ 3 dB darker than before **and** not already water. Keep the same orbit direction for pre/post.
`rmti.sar` also has `otsu_threshold`, `water_mask_sar`, `lee_filter_db`. **Limits:** flooded buildings and flooded vegetation often get *brighter*
(double-bounce), so urban and forest inundation is under-detected; wind-roughened water, radar shadow and smooth surfaces give false positives; mask steep
terrain via `sar_exclude` (a DEM/HAND layer is not bundled). Thresholds are scene-dependent.

## Google Earth Engine
```python
from rmti import gee
gee.init(project="my-cloud-project", authenticate=True)          # once; servers: service_account= + key_file=
post = gee.fetch_bands_gee(aoi, "2026-09-10", "2026-09-30", ("green", "swir1"), collection="sentinel-2", scale=10)
sar_post = gee.fetch_sar_gee(aoi, "2026-09-10", "2026-09-25", orbit="DESCENDING")
```
Compositing and cloud masking run on Google's servers; only the finished composite (≤ ~32 MB per request) is downloaded. For larger areas tile the AOI or use `ee.batch.Export`.
Check Google's terms (commercial use needs a commercial EE licence).

## Verification status (be explicit about what was and was not tested)
| Feature | Tested how |
|---|---|
| Mosaics, grids, scale/offset, cloud masks, time series, Dask laziness, SAR algorithms, pipelines | automated tests on local GeoTIFFs and synthetic data |
| STAC search (`search_items`), Planetary Computer signing, reading remote COGs | **not run live** (no network in the build sandbox) |
| Earth Engine (`rmti.gee`) | **mocked only**: tests check our call logic; the `ee` function names exist in earthengine-api 1.7, but no real EE request was made |
| SAR thresholds on real Sentinel-1 | **not validated**; the −15 dB / −3 dB defaults are conventional starting points |

## General limits
* **Imagery does not replace judgement.** L, V (flood), E and ρ stay analyst inputs; hazard layer, dates, thresholds and anchors move the answer: record them.
* **MNDWI finds open water, not flood hazard**; NDMI dryness is not a fire-danger model; default anchors (−0.2…0.4) are assumptions.
* Population rasters must be **counts per cell**.
* Not implemented: hydrodynamic flood modelling, DEM/HAND derivation, machine-learning classifiers.
