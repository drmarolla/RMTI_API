# Copyright 2025-2026 Cesar Marolla. Apache-2.0.
"""Google Earth Engine backend: server-side compositing, then a small GeoTIFF download into a ``BandStack``.

Requires:  pip install "rmti-py[gee]"   and an Earth Engine account/Cloud project (non-commercial use is free;
commercial use needs an EE commercial licence - check Google's terms for your deployment).

Why GEE: the heavy lifting (cloud masking, compositing, SAR terrain-corrected collections) runs on Google's side,
so you download only the finished composite. Limits: ``getDownloadURL`` caps request size (about 32 MB / 10,000 px per
side); for larger areas tile the AOI or use ``ee.batch.Export`` yourself.

NOT live-tested: this module could not be run against Earth Engine in the build sandbox (no network/credentials).
Unit tests use a mocked ``ee`` and verify only our call logic. The ``ee`` function names used here were checked to
exist in earthengine-api 1.7. Run one small AOI on your account before relying on it.
"""
from __future__ import annotations

import io
import urllib.request
import zipfile
from typing import Dict, Iterable, Optional, Sequence

import numpy as np

from .stac import SCL_BAD, BandStack

S2 = "COPERNICUS/S2_SR_HARMONIZED"
S1 = "COPERNICUS/S1_GRD"
LANDSAT = ("LANDSAT/LC08/C02/T1_L2", "LANDSAT/LC09/C02/T1_L2")
S2_BANDS = dict(green="B3", red="B4", nir="B8", swir1="B11", swir2="B12")
LS_BANDS = dict(green="SR_B3", red="SR_B4", nir="SR_B5", swir1="SR_B6", swir2="SR_B7")


def _ee():
    try:
        import ee
        return ee
    except ImportError as exc:  # pragma: no cover
        raise ImportError('Earth Engine support needs: pip install "rmti-py[gee]"') from exc


def init(project: Optional[str] = None, service_account: Optional[str] = None, key_file: Optional[str] = None,
         authenticate: bool = False):
    """Initialise Earth Engine. Interactive users: ``init(project="my-cloud-project", authenticate=True)`` once.
    Servers: pass a service account email and JSON key file."""
    ee = _ee()
    if service_account and key_file:
        ee.Initialize(ee.ServiceAccountCredentials(service_account, key_file), project=project)
        return
    if authenticate:
        ee.Authenticate()
    ee.Initialize(project=project)


def _aoi_geometry(aoi):
    """(ee.Geometry rectangle, bounds EPSG:4326, UTM crs string)."""
    ee = _ee()
    from .stac import as_gdf
    a = as_gdf(aoi)
    minx, miny, maxx, maxy = a.to_crs(4326).total_bounds
    return ee.Geometry.Rectangle([float(minx), float(miny), float(maxx), float(maxy)]), (minx, miny, maxx, maxy), \
        a.to_crs(4326).estimate_utm_crs().to_string()


def _download(url: str, timeout: int = 300) -> bytes:
    with urllib.request.urlopen(url, timeout=timeout) as r:      # pragma: no cover (network)
        return r.read()


def _to_bandstack(blob: bytes, names: Sequence[str], n_scenes: int) -> BandStack:
    import rasterio
    from rasterio.io import MemoryFile
    names = list(names)
    arrays: Dict[str, np.ndarray] = {}
    if blob[:2] == b"PK":                                          # zipped, one tif per band
        zf = zipfile.ZipFile(io.BytesIO(blob))
        tifs = sorted(n for n in zf.namelist() if n.lower().endswith(".tif"))
        if len(tifs) != len(names):
            raise ValueError(f"expected {len(names)} tifs in archive, got {tifs}")
        for name, t in zip(names, tifs):
            with MemoryFile(zf.read(t)) as m, m.open() as s:
                arrays[name] = s.read(1, masked=True).astype("float32").filled(np.nan)
                tr, crs = s.transform, s.crs
    else:
        with MemoryFile(blob) as m, m.open() as s:
            if s.count != len(names):
                raise ValueError(f"download has {s.count} bands, expected {len(names)}")
            data = s.read(masked=True).astype("float32").filled(np.nan)
            tr, crs = s.transform, s.crs
        arrays = {n: data[i] for i, n in enumerate(names)}
    return BandStack(arrays, tr, crs, n_scenes, ["earthengine"])


def _fetch(image, names, region, scale, crs, n_scenes=1):
    url = image.getDownloadURL({"region": region, "scale": scale, "crs": crs, "format": "GEO_TIFF"})
    return _to_bandstack(_download(url), names, n_scenes)


def fetch_bands_gee(aoi, start: str, end: str, names: Iterable[str] = ("green", "nir", "swir1"),
                    collection: str = "sentinel-2", max_cloud: float = 30.0, scale: float = 10.0,
                    mask_clouds: bool = True) -> BandStack:
    """Cloud-masked median reflectance composite (0-1). ``collection``: ``"sentinel-2"`` or ``"landsat"`` (8+9, L2)."""
    ee = _ee()
    names = list(names)
    region, _, crs = _aoi_geometry(aoi)
    if collection == "sentinel-2":
        bmap, ids = S2_BANDS, [S2]
        col = ee.ImageCollection(S2).filterBounds(region).filterDate(start, end) \
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", max_cloud))

        def prep(img):
            m = ee.Image(1)
            for c in SCL_BAD:
                m = m.And(img.select("SCL").neq(c))
            out = img.select([bmap[n] for n in names], names).multiply(1e-4)
            return out.updateMask(m) if mask_clouds else out
    elif collection == "landsat":
        bmap = LS_BANDS
        col = ee.ImageCollection(LANDSAT[0]).merge(ee.ImageCollection(LANDSAT[1])) \
            .filterBounds(region).filterDate(start, end).filter(ee.Filter.lt("CLOUD_COVER", max_cloud))

        def prep(img):
            qa = img.select("QA_PIXEL")
            m = qa.bitwiseAnd(1 << 1).eq(0).And(qa.bitwiseAnd(1 << 3).eq(0)).And(qa.bitwiseAnd(1 << 4).eq(0))
            out = img.select([bmap[n] for n in names], names).multiply(2.75e-5).add(-0.2)
            return out.updateMask(m) if mask_clouds else out
    else:
        raise ValueError("collection must be 'sentinel-2' or 'landsat'")
    comp = col.map(prep).median().select(names)
    return _fetch(comp, names, region, scale, crs)


def fetch_sar_gee(aoi, start: str, end: str, pols: Iterable[str] = ("VV", "VH"), orbit: Optional[str] = None,
                  scale: float = 10.0) -> BandStack:
    """Sentinel-1 GRD (IW, terrain-corrected, already in dB in GEE): median in LINEAR power, returned in dB.
    ``orbit`` = "ASCENDING"/"DESCENDING" to keep viewing geometry constant between pre and post images (recommended).
    Band names in the returned stack are lower-case (``vv``, ``vh``)."""
    ee = _ee()
    pols = [p.upper() for p in pols]
    region, _, crs = _aoi_geometry(aoi)
    col = ee.ImageCollection(S1).filterBounds(region).filterDate(start, end) \
        .filter(ee.Filter.eq("instrumentMode", "IW"))
    for p in pols:
        col = col.filter(ee.Filter.listContains("transmitterReceiverPolarisation", p))
    if orbit:
        col = col.filter(ee.Filter.eq("orbitProperties_pass", orbit.upper()))
    lin = col.select(pols).map(lambda i: ee.Image(10).pow(i.divide(10)))
    db = lin.median().log10().multiply(10)
    return _fetch(db, [p.lower() for p in pols], region, scale, crs)
