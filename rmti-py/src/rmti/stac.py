# Copyright 2025-2026 Cesar Marolla. Apache-2.0.
"""Satellite ingestion from STAC catalogues (default: AWS Earth Search, public COGs).

Requires:  pip install "rmti-py[sat]"

NOT live-tested in the development sandbox (no outbound network). The band-read,
scaling, masking and compositing code is tested offline against local GeoTIFFs
standing in for scene assets; verify the first real query on your machine.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence

import numpy as np

EARTH_SEARCH = "https://earth-search.aws.element84.com/v1"
PLANETARY = "https://planetarycomputer.microsoft.com/api/stac/v1"   # needs a signing modifier, see search_items
BAND_KEYS = {
    "sentinel-1-rtc": dict(vv="vv", vh="vh"),
    "sentinel-2-l2a": dict(green="green", red="red", nir="nir", swir1="swir16", swir2="swir22", qa="scl"),
    "landsat-c2-l2": dict(green="green", red="red", nir="nir08", swir1="swir16", swir2="swir22", qa="qa_pixel"),
}
SCL_BAD = (0, 1, 3, 8, 9, 10)          # nodata, saturated, shadow, cloud med/high, cirrus
DEFAULT_RES = {"sentinel-2-l2a": 10.0, "landsat-c2-l2": 30.0, "sentinel-1-rtc": 10.0}   # metres
MAX_PIXELS = 40_000_000                # per band per scene; guards against accidental continent-sized grids


@dataclass
class BandStack:
    bands: Dict[str, np.ndarray]
    transform: object
    crs: object
    n_scenes: int
    item_ids: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)       # "id: reason" for scenes that failed

    @property
    def shape(self):
        return next(iter(self.bands.values())).shape


def _need():
    try:
        import pystac_client  # noqa: F401
    except ImportError as exc:  # pragma: no cover
        raise ImportError('satellite search needs: pip install "rmti-py[sat]"') from exc


def search_items(aoi, start: str, end: str, collection: str = "sentinel-2-l2a", max_cloud: Optional[float] = 30.0,
                 endpoint: str = EARTH_SEARCH, limit: int = 50, modifier=None, query: Optional[dict] = None):
    """Query a STAC API. ``aoi`` is a GeoDataFrame (any CRS) or (minx, miny, maxx, maxy) in EPSG:4326.
    Returns items sorted by cloud cover (lowest first). For Planetary Computer pass
    ``endpoint=PLANETARY`` and ``modifier=planetary_computer.sign_inplace`` (pip install planetary-computer).
    ``max_cloud=None`` skips the cloud filter (use it for radar). Items are not de-duplicated across tiles."""
    _need()
    from pystac_client import Client
    bbox = tuple(as_gdf(aoi).to_crs(4326).total_bounds)
    q = dict(query or {})
    if max_cloud is not None:
        q["eo:cloud_cover"] = {"lt": max_cloud}
    search = Client.open(endpoint, modifier=modifier).search(collections=[collection], bbox=bbox,
                                                             datetime=f"{start}/{end}", query=q or None, max_items=limit)
    items = list(search.items())
    return sorted(items, key=lambda i: i.properties.get("eo:cloud_cover", 100))


def _asset(item, key):
    a = item.assets[key]
    return getattr(a, "href", a)


def _scale_offset(item, key, default=(1e-4, 0.0)):
    a = item.assets[key]
    ex = getattr(a, "extra_fields", {}) or {}
    rb = (ex.get("raster:bands") or [{}])[0]
    return rb.get("scale", default[0]), rb.get("offset", default[1])


def as_gdf(aoi):
    """Accept a GeoDataFrame, a shapely geometry (assumed EPSG:4326) or a (minx, miny, maxx, maxy) tuple in EPSG:4326."""
    import geopandas as gpd
    from shapely.geometry import box
    from shapely.geometry.base import BaseGeometry
    if hasattr(aoi, "to_crs"):
        return aoi
    if isinstance(aoi, BaseGeometry):
        return gpd.GeoDataFrame(geometry=[aoi], crs=4326)
    return gpd.GeoDataFrame(geometry=[box(*aoi)], crs=4326)


def target_grid(aoi, crs=None, resolution: float = 10.0, max_pixels: int = MAX_PIXELS):
    """Common output grid for the AOI: (crs, affine transform, height, width). ``crs`` defaults to the AOI's UTM zone,
    ``resolution`` is in that CRS's units (metres for UTM). Every scene is warped onto this grid, so tiles from
    different MGRS squares or UTM zones mosaic cleanly."""
    from rasterio.crs import CRS
    from rasterio.transform import from_origin
    a = as_gdf(aoi)
    crs = CRS.from_user_input(crs if crs is not None else a.estimate_utm_crs())
    minx, miny, maxx, maxy = a.to_crs(crs).total_bounds
    minx, maxy = np.floor(minx / resolution) * resolution, np.ceil(maxy / resolution) * resolution
    w = int(np.ceil((maxx - minx) / resolution))
    h = int(np.ceil((maxy - (np.floor(miny / resolution) * resolution)) / resolution))
    if w * h > max_pixels:
        raise ValueError(f"grid {w}x{h} exceeds {max_pixels:,} pixels; use a coarser resolution or a smaller AOI")
    return crs, from_origin(minx, maxy, resolution, resolution), h, w


def read_on_grid(href: str, crs, transform, height: int, width: int, resampling: str = "bilinear"):
    """Read a raster (local or remote COG) warped onto the target grid. Returns float32, NaN where the source
    has no data or does not cover the pixel. Only the blocks overlapping the grid are fetched."""
    import rasterio
    from rasterio.enums import Resampling
    from rasterio.vrt import WarpedVRT
    with rasterio.open(href) as src:
        with WarpedVRT(src, crs=crs, transform=transform, width=width, height=height, add_alpha=True,
                       src_nodata=src.nodata, resampling=getattr(Resampling, resampling)) as vrt:
            data = vrt.read(1).astype("float32")
            valid = vrt.read(vrt.count) > 0
    return np.where(valid, data, np.nan)


def _scene_bands(it, keys, names, collection, grid, mask_clouds, default_so, resampling="bilinear"):
    crs, tr, h, w = grid
    layers = {}
    for n in names:
        arr = read_on_grid(_asset(it, keys[n]), crs, tr, h, w, resampling)
        sc, off = _scale_offset(it, keys[n], default_so)
        layers[n] = arr * sc + off
    bad = np.zeros((h, w), bool)
    qa_key = keys.get("qa")
    if mask_clouds and qa_key and qa_key in getattr(it, "assets", {}):
        q = read_on_grid(_asset(it, qa_key), crs, tr, h, w, "nearest")
        if collection == "sentinel-2-l2a":
            bad = np.isnan(q) | np.isin(np.nan_to_num(q, nan=0).astype(int), SCL_BAD)
        else:
            qi = np.nan_to_num(q, nan=0).astype(int)
            bad = np.isnan(q) | ((qi >> 1 & 1) | (qi >> 3 & 1) | (qi >> 4 & 1)).astype(bool)
    for n in names:
        layers[n][bad] = np.nan
    return layers


def _composite(stack, how):
    red = {"median": np.nanmedian, "mean": np.nanmean, "max": np.nanmax, "min": np.nanmin}[how]
    with np.errstate(all="ignore"):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            return red(np.stack(stack), axis=0).astype("float32")


def fetch_bands(items: Sequence, aoi, names: Iterable[str] = ("green", "nir", "swir1"),
                collection: str = "sentinel-2-l2a", mask_clouds: bool = True, composite: str = "median",
                crs=None, resolution: Optional[float] = None) -> BandStack:
    """Read bands for ALL given scenes onto one AOI grid (multi-tile and multi-zone safe), apply scale/offset and
    cloud masking, and reduce over time. Because each scene is NaN outside its footprint, overlapping and adjacent
    tiles are mosaicked by the composite itself. Failed scenes are listed in ``BandStack.skipped``."""
    keys, names = BAND_KEYS[collection], list(names)
    res = resolution or DEFAULT_RES[collection]
    grid = target_grid(aoi, crs, res)
    default_so = (1.0, 0.0) if collection == "sentinel-1-rtc" else (1e-4, 0.0)
    stacks: Dict[str, list] = {n: [] for n in names}
    ids, skipped = [], []
    for it in items:
        try:
            layers = _scene_bands(it, keys, names, collection, grid, mask_clouds, default_so)
        except Exception as exc:                          # a broken asset must not kill the batch
            skipped.append(f"{getattr(it, 'id', '?')}: {exc}")
            continue
        for n in names:
            stacks[n].append(layers[n])
        ids.append(getattr(it, "id", str(len(ids))))
    if not ids:
        raise RuntimeError("no usable scenes (check AOI, dates, cloud filter, network). " + "; ".join(skipped[:3]))
    out = {n: _composite(v, composite) for n, v in stacks.items()}
    return BandStack(out, grid[1], grid[0], len(ids), ids, skipped)


def _item_date(it):
    import datetime as dt
    d = getattr(it, "datetime", None)
    if d is None:
        d = (getattr(it, "properties", {}) or {}).get("datetime")
    if isinstance(d, str):
        d = dt.datetime.fromisoformat(d.replace("Z", "+00:00"))
    if d is None:
        raise ValueError(f"item {getattr(it, 'id', '?')} has no datetime")
    return np.datetime64(d.replace(tzinfo=None), "D")


def fetch_timeseries(items: Sequence, aoi, names: Iterable[str] = ("green", "nir", "swir1"),
                     collection: str = "sentinel-2-l2a", mask_clouds: bool = True, crs=None,
                     resolution: Optional[float] = None, lazy: bool = False):
    """Time series as an ``xarray.Dataset`` (dims time, y, x; one variable per band). Scenes from the same
    calendar day are mosaicked (median), so adjacent tiles form one time step. With ``lazy=True`` each time step
    is a Dask task (nothing is read until ``.compute()`` / ``.load()``), so long series need not fit in memory.
    Requires: pip install "rmti-py[sat]" (xarray; dask for lazy)."""
    import xarray as xr
    keys, names = BAND_KEYS[collection], list(names)
    grid = target_grid(aoi, crs, resolution or DEFAULT_RES[collection])
    crs_, tr, h, w = grid
    default_so = (1.0, 0.0) if collection == "sentinel-1-rtc" else (1e-4, 0.0)
    groups: Dict[np.datetime64, list] = {}
    for it in items:
        groups.setdefault(_item_date(it), []).append(it)
    dates = sorted(groups)
    if not dates:
        raise RuntimeError("no items")

    def load(group):
        per_band = {n: [] for n in names}
        for it in group:
            try:
                lay = _scene_bands(it, keys, names, collection, grid, mask_clouds, default_so)
            except Exception:
                continue
            for n in names:
                per_band[n].append(lay[n])
        return np.stack([_composite(per_band[n], "median") if per_band[n] else np.full((h, w), np.nan, "float32")
                         for n in names])

    if lazy:
        import dask
        import dask.array as da
        arrs = [da.from_delayed(dask.delayed(load)(groups[d]), shape=(len(names), h, w), dtype="float32") for d in dates]
        data = da.stack(arrs)
    else:
        data = np.stack([load(groups[d]) for d in dates])
    xs = tr.c + tr.a * (np.arange(w) + 0.5)
    ys = tr.f + tr.e * (np.arange(h) + 0.5)
    return xr.Dataset({n: (("time", "y", "x"), data[:, i]) for i, n in enumerate(names)},
                      coords={"time": np.array(dates, dtype="datetime64[ns]"), "y": ys, "x": xs},
                      attrs={"crs": crs_.to_string(), "transform": tuple(tr)[:6], "collection": collection})


def fetch_sar(items: Sequence, aoi, pols: Iterable[str] = ("vv", "vh"), collection: str = "sentinel-1-rtc",
              composite: str = "median", crs=None, resolution: Optional[float] = None) -> BandStack:
    """Sentinel-1 radiometrically terrain-corrected scenes (Planetary Computer ``sentinel-1-rtc``, linear gamma0)
    -> composite in linear power -> converted to dB. Returns a BandStack whose bands are in dB.
    NOT live-tested (no network in the build sandbox); needs a signed PC client (see ``search_items``)."""
    from .sar import to_db
    bs = fetch_bands(items, aoi, names=list(pols), collection=collection, mask_clouds=False,
                     composite=composite, crs=crs, resolution=resolution)
    bs.bands = {k: to_db(v) for k, v in bs.bands.items()}
    return bs


def bandstack_from_tif(path: str, names: Sequence[str]) -> BandStack:
    """Offline alternative to STAC: load a multiband GeoTIFF whose bands are ``names`` (reflectance 0-1)."""
    import rasterio
    with rasterio.open(path) as s:
        if s.count != len(names):
            raise ValueError(f"{path} has {s.count} bands but {len(names)} names were given")
        arr = s.read(masked=True).astype("float32").filled(np.nan)
        return BandStack({n: arr[i] for i, n in enumerate(names)}, s.transform, s.crs, 1, [path])
