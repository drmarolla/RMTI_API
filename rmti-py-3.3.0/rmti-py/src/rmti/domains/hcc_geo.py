# Copyright 2025-2026 Cesar Marolla. Apache-2.0.
"""Spatial HCC-surveillance analytics: the oncology counterpart of the urban geospatial pipeline.

There is no satellite component for HCC. The spatial analogue of the hazard footprint is the
*surveillance footprint*: E = share of the at-risk population that lies within reach of a
surveillance-capable centre (the preprint's definition of E). Here "reach" is a straight-line
radius around each centre, which ignores roads, transit and referral rules; replace it with
travel-time isochrones for real planning. Research prototype; not a medical device.

Requires:  pip install "rmti-py[geo]"
"""
from __future__ import annotations

from typing import Optional

import numpy as np

from ..core import C_INFRA, TIER_LABELS
from ..geospatial import _union, raster_sum
from ..raster_risk import risk_arrays
from .hcc import C_LEVEL, RHO

# Published ladder anchors (uptake / completion -> rho). Interpolating between them is an ASSUMPTION
# made by this library, not a result of the preprint; prefer an explicit rho per zone when you have one.
_UPTAKE_ANCHORS = ([0.18, 0.45, 0.52], [0.15, 0.45, 0.50])


def rho_from_uptake(uptake):
    """Piecewise-linear interpolation of rho on the ladder anchors (clipped to 0.15..0.50)."""
    return np.interp(np.asarray(uptake, dtype=float), *_UPTAKE_ANCHORS)


def surveillance_footprint(centers, radius_km: float):
    """Union of circles of ``radius_km`` around centres (GeoDataFrame, EPSG of the input)."""
    import geopandas as gpd
    utm = centers.estimate_utm_crs()
    geom = _union(gpd.GeoDataFrame(geometry=centers.to_crs(utm).buffer(radius_km * 1000.0), crs=utm))
    return gpd.GeoDataFrame(geometry=[geom], crs=utm).to_crs(centers.crs)


def access_exposure(zones, centers, radius_km: float, at_risk_raster: str, all_touched: bool = False):
    """E per zone = at-risk persons inside (zone ∩ footprint) / at-risk persons in zone, from a count raster.
    Adds columns ``at_risk_raster_sum`` and ``E`` (NaN where a zone has no at-risk population)."""
    import geopandas as gpd
    import rasterio
    with rasterio.open(at_risk_raster) as s:
        rcrs = s.crs
    foot = surveillance_footprint(centers, radius_km).to_crs(rcrs).geometry.iloc[0]
    z = zones.to_crs(rcrs).copy()
    tot, cov = [], []
    for geom in z.geometry:
        g = gpd.GeoDataFrame(geometry=[geom], crs=rcrs)
        t = raster_sum(g, at_risk_raster, all_touched)
        inter = geom.intersection(foot)
        c = 0.0 if inter.is_empty else raster_sum(gpd.GeoDataFrame(geometry=[inter], crs=rcrs), at_risk_raster, all_touched)
        tot.append(t)
        cov.append(c)
    tot, cov = np.array(tot), np.array(cov)
    z["at_risk_raster_sum"] = tot
    z["E"] = np.where(tot > 0, cov / np.where(tot > 0, tot, 1), np.nan)
    return zones.assign(at_risk_raster_sum=tot, E=z["E"].to_numpy())


def score_zones(zones, L="L", V="V", rho="rho", E="E", C: str = "C-D", rho_after: Optional[float] = None):
    """Zone-level R, tier and EAL. Each of L/V/rho/E is a column name or a constant. ``C`` is the BCLC stage
    key assumed if a tumour is missed. Optional ``rho_after`` scores a scenario (e.g. optimised programme 0.65)."""
    def col(x):
        return zones[x].to_numpy("float32") if isinstance(x, str) else np.float32(x)
    Lc, Ec, Vc, rc = col(L), col(E), col(V), col(rho)
    R, t = risk_arrays(Lc, Ec, Vc, rc)
    out = zones.copy()
    out["R"], out["tier_n"] = R, t
    out["tier"] = [TIER_LABELS[i - 1] if i else None for i in t]
    out["EAL"] = np.where(np.isnan(R), np.nan, Lc * C_INFRA[C_LEVEL[C]] * (1 - rc))
    if rho_after is not None:
        R2, t2 = risk_arrays(Lc, Ec, Vc, np.float32(rho_after))
        out["R_after"] = R2
        out["tier_after"] = [TIER_LABELS[i - 1] if i else None for i in t2]
    return out
