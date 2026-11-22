# Copyright 2025-2026 Cesar Marolla. Apache-2.0.
"""Time-series analytics on xarray Datasets from ``stac.fetch_timeseries`` (works lazily with Dask-backed data).

Requires: pip install "rmti-py[sat]"
"""
from __future__ import annotations

from typing import Optional, Tuple

import numpy as np

from .stac import BandStack

_INDEX_BANDS = {"ndvi": ("nir", "red"), "ndwi": ("green", "nir"), "mndwi": ("green", "swir1"),
                "ndmi": ("nir", "swir1"), "nbr": ("nir", "swir2")}


def add_index(ds, name: str):
    """Add a normalised-difference index variable (ndvi, ndwi, mndwi, ndmi, nbr) to a Dataset."""
    a, b = _INDEX_BANDS[name]
    if a not in ds or b not in ds:
        raise KeyError(f"{name} needs bands {a!r} and {b!r}")
    return ds.assign({name: ((ds[a] - ds[b]) / (ds[a] + ds[b])).astype("float32")})


def climatology_anomaly(da, baseline: Tuple[str, str], min_std: float = 1e-3):
    """Per-pixel z-score of ``da`` against its mean/std over the baseline period (e.g. dryness vs. a normal year)."""
    ref = da.sel(time=slice(*baseline))
    return (da - ref.mean("time")) / ref.std("time").clip(min=min_std)


def water_frequency(mndwi, threshold: float = 0.0):
    """Fraction of valid observations in which each pixel is water (permanent water ~ 1; flood-prone ~ 0.1-0.5)."""
    valid = mndwi.notnull()
    return ((mndwi > threshold) & valid).sum("time") / valid.sum("time").where(lambda n: n > 0)


def permanent_water(freq, min_freq: float = 0.8):
    return freq >= min_freq


def new_water_from_series(mndwi, baseline: Tuple[str, str], event: Tuple[str, str], threshold: float = 0.0,
                          perm_freq: float = 0.5):
    """Flood-extent proxy: water at least once during ``event`` at pixels that are not water most of the
    ``baseline`` period. Returns a 2-D boolean DataArray."""
    ev = (mndwi.sel(time=slice(*event)) > threshold).any("time")
    return ev & ~(water_frequency(mndwi.sel(time=slice(*baseline)), threshold) >= perm_freq)


def trend(da):
    """Per-pixel least-squares slope per year, ignoring NaNs (vectorised, Dask-friendly)."""
    import xarray as xr
    t = xr.DataArray((da["time"].values - da["time"].values[0]) / np.timedelta64(1, "D") / 365.25, dims="time",
                     coords={"time": da["time"]})
    valid = da.notnull()
    n = valid.sum("time")
    tbar = (t * valid).sum("time") / n
    ybar = da.mean("time")
    cov = ((t - tbar) * (da - ybar)).sum("time")
    var = (((t - tbar) ** 2) * valid).sum("time")
    return (cov / var.where(var > 0)).where(n >= 3)


def to_bandstack(ds, how: str = "median", start: Optional[str] = None, end: Optional[str] = None) -> BandStack:
    """Collapse a Dataset (optionally to a date window) into a BandStack for the raster/pipeline functions."""
    from affine import Affine
    from rasterio.crs import CRS
    sub = ds.sel(time=slice(start, end)) if (start or end) else ds
    red = {"median": lambda x: x.median("time"), "mean": lambda x: x.mean("time"),
           "max": lambda x: x.max("time"), "min": lambda x: x.min("time")}[how]
    bands = {k: red(v).values.astype("float32") for k, v in sub.data_vars.items()}
    return BandStack(bands, Affine(*ds.attrs["transform"]), CRS.from_string(ds.attrs["crs"]), int(sub.sizes["time"]))
