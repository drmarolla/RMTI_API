# Copyright 2025-2026 Cesar Marolla. Apache-2.0.
"""Spectral indices and fixed-anchor scaling (pure NumPy; no I/O).

All functions take reflectance arrays (0-1) and propagate NaN. Scaling to the
RMTI [0, 1] range uses FIXED, user-stated anchors (never the sample's own
min/max), in the same spirit as the fixed tiers: a score must mean the same
thing in every scene.  The default anchors below are ASSUMPTIONS to be
replaced with locally calibrated values.
"""
from __future__ import annotations

import numpy as np


def normalized_difference(a, b):
    a, b = np.asarray(a, dtype="float32"), np.asarray(b, dtype="float32")
    with np.errstate(divide="ignore", invalid="ignore"):
        out = (a - b) / (a + b)
    return np.where(np.isfinite(out), out, np.nan).astype("float32")


def ndvi(nir, red):      return normalized_difference(nir, red)
def ndwi(green, nir):    return normalized_difference(green, nir)      # McFeeters 1996
def mndwi(green, swir1): return normalized_difference(green, swir1)    # Xu 2006
def ndmi(nir, swir1):    return normalized_difference(nir, swir1)      # vegetation moisture
def nbr(nir, swir2):     return normalized_difference(nir, swir2)      # burn ratio


def savi(nir, red, L=0.5):
    nir, red = np.asarray(nir, dtype="float32"), np.asarray(red, dtype="float32")
    with np.errstate(divide="ignore", invalid="ignore"):
        return ((nir - red) / (nir + red + L) * (1 + L)).astype("float32")


def scale_linear(x, lo: float, hi: float, invert: bool = False):
    """Map x to [0, 1] with fixed anchors lo -> 0, hi -> 1 (clipped); NaN preserved."""
    if hi == lo:
        raise ValueError("lo and hi must differ")
    y = np.clip((np.asarray(x, dtype="float32") - lo) / (hi - lo), 0.0, 1.0)
    return (1.0 - y if invert else y).astype("float32")


def fuel_dryness(ndmi_arr, lo: float = -0.2, hi: float = 0.4):
    """Dryness proxy in [0,1]: 1 = driest. ASSUMED anchors (NDMI -0.2 .. 0.4);
    calibrate locally. A vegetation-moisture proxy is not a fire-danger model."""
    return scale_linear(ndmi_arr, lo, hi, invert=True)


def water_mask(mndwi_arr, threshold: float = 0.0):
    """Open-water mask from MNDWI > threshold (0.0 is the conventional start; tune)."""
    a = np.asarray(mndwi_arr)
    return np.where(np.isnan(a), False, a > threshold)


def new_water(pre_water, post_water):
    """Pixels that are water now but were not before (a flood-extent proxy).
    Surface-water indices are blind to cloud-covered, vegetated or built-up
    inundation; SAR-based products are preferable for event mapping."""
    return np.asarray(post_water, dtype=bool) & ~np.asarray(pre_water, dtype=bool)
