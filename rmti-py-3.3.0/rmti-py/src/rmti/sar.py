# Copyright 2025-2026 Cesar Marolla. Apache-2.0.
"""Radar (SAR) flood-extent screening from Sentinel-1-type backscatter (pure NumPy/SciPy).

Open calm water is dark in radar (specular reflection away from the sensor), so inundation shows as a
large drop in backscatter. Unlike optical imagery, SAR sees through cloud, which is why it is the usual choice
for flood events. Method here = speckle filter + fixed/Otsu water threshold + change detection vs a pre-event image.

KNOWN LIMITS (do not skip): flooded buildings and flooded vegetation often get BRIGHTER (double-bounce), so
urban and forest inundation is under-detected; wind-roughened water, radar shadow on steep slopes and smooth
surfaces (tarmac, sand) cause false positives; thresholds are scene-dependent. Mask steep terrain and permanent water
with ``exclude`` (e.g. slope or HAND-derived, a DEM is not bundled). Treat output as a screening footprint.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage


def to_db(linear):
    """Linear power -> dB, NaN preserved, non-positive values mapped to NaN."""
    a = np.asarray(linear, dtype="float32")
    with np.errstate(divide="ignore", invalid="ignore"):
        out = 10.0 * np.log10(np.where(a > 0, a, np.nan))
    return out.astype("float32")


def from_db(db):
    return (10.0 ** (np.asarray(db, dtype="float32") / 10.0)).astype("float32")


def lee_filter(linear, size: int = 5, looks: float = 4.4):
    """Lee speckle filter on LINEAR power. ``looks`` is the equivalent number of looks (S1 GRD IW ~ 4.4).
    NaN pixels are ignored and restored."""
    a = np.asarray(linear, dtype="float64")
    nan = ~np.isfinite(a)
    fill = np.nanmean(a) if (~nan).any() else 0.0
    a = np.where(nan, fill, a)
    mean = ndimage.uniform_filter(a, size, mode="reflect")
    sq = ndimage.uniform_filter(a * a, size, mode="reflect")
    var = np.maximum(sq - mean * mean, 0.0)
    cu2 = 1.0 / looks
    with np.errstate(divide="ignore", invalid="ignore"):
        ci2 = np.where(mean > 0, var / (mean * mean), 0.0)
        w = np.clip(1.0 - cu2 / np.where(ci2 > 0, ci2, np.inf), 0.0, 1.0)
    out = mean + w * (a - mean)
    out[nan] = np.nan
    return out.astype("float32")


def lee_filter_db(db, size: int = 5, looks: float = 4.4):
    return to_db(lee_filter(from_db(db), size, looks))


def otsu_threshold(values, nbins: int = 256) -> float:
    """Otsu's threshold on finite values (use on dB images with a bimodal water/land histogram)."""
    v = np.asarray(values, dtype="float64").ravel()
    v = v[np.isfinite(v)]
    if v.size < 2 or v.min() == v.max():
        raise ValueError("need at least two distinct finite values")
    hist, edges = np.histogram(v, bins=nbins)
    p = hist / hist.sum()
    centers = (edges[:-1] + edges[1:]) / 2
    w0 = np.cumsum(p)
    mu = np.cumsum(p * centers)
    with np.errstate(divide="ignore", invalid="ignore"):
        between = (mu[-1] * w0 - mu) ** 2 / (w0 * (1 - w0))
    return float(centers[np.nanargmax(between)])


def water_mask_sar(db, threshold: float = -15.0):
    """Open-water pixels: backscatter below ``threshold`` dB (typical VV -15..-18, VH -20..-24; tune per scene)."""
    a = np.asarray(db)
    return np.where(np.isnan(a), False, a < threshold)


def flood_from_change(pre_db, post_db, water_db: float = -15.0, change_db: float = -3.0, exclude=None,
                      min_pixels: int = 0):
    """Flood footprint = dark now (< water_db), notably darker than before (post - pre < change_db), and not already
    water. ``exclude`` is an optional boolean mask of pixels to ignore (steep slope, permanent water...).
    ``min_pixels`` removes connected specks smaller than this many pixels."""
    pre, post = np.asarray(pre_db, dtype="float32"), np.asarray(post_db, dtype="float32")
    with np.errstate(invalid="ignore"):
        m = (post < water_db) & ((post - pre) < change_db) & ~(pre < water_db)
    m = np.where(np.isnan(pre) | np.isnan(post), False, m)
    if exclude is not None:
        m &= ~np.asarray(exclude, dtype=bool)
    if min_pixels > 1:
        lab, n = ndimage.label(m)
        if n:
            sizes = ndimage.sum(m, lab, index=np.arange(1, n + 1))
            m = np.isin(lab, np.where(sizes >= min_pixels)[0] + 1)
    return m
