# Copyright 2025-2026 Cesar Marolla. Apache-2.0.
"""Spatial derivation of E_sel and population N from GIS layers and rasters.

Requires the optional dependencies:  pip install "rmti-py[geo]"

What this does and does not do
------------------------------
It replaces *hand arithmetic* on E_sel with a reproducible spatial
calculation. It does NOT remove analyst judgement: which hazard layer (model,
return period, climate scenario), which asset registry and which population
raster are used remain choices that move the result, and they should be
recorded alongside the output.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from .core import N_MIN, e_log_clipped


def _require():
    try:
        import geopandas as gpd  # noqa: F401
        import rasterio  # noqa: F401
        from rasterstats import zonal_stats  # noqa: F401
    except ImportError as exc:  # pragma: no cover
        raise ImportError('geospatial features need: pip install "rmti-py[geo]"') from exc


def _metric_crs(gdf):
    if gdf.crs is None:
        raise ValueError("input layer has no CRS; set one before calling")
    return gdf.estimate_utm_crs() if gdf.crs.is_geographic else gdf.crs


def _union(gdf):
    return gdf.geometry.union_all() if hasattr(gdf.geometry, "union_all") else gdf.geometry.unary_union


@dataclass(frozen=True)
class ExposureResult:
    N: int                      # population in the jurisdiction (raster sum)
    N_exposed: int              # population inside hazard footprint ∩ jurisdiction
    E_log: float                # advisory Eq. (4), clipped to [0, 1]
    E_sel: float                # weighted share of assets inside the footprint
    E_pop: float                # N_exposed / N
    n_assets: int


def asset_exposure_fractions(assets, hazard):
    """Per-asset exposed fraction in [0, 1]: points 0/1, lines by length, polygons by area (vectorised).
    Overlapping hazard polygons are dissolved first so nothing is double counted."""
    _require()
    crs = _metric_crs(assets)
    a = assets.to_crs(crs)
    footprint = _union(hazard.to_crs(crs))
    g = a.geometry
    inter = g.intersection(footprint)
    kinds = a.geom_type.to_numpy().astype(str)
    is_pt = np.char.find(kinds, "Point") >= 0
    is_ln = np.char.find(kinds, "Line") >= 0
    with np.errstate(divide="ignore", invalid="ignore"):
        ln = np.where(g.length.to_numpy() > 0, inter.length.to_numpy() / g.length.to_numpy(), 0.0)
        pg = np.where(g.area.to_numpy() > 0, inter.area.to_numpy() / g.area.to_numpy(), 0.0)
    pt = (~inter.is_empty.to_numpy()).astype(float)
    frac = np.where(is_pt, pt, np.where(is_ln, ln, pg))
    return np.clip(frac, 0.0, 1.0), a


def compute_e_sel(assets, hazard, weight_col: Optional[str] = None) -> float:
    """E_sel = sum_i w_i f_i / sum_i w_i.

    w_i defaults to length (lines) or area (polygons) when the layer has a single
    geometry family; for points, or for mixed layers, pass ``weight_col``
    (e.g. replacement value or users served)."""
    frac, a = asset_exposure_fractions(assets, hazard)
    if weight_col is not None:
        w = a[weight_col].to_numpy(dtype=float)
    else:
        fam = {("point" if "Point" in k else "line" if "Line" in k else "poly") for k in a.geom_type}
        if len(fam) != 1 or fam == {"point"}:
            raise ValueError("mixed or point-only asset layers need weight_col (value, users served, ...)")
        w = (a.length if fam == {"line"} else a.area).to_numpy(dtype=float)
    if np.any(w < 0) or w.sum() == 0:
        raise ValueError("asset weights must be non-negative with a positive sum")
    return float((w * frac).sum() / w.sum())


def raster_sum(polygons, raster_path: str, all_touched: bool = False) -> float:
    """Sum of raster cell values inside polygons, reprojecting polygons to the raster CRS."""
    _require()
    import rasterio
    from rasterstats import zonal_stats
    with rasterio.open(raster_path) as src:
        crs, nodata = src.crs, src.nodata
    g = polygons.to_crs(crs)
    stats = zonal_stats(g, raster_path, stats=["sum"], nodata=nodata, all_touched=all_touched)
    return float(sum((s["sum"] or 0.0) for s in stats))


def compute_spatial_exposure(assets, hazard, jurisdiction, population_raster: str,
                             weight_col: Optional[str] = None, all_touched: bool = False) -> ExposureResult:
    """Derive N, E_log, E_sel and the population-share exposure from GIS layers.

    Parameters are GeoDataFrames (any CRS, reprojected internally) and the path
    to a population-count raster (e.g. WorldPop; values must be persons per cell,
    not density).
    """
    _require()
    import geopandas as gpd
    import rasterio

    e_sel = compute_e_sel(assets, hazard, weight_col)
    with rasterio.open(population_raster) as src:
        rcrs = src.crs
    juris = jurisdiction.to_crs(rcrs)
    n_total = raster_sum(juris, population_raster, all_touched)
    exposed_geom = _union(hazard.to_crs(rcrs)).intersection(_union(juris))
    exposed = gpd.GeoDataFrame(geometry=[exposed_geom], crs=rcrs)
    n_exp = 0.0 if exposed_geom.is_empty else raster_sum(exposed, population_raster, all_touched)
    n_int = int(round(n_total))
    return ExposureResult(N=n_int, N_exposed=int(round(n_exp)),
                          E_log=round(float(e_log_clipped(max(n_int, N_MIN))), 3),
                          E_sel=round(e_sel, 3), E_pop=round(n_exp / n_total, 3) if n_total > 0 else 0.0,
                          n_assets=len(assets))


def compute_e_sel_by_zone(assets, hazard, zones, weight_col: Optional[str] = None, zone_id: Optional[str] = None):
    """E_sel per zone (tract, ward, district): assets are clipped to each zone first.
    Returns the zones GeoDataFrame with columns ``E_sel`` and ``n_assets`` (NaN if a zone has no assets)."""
    _require()
    import geopandas as gpd
    z = zones.to_crs(assets.crs).copy()
    e, n = [], []
    for geom in z.geometry:
        clip = gpd.clip(assets, geom)
        n.append(len(clip))
        try:
            e.append(compute_e_sel(clip, hazard, weight_col) if len(clip) else np.nan)
        except ValueError:
            e.append(np.nan)
    z["E_sel"], z["n_assets"] = e, n
    return z


def mask_to_polygons(mask: np.ndarray, transform, crs, min_area_m2: float = 0.0):
    """Vectorise a boolean raster mask (e.g. water or new-water) into a hazard-footprint GeoDataFrame."""
    _require()
    import geopandas as gpd
    from rasterio.features import shapes
    from shapely.geometry import shape
    geoms = [shape(g) for g, v in shapes(np.asarray(mask, dtype="uint8"), mask=np.asarray(mask, bool),
                                         transform=transform) if v == 1]
    gdf = gpd.GeoDataFrame(geometry=geoms, crs=crs)
    if min_area_m2 > 0 and len(gdf):
        keep = gdf.to_crs(gdf.estimate_utm_crs()).area >= min_area_m2
        gdf = gdf[keep.to_numpy()].reset_index(drop=True)
    return gdf
