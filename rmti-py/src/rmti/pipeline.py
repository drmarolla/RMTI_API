# Copyright 2025-2026 Cesar Marolla. Apache-2.0.
"""End-to-end area-of-interest workflows (AOI -> imagery -> exposure -> score -> map/COG).

    flood_run    surface-water hazard footprint (MNDWI, or pre/post difference) -> E_sel, E_pop -> R, tier, map
    dryness_run  NDMI-based fuel-dryness V raster -> pixel-wise R and tier COGs -> map

Both accept pre-built ``BandStack`` objects (from ``rmti.stac.fetch_bands`` or ``bandstack_from_tif``),
so they run offline. L, V (flood) / L, E, rho (dryness) and rho_after remain ANALYST INPUTS: imagery
informs the hazard footprint or a vulnerability proxy; it does not replace judgement about likelihood
or resilience. Index-derived proxies (MNDWI, NDMI) are screening tools, not hazard models.
Requires:  pip install "rmti-py[geo,viz]"
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from . import indices, sar
from .core import TIER_LABELS, score
from .geospatial import ExposureResult, compute_e_sel_by_zone, compute_spatial_exposure, mask_to_polygons
from .raster_risk import cogify, risk_arrays, risk_raster, tier_histogram, write_cog, zonal_risk


def _gdf(x):
    import geopandas as gpd
    return gpd.read_file(x) if isinstance(x, (str, os.PathLike)) else x


@dataclass
class RunResult:
    summary: dict
    outputs: dict = field(default_factory=dict)
    hazard: object = None
    zones: object = None
    exposure: Optional[ExposureResult] = None


def _finish(res: RunResult, out_dir: str, map_kwargs: dict, write_map: bool):
    path = os.path.join(out_dir, "summary.json")
    with open(path, "w") as f:
        json.dump(res.summary, f, indent=2, default=str)
    res.outputs["summary"] = path
    if write_map:
        from .webmap import risk_map
        m = risk_map(**map_kwargs)
        p = os.path.join(out_dir, "map.html")
        m.save(p)
        res.outputs["map"] = p
    return res


def flood_run(aoi, assets, population_raster: str, out_dir: str, *, post=None, pre=None, hazard=None,
              sar_post=None, sar_pre=None, sar_pol: str = "vv", sar_water_db: float = -15.0,
              sar_change_db: float = -3.0, sar_exclude=None, speckle_size: int = 5, min_pixels: int = 4,
              L: float, V: float, rho: float, C: int = 5, rho_after: Optional[float] = None,
              weight_col: Optional[str] = None, zones=None, mndwi_threshold: float = 0.0,
              min_area_m2: float = 0.0, write_map: bool = True) -> RunResult:
    os.makedirs(out_dir, exist_ok=True)
    aoi, assets = _gdf(aoi), _gdf(assets)
    out, source = {}, "supplied hazard layer"
    if hazard is None and sar_post is not None:
        if sar_pre is None:
            raise ValueError("SAR flood mapping needs both sar_pre and sar_post (change detection)")
        pre_db = sar.lee_filter_db(sar_pre.bands[sar_pol], speckle_size)
        post_db = sar.lee_filter_db(sar_post.bands[sar_pol], speckle_size)
        wm = sar.flood_from_change(pre_db, post_db, sar_water_db, sar_change_db, sar_exclude, min_pixels)
        source = (f"SAR {sar_pol.upper()} change detection (post < {sar_water_db} dB and change < {sar_change_db} dB, "
                  f"Lee {speckle_size}px)")
        hazard = mask_to_polygons(wm, sar_post.transform, sar_post.crs)
        if len(hazard) == 0:
            raise ValueError("no flood pixels detected from SAR; check thresholds, dates and orbit geometry")
    elif hazard is None:
        if post is None:
            raise ValueError("supply `hazard` (polygons), `post` optical imagery (green, swir1) or `sar_pre`+`sar_post`")
        mn = indices.mndwi(post.bands["green"], post.bands["swir1"])
        wm = indices.water_mask(mn, mndwi_threshold)
        source = f"MNDWI > {mndwi_threshold} (post)"
        if pre is not None:
            wm = indices.new_water(indices.water_mask(indices.mndwi(pre.bands["green"], pre.bands["swir1"]), mndwi_threshold), wm)
            source = f"new water: MNDWI > {mndwi_threshold} post minus pre"
        raw = os.path.join(out_dir, "_mndwi.tif")
        import rasterio
        with rasterio.open(raw, "w", driver="GTiff", height=mn.shape[0], width=mn.shape[1], count=1, dtype="float32",
                           crs=post.crs, transform=post.transform, nodata=np.nan) as d:
            d.write(mn, 1)
        out["mndwi_cog"] = cogify(raw, os.path.join(out_dir, "mndwi.tif"))
        os.remove(raw)
        hazard = mask_to_polygons(wm, post.transform, post.crs, min_area_m2)
        if len(hazard) == 0:
            raise ValueError("no hazard pixels detected; check threshold, dates and imagery")
    else:
        hazard = _gdf(hazard)
    hp = os.path.join(out_dir, "hazard.geojson")
    hazard.to_crs(4326).to_file(hp, driver="GeoJSON")
    out["hazard"] = hp

    exp = compute_spatial_exposure(assets, hazard, aoi, population_raster, weight_col)
    now = score(L, exp.E_sel, V, rho, C)
    summ = {"hazard_source": source, "exposure": exp.__dict__, "inputs": dict(L=L, V=V, rho=rho, C=C),
            "R": now["R"], "tier": now["tier"], "EAL": now["EAL"]}
    if rho_after is not None:
        aft = score(L, exp.E_sel, V, rho_after, C)
        summ.update(R_after=aft["R"], tier_after=aft["tier"])
    res = RunResult(summ, out, hazard, None, exp)
    zr = None
    if zones is not None:
        zr = compute_e_sel_by_zone(assets, hazard, _gdf(zones), weight_col)
        zr = zonal_risk(zr, L, "E_sel", V, rho)
        zp = os.path.join(out_dir, "zones_scored.geojson")
        zr.to_crs(4326).to_file(zp, driver="GeoJSON")
        out["zones"] = zp
        res.zones = zr
    return _finish(res, out_dir, dict(zones=zr, hazard=hazard, assets=assets), write_map)


def dryness_run(bands, out_dir: str, *, L, E, rho, ndmi_lo: float = -0.2, ndmi_hi: float = 0.4,
                zones=None, write_map: bool = True) -> RunResult:
    """Pixel-wise R with V = NDMI-based dryness. L, E, rho: constants or raster paths on the same grid."""
    import rasterio
    os.makedirs(out_dir, exist_ok=True)
    v = indices.fuel_dryness(indices.ndmi(bands.bands["nir"], bands.bands["swir1"]), ndmi_lo, ndmi_hi)
    vp = os.path.join(out_dir, "V_dryness.tif")
    write_cog(v, vp, bands.transform, bands.crs, nodata=float("nan"))
    rp, tp = os.path.join(out_dir, "_R.tif"), os.path.join(out_dir, "_tier.tif")
    risk_raster({"L": L, "E": E, "V": vp, "rho": rho}, rp, tp)
    outs = {"V": vp, "R": cogify(rp, os.path.join(out_dir, "R.tif")), "tier": cogify(tp, os.path.join(out_dir, "tier.tif"))}
    hist = tier_histogram(tp)
    for t in (rp, tp):
        os.remove(t)
    zr = None
    if zones is not None:
        zr = zonal_risk(_gdf(zones), L if not isinstance(L, str) else "L", E if not isinstance(E, str) else "E",
                        "V", rho if not isinstance(rho, str) else "rho", layer_paths={"V": vp})
    summ = {"V_source": f"1 - scale(NDMI, {ndmi_lo}, {ndmi_hi}) (assumed anchors)", "tier_share": hist,
            "n_scenes": bands.n_scenes}
    res = RunResult(summ, outs, None, zr)
    return _finish(res, out_dir, dict(zones=zr, tier_raster=outs["tier"]), write_map)
