"""Multi-tile mosaics, xarray/Dask time series, SAR flood mapping, Earth Engine (mocked)."""
import datetime as dt, io, zipfile
from unittest.mock import MagicMock
import numpy as np
import pytest

gpd = pytest.importorskip("geopandas"); rasterio = pytest.importorskip("rasterio")
xr = pytest.importorskip("xarray"); pytest.importorskip("dask"); pytest.importorskip("rasterstats")
from rasterio.transform import from_origin, from_bounds
from shapely.geometry import box

from rmti import datasets, gee, sar, stac, timeseries as ts
from rmti.pipeline import flood_run

S = datasets.sample_path


class _A:
    def __init__(self, href, scale=1e-4): self.href, self.extra_fields = href, {"raster:bands": [{"scale": scale, "offset": 0.0}]}
class _I:
    def __init__(self, id, assets, date=None): self.id, self.assets, self.datetime = id, assets, date


def _write(path, arr, crs="EPSG:4326", transform=None, nodata=np.nan):
    transform = transform or from_origin(0, 1, 0.01, 0.01)
    with rasterio.open(path, "w", driver="GTiff", height=arr.shape[0], width=arr.shape[1], count=1, dtype="float32",
                       crs=crs, transform=transform, nodata=nodata) as d:
        d.write(arr.astype("float32"), 1)
    return str(path)


# ---------------- multi-tile mosaic ----------------
def test_target_grid_and_guard():
    crs, tr, h, w = stac.target_grid(box(3.3, 6.45, 3.4, 6.55), resolution=1000)
    assert crs.to_string().startswith("EPSG:326") and 10 <= h <= 14 and 10 <= w <= 14 and tr.a == 1000
    with pytest.raises(ValueError, match="exceeds"):
        stac.target_grid(box(3.0, 6.0, 4.0, 7.0), resolution=10)


def test_mosaic_two_tiles_in_different_crs(tmp_path):
    from pyproj import Transformer
    left = _write(tmp_path / "L.tif", np.full((20, 10), 2000.0), transform=from_bounds(0.0, 0.8, 0.1, 1.0, 10, 20))
    t = Transformer.from_crs(4326, 3857, always_xy=True)
    x0, y0 = t.transform(0.1, 0.8); x1, y1 = t.transform(0.2, 1.0)
    right = _write(tmp_path / "R.tif", np.full((20, 10), 4000.0), crs="EPSG:3857", transform=from_bounds(x0, y0, x1, y1, 10, 20))
    items = [_I("tileA", {"green": _A(left)}), _I("tileB", {"green": _A(right)})]
    aoi = box(0.02, 0.82, 0.18, 0.98)
    bs = stac.fetch_bands(items, aoi, names=["green"], resolution=1500)
    g = bs.bands["green"]
    assert np.isnan(g).mean() < 0.12                                   # seam only
    assert np.nanmean(g[:, 0]) == pytest.approx(0.2, abs=1e-3) and np.nanmean(g[:, -1]) == pytest.approx(0.4, abs=1e-3)
    assert bs.n_scenes == 2 and bs.skipped == []


def test_bad_scene_is_reported_not_fatal(tmp_path):
    ok = _write(tmp_path / "ok.tif", np.full((20, 20), 1000.0))
    items = [_I("good", {"green": _A(ok)}), _I("broken", {"green": _A(str(tmp_path / "missing.tif"))})]
    bs = stac.fetch_bands(items, box(0.02, 0.82, 0.1, 0.9), names=["green"], resolution=2000)
    assert bs.item_ids == ["good"] and len(bs.skipped) == 1 and "broken" in bs.skipped[0]


# ---------------- xarray / dask time series ----------------
def _series_items(tmp_path):
    items, dates = [], [dt.datetime(2026, 1, d) for d in (1, 8, 15, 22)]
    for k, d in enumerate(dates):
        gdn = np.full((100, 100), 1000.0)                               # green 0.10
        sw = np.full((100, 100), 2000.0)                                # swir 0.20  -> MNDWI < 0 (land)
        sw[:, 50:] = 200.0                                              # right half: permanent water (swir 0.02)
        if k >= 2:
            sw[:, :50] = 200.0                                          # left half floods on the last two dates
        items.append(_I(f"s{k}", {"green": _A(_write(tmp_path / f"g{k}.tif", gdn)), "nir": _A(_write(tmp_path / f"n{k}.tif", gdn * 3)),
                                  "swir16": _A(_write(tmp_path / f"s{k}.tif", sw))}, d))
    return items


AOI = box(0.05, 0.1, 0.85, 0.9)


