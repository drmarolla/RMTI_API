# Copyright 2025-2026 Cesar Marolla. Apache-2.0.
"""Pixel-wise and zone-wise RMTI on rasters, with block-wise processing (bounded memory).

Memory: ``risk_raster`` streams one raster block at a time, so file size is not
limited by RAM. (Dask/xarray are not used; plain rasterio windows suffice here.)
Inputs must share one grid; use ``align_raster`` to resample onto a template.
"""
from __future__ import annotations

from typing import Dict, Mapping, Optional, Union

import numpy as np

from .core import TIER_LABELS, tier_index

Layer = Union[float, int, str]            # constant or path to a single-band raster
FIELDS = ("L", "E", "V", "rho")


def risk_arrays(L, E, V, rho):
    """Broadcast Eq. (1)/(2). Returns (R float32 with NaN where any input is NaN, tier uint8 1..5, 0 = nodata)."""
    L, E, V, rho = np.broadcast_arrays(*(np.asarray(x, dtype="float32") for x in (L, E, V, rho)))
    bad = ~(np.isfinite(L) & np.isfinite(E) & np.isfinite(V) & np.isfinite(rho))
    for n, a in zip(FIELDS, (L, E, V, rho)):
        if np.nanmin(np.where(bad, 0, a)) < 0 or np.nanmax(np.where(bad, 0, a)) > 1:
            raise ValueError(f"{n} must lie in [0, 1]")
    R = L * E * V * (1 - rho)
    R = np.where(bad, np.nan, R).astype("float32")
    t = np.where(bad, 0, tier_index(np.where(bad, 0, R)) + 1).astype("uint8")
    return R, t


def align_raster(src_path: str, template_path: str, out_path: str, resampling: str = "bilinear") -> str:
    """Resample/reproject ``src_path`` onto the grid of ``template_path``."""
    import rasterio
    from rasterio.enums import Resampling
    from rasterio.warp import reproject
    with rasterio.open(template_path) as t, rasterio.open(src_path) as s:
        prof = t.profile.copy()
        prof.update(count=1, dtype="float32", nodata=np.nan, driver="GTiff", compress="deflate")
        dst = np.full((t.height, t.width), np.nan, dtype="float32")
        reproject(rasterio.band(s, 1), dst, src_nodata=s.nodata, dst_transform=t.transform, dst_crs=t.crs,
                  dst_nodata=np.nan, resampling=getattr(Resampling, resampling))
        with rasterio.open(out_path, "w", **prof) as o:
            o.write(dst, 1)
    return out_path


def write_cog(array: np.ndarray, path: str, transform, crs, nodata=None, resampling: str = "nearest") -> str:
    """Write a single-band Cloud-Optimised GeoTIFF (GDAL COG driver; falls back to tiled GTiff + overviews)."""
    import rasterio
    from rasterio.enums import Resampling
    prof = dict(driver="GTiff", height=array.shape[0], width=array.shape[1], count=1, dtype=array.dtype,
                crs=crs, transform=transform, nodata=nodata)
    try:
        from rasterio.env import Env
        with Env() as env:
            has_cog = "COG" in env.drivers()
        if not has_cog:
            raise RuntimeError
        with rasterio.open(path, "w", **{**prof, "driver": "COG", "compress": "deflate"}) as dst:
            dst.write(array, 1)
    except Exception:
        with rasterio.open(path, "w", **{**prof, "tiled": True, "blockxsize": 256, "blockysize": 256,
                                         "compress": "deflate"}) as dst:
            dst.write(array, 1)
            dst.build_overviews([2, 4, 8], getattr(Resampling, resampling))
    return path


def cogify(src_path: str, dst_path: str) -> str:
    """Stream-copy any raster into a Cloud-Optimised GeoTIFF (falls back to a tiled GeoTIFF with overviews)."""
    import rasterio
    import rasterio.shutil
    try:
        rasterio.shutil.copy(src_path, dst_path, driver="COG", compress="deflate")
    except Exception:
        rasterio.shutil.copy(src_path, dst_path, driver="GTiff", tiled=True, compress="deflate")
        with rasterio.open(dst_path, "r+") as d:
            from rasterio.enums import Resampling
            d.build_overviews([2, 4, 8], Resampling.nearest)
    return dst_path


