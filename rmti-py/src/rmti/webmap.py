# Copyright 2025-2026 Cesar Marolla. Apache-2.0.
"""Interactive HTML maps (Folium): tier raster overlay, zone choropleth, assets, hazard, centres.

Requires:  pip install "rmti-py[viz]"
The satellite basemap is Esri World Imagery (check its terms of use for your deployment).
"""
from __future__ import annotations

import base64
import io
from typing import Optional

import numpy as np

from .core import TIER_LABELS

TIER_COLORS = ["#2e7d32", "#9ccc65", "#fdd835", "#fb8c00", "#c62828"]     # Tier 1..5
ESRI = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"


def _folium():
    try:
        import folium
        return folium
    except ImportError as exc:  # pragma: no cover
        raise ImportError('maps need: pip install "rmti-py[viz]"') from exc


def tier_raster_png(tier_path: str):
    """Reproject a tier raster (uint8, 0 = nodata) to EPSG:4326 and render an RGBA PNG.
    Returns (png_bytes, [[south, west], [north, east]])."""
    import rasterio
    from PIL import Image
    from rasterio.warp import Resampling, calculate_default_transform, reproject
    with rasterio.open(tier_path) as s:
        tr, w, h = calculate_default_transform(s.crs, "EPSG:4326", s.width, s.height, *s.bounds)
        dst = np.zeros((h, w), dtype="uint8")
        reproject(rasterio.band(s, 1), dst, src_transform=s.transform, src_crs=s.crs, dst_transform=tr,
                  dst_crs="EPSG:4326", resampling=Resampling.nearest, src_nodata=0, dst_nodata=0)
    rgba = np.zeros((h, w, 4), dtype="uint8")
    for i, col in enumerate(TIER_COLORS, start=1):
        rgba[dst == i] = [int(col[j:j + 2], 16) for j in (1, 3, 5)] + [190]
    buf = io.BytesIO()
    Image.fromarray(rgba, "RGBA").save(buf, format="PNG")
    west, north = tr.c, tr.f
    east, south = tr.c + tr.a * w, tr.f + tr.e * h
    return buf.getvalue(), [[south, west], [north, east]]


def risk_map(zones=None, tier_raster: Optional[str] = None, hazard=None, assets=None, centers=None,
             popup_cols=("name", "R", "tier"), satellite: bool = True):
    """Build a Folium map. ``zones`` should carry ``tier_n`` (1..5) and ``R`` (see raster_risk.zonal_risk)."""
    folium = _folium()
    layers = [zones, hazard, assets, centers]
    ref = next((g for g in layers if g is not None), None)
    if ref is not None:
        minx, miny, maxx, maxy = ref.to_crs(4326).total_bounds
        center = [(miny + maxy) / 2, (minx + maxx) / 2]
    else:
        center = [0, 0]
    m = folium.Map(location=center, zoom_start=11, tiles="OpenStreetMap" if not satellite else None, control_scale=True)
    if satellite:
        folium.TileLayer(ESRI, attr="Esri World Imagery", name="Satellite").add_to(m)
        folium.TileLayer("OpenStreetMap", name="Streets").add_to(m)
    if tier_raster:
        png, bounds = tier_raster_png(tier_raster)
        folium.raster_layers.ImageOverlay("data:image/png;base64," + base64.b64encode(png).decode(),
                                          bounds=bounds, name="RMTI tier (raster)", opacity=0.8).add_to(m)
    if zones is not None:
        z = zones.to_crs(4326)
        cols = [c for c in popup_cols if c in z.columns]
        def style(f):
            n = f["properties"].get("tier_n")
            col = TIER_COLORS[int(n) - 1] if n and not np.isnan(n) else "#9e9e9e"
            return {"fillColor": col, "color": "#222", "weight": 1, "fillOpacity": 0.55}
        keep = z[cols + ["tier_n", "geometry"]] if "tier_n" in z.columns else z[cols + ["geometry"]]
        folium.GeoJson(keep.to_json(), name="Zones (RMTI tier)", style_function=style,
                       tooltip=folium.GeoJsonTooltip(fields=cols) if cols else None).add_to(m)
    if hazard is not None:
        folium.GeoJson(hazard.to_crs(4326).to_json(), name="Hazard footprint",
                       style_function=lambda f: {"color": "#1565c0", "fillColor": "#42a5f5", "weight": 1,
                                                 "fillOpacity": 0.35}).add_to(m)
    if assets is not None:
        folium.GeoJson(assets.to_crs(4326).to_json(), name="Assets",
                       style_function=lambda f: {"color": "#ffffff", "weight": 3}).add_to(m)
    if centers is not None:
        c = centers.to_crs(4326)
        fg = folium.FeatureGroup(name="Centres")
        for _, r in c.iterrows():
            folium.CircleMarker([r.geometry.y, r.geometry.x], radius=6, color="#000", fill=True,
                                fill_color="#fff", tooltip=str(r.get("name", "centre"))).add_to(fg)
        fg.add_to(m)
    legend = "".join(f'<div><span style="background:{c};width:12px;height:12px;display:inline-block;margin-right:6px"></span>{l}</div>'
                     for c, l in zip(TIER_COLORS, TIER_LABELS))
    m.get_root().html.add_child(folium.Element(
        f'<div style="position:fixed;bottom:24px;left:12px;z-index:9999;background:#fff;padding:8px 10px;'
        f'font:12px sans-serif;border:1px solid #888;border-radius:4px">{legend}</div>'))
    folium.LayerControl().add_to(m)
    return m