def test_timeseries_eager_equals_lazy_and_groups_by_day(tmp_path):
    items = _series_items(tmp_path)
    eager = stac.fetch_timeseries(items, AOI, names=["green", "nir", "swir1"], resolution=8000)
    lazy = stac.fetch_timeseries(items, AOI, names=["green", "nir", "swir1"], resolution=8000, lazy=True)
    assert eager.sizes["time"] == 4 and eager.attrs["crs"].startswith("EPSG:")
    assert lazy["green"].chunks is not None                           # dask-backed, nothing loaded yet
    xr.testing.assert_allclose(eager, lazy.compute())
    # two tiles on the same day become ONE time step
    dup = items + [_I("dup", items[0].assets, items[0].datetime)]
    assert stac.fetch_timeseries(dup, AOI, names=["green"], resolution=8000).sizes["time"] == 4


def test_timeseries_analytics_flood_from_series(tmp_path):
    ds = stac.fetch_timeseries(_series_items(tmp_path), AOI, names=["green", "nir", "swir1"], resolution=8000, lazy=True)
    ds = ts.add_index(ds, "mndwi")
    freq = ts.water_frequency(ds["mndwi"]).compute()
    assert freq.isel(x=0).mean() == pytest.approx(0.5, abs=0.01) and freq.isel(x=-1).mean() == pytest.approx(1.0, abs=0.01)
    new = ts.new_water_from_series(ds["mndwi"], ("2026-01-01", "2026-01-10"), ("2026-01-14", "2026-01-25")).compute()
    assert new.isel(x=0).all() and not new.isel(x=-1).any()
    assert ts.permanent_water(freq).isel(x=-1).all()
    bs = ts.to_bandstack(ds, "median", "2026-01-14", "2026-01-25")
    assert bs.bands["green"].shape == ds["green"].shape[1:] and bs.n_scenes == 2


def test_trend_and_anomaly():
    t = np.array(["2026-01-01", "2026-04-01", "2026-07-01", "2026-10-01"], dtype="datetime64[ns]")
    base = np.arange(4, dtype="float32")[:, None, None] * np.ones((4, 2, 2), "float32")
    da = xr.DataArray(base, dims=("time", "y", "x"), coords={"time": t})
    slope = ts.trend(da)
    yrs = (t - t[0]) / np.timedelta64(1, "D") / 365.25
    assert float(slope.isel(y=0, x=0)) == pytest.approx(np.polyfit(yrs, np.arange(4), 1)[0], rel=1e-4)
    z = ts.climatology_anomaly(da, ("2026-01-01", "2026-04-02"))
    assert float(z.isel(time=3, y=0, x=0)) > 3


# ---------------- SAR ----------------
def test_db_roundtrip_and_nan():
    assert sar.to_db(1.0) == 0 and sar.to_db(0.1) == pytest.approx(-10, abs=1e-5)
    assert np.isnan(sar.to_db(np.array([0.0, np.nan]))).all()
    assert sar.from_db(sar.to_db(0.37)) == pytest.approx(0.37, rel=1e-5)


def test_lee_reduces_speckle_keeps_mean():
    rng = np.random.default_rng(0)
    img = 0.1 * rng.gamma(4.4, 1 / 4.4, (200, 200))
    f = sar.lee_filter(img)
    assert f.std() < 0.5 * img.std() and f.mean() == pytest.approx(img.mean(), rel=0.03)
    img[3, 3] = np.nan
    assert np.isnan(sar.lee_filter(img)[3, 3])


def test_otsu_separates_modes():
    rng = np.random.default_rng(1)
    v = np.r_[rng.normal(-21, 1.5, 5000), rng.normal(-9, 2, 15000)]
    assert -17 < sar.otsu_threshold(v) < -12
    with pytest.raises(ValueError):
        sar.otsu_threshold([1.0, 1.0])


def _dist():
    yy, xx = np.mgrid[0:100, 0:100]
    return np.abs(yy - (70 + 8 * np.sin(xx / 12.0)))


def test_flood_from_change_on_synthetic_sample_recovers_truth():
    names = ["vv", "vh"]
    pre, post = stac.bandstack_from_tif(S("urban_sar_pre.tif"), names), stac.bandstack_from_tif(S("urban_sar_post.tif"), names)
    m = sar.flood_from_change(sar.lee_filter_db(pre.bands["vv"]), sar.lee_filter_db(post.bands["vv"]), min_pixels=4)
    truth = (_dist() < 12) & ~(_dist() < 3)
    iou = (m & truth).sum() / (m | truth).sum()
    assert iou > 0.8, iou
    assert not (m & (_dist() < 3)).any()                                # permanent river excluded
    m2 = sar.flood_from_change(pre.bands["vv"], post.bands["vv"], exclude=np.ones((100, 100), bool))
    assert not m2.any()


def test_flood_run_with_sar(tmp_path):
    names = ["vv", "vh"]
    pre, post = stac.bandstack_from_tif(S("urban_sar_pre.tif"), names), stac.bandstack_from_tif(S("urban_sar_post.tif"), names)
    res = flood_run(S("urban_aoi.geojson"), S("urban_assets_lines.geojson"), S("urban_population.tif"), str(tmp_path),
                    sar_pre=pre, sar_post=post, L=0.9, V=0.8, rho=0.2, rho_after=0.55, write_map=False)
    assert "SAR VV" in res.summary["hazard_source"] and 0 < res.exposure.E_sel < 1
    with pytest.raises(ValueError, match="both"):
        flood_run(S("urban_aoi.geojson"), S("urban_assets_lines.geojson"), S("urban_population.tif"), str(tmp_path),
                  sar_post=post, L=0.9, V=0.8, rho=0.2)