def risk_raster(layers: Mapping[str, Layer], out_R: str, out_tier: Optional[str] = None) -> Dict[str, str]:
    """Pixel-wise RMTI over rasters. ``layers`` maps L, E, V, rho to a constant or a raster path; at least
    one must be a path (it defines the grid). Processes block-by-block and writes GeoTIFFs (R float32, tier uint8)."""
    import rasterio
    missing = set(FIELDS) - set(layers)
    if missing:
        raise ValueError(f"layers missing: {sorted(missing)}")
    paths = {k: v for k, v in layers.items() if isinstance(v, str)}
    if not paths:
        raise ValueError("need at least one raster layer to define the grid")
    srcs = {k: rasterio.open(p) for k, p in paths.items()}
    try:
        ref = next(iter(srcs.values()))
        for k, s in srcs.items():
            if (s.height, s.width, s.transform, s.crs) != (ref.height, ref.width, ref.transform, ref.crs):
                raise ValueError(f"layer {k!r} is not on the same grid; use align_raster()")
        prof = ref.profile.copy()
        prof.update(count=1, dtype="float32", nodata=np.nan, compress="deflate", tiled=True,
                    blockxsize=256, blockysize=256, driver="GTiff")
        tprof = {**prof, "dtype": "uint8", "nodata": 0}
        with rasterio.open(out_R, "w", **prof) as dR, \
                (rasterio.open(out_tier, "w", **tprof) if out_tier else _Null()) as dT:
            for _, win in ref.block_windows(1):
                vals = {}
                for k in FIELDS:
                    if k in srcs:
                        a = srcs[k].read(1, window=win, masked=True).astype("float32").filled(np.nan)
                    else:
                        a = np.float32(layers[k])
                    vals[k] = a
                R, t = risk_arrays(vals["L"], vals["E"], vals["V"], vals["rho"])
                dR.write(R, 1, window=win)
                if out_tier:
                    dT.write(t, 1, window=win)
    finally:
        for s in srcs.values():
            s.close()
    return {"R": out_R, **({"tier": out_tier} if out_tier else {})}


class _Null:
    def __enter__(self): return self
    def __exit__(self, *a): return False


def tier_histogram(tier_path: str) -> Dict[str, float]:
    """Share of valid pixels in each tier (block-wise)."""
    import rasterio
    counts = np.zeros(6, dtype="int64")
    with rasterio.open(tier_path) as s:
        for _, win in s.block_windows(1):
            counts += np.bincount(s.read(1, window=win).ravel(), minlength=6)
    valid = counts[1:].sum()
    return {TIER_LABELS[i]: (counts[i + 1] / valid if valid else 0.0) for i in range(5)}


def zonal_layer_means(zones, layer_paths: Mapping[str, str], all_touched: bool = False):
    """Mean of each raster per zone (GeoDataFrame in, same GeoDataFrame + columns out)."""
    import rasterio
    from rasterstats import zonal_stats
    out = zones.copy()
    for name, p in layer_paths.items():
        with rasterio.open(p) as s:
            crs, nd = s.crs, s.nodata
        st = zonal_stats(zones.to_crs(crs), p, stats=["mean"], nodata=nd, all_touched=all_touched)
        out[name] = [r["mean"] if r["mean"] is not None else np.nan for r in st]
    return out


def zonal_risk(zones, L, E, V, rho, layer_paths: Optional[Mapping[str, str]] = None,
               all_touched: bool = False):
    """Zone-level RMTI. Each of L/E/V/rho is a constant, a column name already in ``zones``, or a key of
    ``layer_paths`` (zonal mean is taken). Adds R and tier columns."""
    z = zonal_layer_means(zones, layer_paths or {}, all_touched) if layer_paths else zones.copy()
    spec = dict(L=L, E=E, V=V, rho=rho)
    vals = {}
    for k, v in spec.items():
        vals[k] = z[v].to_numpy(dtype="float32") if isinstance(v, str) else np.float32(v)
    R, t = risk_arrays(vals["L"], vals["E"], vals["V"], vals["rho"])
    z["R"] = R
    z["tier"] = [TIER_LABELS[i - 1] if i > 0 else None for i in t]
    z["tier_n"] = t
    return z