def test_fetch_sar_returns_db(tmp_path):
    p = _write(tmp_path / "vv.tif", np.full((20, 20), 0.1))
    bs = stac.fetch_sar([_I("a", {"vv": _A(p, scale=1.0)})], box(0.02, 0.82, 0.1, 0.9), pols=["vv"], resolution=2000)
    assert np.nanmean(bs.bands["vv"]) == pytest.approx(-10.0, abs=0.01)


# ---------------- Google Earth Engine (MOCKED: verifies our call logic only) ----------------
def _tif_bytes(n):
    from rasterio.io import MemoryFile
    with MemoryFile() as m:
        with m.open(driver="GTiff", height=5, width=6, count=n, dtype="float32", crs="EPSG:32631", transform=from_origin(0, 50, 10, 10)) as d:
            d.write(np.stack([np.full((5, 6), float(i + 1), "float32") for i in range(n)]))
        return m.read()


def _fake_ee():
    ee = MagicMock()
    col = MagicMock()
    for n in ("filterBounds", "filterDate", "filter", "merge", "select"):
        getattr(col, n).return_value = col
    col.map.side_effect = lambda fn: (fn(MagicMock()), col)[1]          # executes our per-image function body
    ee.ImageCollection.return_value = col
    return ee, col


def test_gee_optical_call_logic(monkeypatch):
    ee, col = _fake_ee()
    final = col.median.return_value.select.return_value
    final.getDownloadURL.return_value = "http://example/dl"
    monkeypatch.setattr(gee, "_ee", lambda: ee)
    monkeypatch.setattr(gee, "_download", lambda url, timeout=300: _tif_bytes(3) if url == "http://example/dl" else b"")
    bs = gee.fetch_bands_gee(box(3.3, 6.45, 3.4, 6.55), "2026-01-01", "2026-02-01", ("green", "nir", "swir1"), max_cloud=20, scale=10)
    assert set(bs.bands) == {"green", "nir", "swir1"} and bs.bands["swir1"].mean() == 3 and str(bs.crs) == "EPSG:32631"
    assert ee.ImageCollection.call_args_list[0].args[0] == gee.S2
    req = final.getDownloadURL.call_args.args[0]
    assert req["scale"] == 10 and req["format"] == "GEO_TIFF" and req["crs"].startswith("EPSG:326")
    ee.Filter.lt.assert_called_with("CLOUDY_PIXEL_PERCENTAGE", 20)
    with pytest.raises(ValueError):
        gee.fetch_bands_gee(box(3.3, 6.45, 3.4, 6.55), "a", "b", collection="modis")


def test_gee_landsat_and_sar_and_zip(monkeypatch):
    ee, col = _fake_ee()
    monkeypatch.setattr(gee, "_ee", lambda: ee)
    col.median.return_value.select.return_value.getDownloadURL.return_value = "u1"
    col.median.return_value.log10.return_value.multiply.return_value.getDownloadURL.return_value = "u2"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("x.vh.tif", _tif_bytes(1)); z.writestr("x.vv.tif", _tif_bytes(1))
    monkeypatch.setattr(gee, "_download", lambda url, timeout=300: {"u1": _tif_bytes(2), "u2": buf.getvalue()}[url])
    ls = gee.fetch_bands_gee(box(3.3, 6.45, 3.4, 6.55), "2026-01-01", "2026-02-01", ("green", "swir1"), collection="landsat", scale=30)
    assert set(ls.bands) == {"green", "swir1"}
    assert [c.args[0] for c in ee.ImageCollection.call_args_list][-2:] == list(gee.LANDSAT)
    s1 = gee.fetch_sar_gee(box(3.3, 6.45, 3.4, 6.55), "2026-01-01", "2026-02-01", pols=("VV", "VH"), orbit="descending")
    assert set(s1.bands) == {"vv", "vh"}
    ee.Filter.eq.assert_any_call("orbitProperties_pass", "DESCENDING")
    with pytest.raises(ValueError):
        gee._to_bandstack(_tif_bytes(2), ["a", "b", "c"], 1)


def test_gee_init_paths(monkeypatch):
    ee = MagicMock(); monkeypatch.setattr(gee, "_ee", lambda: ee)
    gee.init(project="p"); ee.Initialize.assert_called_with(project="p")
    gee.init(project="p", service_account="a@b", key_file="k.json"); ee.ServiceAccountCredentials.assert_called_with("a@b", "k.json")
    gee.init(project="p", authenticate=True); ee.Authenticate.assert_called()
