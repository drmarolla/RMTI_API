import json, os
import numpy as np
import pytest

gpd = pytest.importorskip("geopandas")
rasterio = pytest.importorskip("rasterio")
pytest.importorskip("rasterstats")
pd = pytest.importorskip("pandas")
from rasterio.transform import from_origin

from rmti import indices, raster_risk as rr, datasets
from rmti.core import tier_index, TIER_LABELS
from rmti.domains import hcc, hcc_geo
from rmti.stac import BandStack, bandstack_from_tif, fetch_bands
from rmti.pipeline import flood_run, dryness_run

S = datasets.sample_path


# ---------- indices ----------
def test_indices_and_scaling():
    assert indices.ndvi(0.5, 0.1) == pytest.approx(0.4 / 0.6)
    assert np.isnan(indices.ndvi(0.0, 0.0))
    assert indices.mndwi(0.1, 0.02) > 0 > indices.mndwi(0.05, 0.3)
    s = indices.scale_linear(np.array([-1, 0.1, 2, np.nan]), 0.0, 1.0)
    assert s[0] == 0 and s[2] == 1 and np.isnan(s[3])
    assert indices.fuel_dryness(np.array([-0.2, 0.4]))[0] == 1 and indices.fuel_dryness(np.array([-0.2, 0.4]))[1] == 0
    assert indices.new_water(np.array([1, 0, 0], bool), np.array([1, 1, 0], bool)).tolist() == [False, True, False]


# ---------- raster risk ----------
def _tif(path, arr, nodata=np.nan):
    with rasterio.open(path, "w", driver="GTiff", height=arr.shape[0], width=arr.shape[1], count=1, dtype="float32",
                       crs="EPSG:4326", transform=from_origin(0, 1, 0.01, 0.01), nodata=nodata) as d:
        d.write(arr.astype("float32"), 1)
    return str(path)


def test_risk_arrays_matches_scalar_and_nan_and_bounds():
    R, t = rr.risk_arrays(0.9, 0.65, 0.8, 0.2)
    assert float(R) == pytest.approx(0.3744, abs=1e-4) and int(t) == 4
    R, t = rr.risk_arrays(np.array([0.5, np.nan]), 1, 1, 0)
    assert t.tolist() == [4, 0] and np.isnan(R[1])
    with pytest.raises(ValueError):
        rr.risk_arrays(1.5, 0.5, 0.5, 0.5)


def test_risk_raster_blockwise_equals_in_memory(tmp_path):
    rng = np.random.default_rng(1)
    v = rng.uniform(0, 1, (300, 400)).astype("float32")      # > one 256 block in both axes
    v[5, 5] = np.nan
    vp = _tif(tmp_path / "v.tif", v)
    out = rr.risk_raster({"L": 0.9, "E": 0.7, "V": vp, "rho": 0.2}, str(tmp_path / "R.tif"), str(tmp_path / "t.tif"))
    with rasterio.open(out["R"]) as s:
        R = s.read(1)
    expect = 0.9 * 0.7 * v * 0.8
    np.testing.assert_allclose(R[~np.isnan(v)], expect[~np.isnan(v)], rtol=1e-5)
    assert np.isnan(R[5, 5])
    with rasterio.open(out["tier"]) as s:
        t = s.read(1)
    assert t[5, 5] == 0
    h = rr.tier_histogram(out["tier"])
    assert sum(h.values()) == pytest.approx(1.0)


def test_risk_raster_grid_mismatch_and_align(tmp_path):
    a = _tif(tmp_path / "a.tif", np.full((20, 20), 0.5))
    b = _tif(tmp_path / "b.tif", np.full((10, 10), 0.5))
    with pytest.raises(ValueError, match="same grid"):
        rr.risk_raster({"L": a, "E": b, "V": 1, "rho": 0}, str(tmp_path / "o.tif"))
    al = rr.align_raster(b, a, str(tmp_path / "b_al.tif"))
    out = rr.risk_raster({"L": a, "E": al, "V": 1, "rho": 0}, str(tmp_path / "o.tif"))
    with rasterio.open(out["R"]) as s:
        assert s.read(1).shape == (20, 20)
    with pytest.raises(ValueError):
        rr.risk_raster({"L": 1, "E": 1, "V": 1, "rho": 0}, str(tmp_path / "x.tif"))


def test_cog_written_and_zonal_risk(tmp_path):
    arr = np.full((20, 20), 0.5, dtype="float32")
    p = _tif(tmp_path / "v.tif", arr)
    cog = rr.cogify(p, str(tmp_path / "c.tif"))
    with rasterio.open(cog) as s:
        assert s.read(1).shape == (20, 20)
    from shapely.geometry import box
    z = gpd.GeoDataFrame({"name": ["a"]}, geometry=[box(0, 0.8, 0.1, 1.0)], crs=4326)
    out = rr.zonal_risk(z, 0.9, 0.7, "V", 0.2, layer_paths={"V": p})
    assert out["R"].iloc[0] == pytest.approx(0.9 * 0.7 * 0.5 * 0.8, abs=1e-5)
    assert out["tier"].iloc[0] == TIER_LABELS[int(tier_index(out["R"].iloc[0]))]


# ---------- STAC (offline, fake items on local files) ----------
class _Asset:
    def __init__(self, href, scale=1.0, offset=0.0):
        self.href, self.extra_fields = href, {"raster:bands": [{"scale": scale, "offset": offset}]}


class _Item:
    def __init__(self, id, assets): self.id, self.assets = id, assets


def test_fetch_bands_scale_cloudmask_and_median(tmp_path):
    aoi = gpd.GeoDataFrame(geometry=[__import__("shapely.geometry", fromlist=["box"]).box(0.02, 0.8, 0.12, 0.98)], crs=4326)
    items = []
    for k, dn in enumerate([1000, 2000, 9000]):               # third scene is cloudy -> masked
        a = {}
        for key in ("green", "nir", "swir16"):
            a[key] = _Asset(_tif(tmp_path / f"{k}{key}.tif", np.full((100, 100), dn)), scale=1e-4)
        scl = np.full((100, 100), 9 if k == 2 else 4)
        a["scl"] = _Asset(_tif(tmp_path / f"{k}scl.tif", scl), scale=1.0)
        items.append(_Item(f"s{k}", a))
    st = fetch_bands(items, aoi, names=("green", "nir", "swir1"), resolution=2000)
    assert st.n_scenes == 3
    assert np.nanmedian(st.bands["green"]) == pytest.approx(0.15, abs=1e-3)      # median(0.1, 0.2), cloud scene masked
    with pytest.raises(RuntimeError):
        fetch_bands([], aoi)


def test_bandstack_from_tif_validates():
    st = bandstack_from_tif(S("urban_bands_post.tif"), ["green", "red", "nir", "swir1"])
    assert st.bands["green"].shape == (100, 100)
    with pytest.raises(ValueError):
        bandstack_from_tif(S("urban_bands_post.tif"), ["a", "b"])


# ---------- pipelines on the synthetic sample ----------
NAMES = ["green", "red", "nir", "swir1"]


def test_flood_run_sample_end_to_end(tmp_path):
    post = bandstack_from_tif(S("urban_bands_post.tif"), NAMES)
    pre = bandstack_from_tif(S("urban_bands_pre.tif"), NAMES)
    res = flood_run(S("urban_aoi.geojson"), S("urban_assets_lines.geojson"), S("urban_population.tif"),
                    str(tmp_path), post=post, pre=pre, L=0.9, V=0.8, rho=0.2, C=5, rho_after=0.55,
                    zones=S("urban_zones.geojson"))
    e = res.exposure
    assert 0 < e.E_sel < 1 and e.N > 0 and 0 < e.E_pop < 1
    assert res.summary["R_after"] < res.summary["R"]
    assert "R" in res.zones and res.zones["tier_n"].notna().any()
    for k in ("hazard", "mndwi_cog", "summary", "map", "zones"):
        assert os.path.exists(res.outputs[k]), k
    html = open(res.outputs["map"]).read()
    assert "leaflet" in html.lower()
    # post-only (all water) hazard must be at least as large as new water
    res2 = flood_run(S("urban_aoi.geojson"), S("urban_assets_lines.geojson"), S("urban_population.tif"),
                     str(tmp_path / "b"), post=post, L=0.9, V=0.8, rho=0.2, write_map=False)
    assert res2.exposure.E_sel >= e.E_sel


def test_flood_run_requires_hazard_or_imagery(tmp_path):
    with pytest.raises(ValueError):
        flood_run(S("urban_aoi.geojson"), S("urban_assets_lines.geojson"), S("urban_population.tif"),
                  str(tmp_path), L=0.9, V=0.8, rho=0.2)


def test_dryness_run_sample(tmp_path):
    post = bandstack_from_tif(S("urban_bands_post.tif"), NAMES)
    res = dryness_run(post, str(tmp_path), L=0.8, E=0.6, rho=0.3, zones=S("urban_zones.geojson"))
    assert abs(sum(res.summary["tier_share"].values()) - 1) < 1e-9
    for k in ("V", "R", "tier", "map"):
        assert os.path.exists(res.outputs[k])
    assert res.zones["R"].notna().all()


def test_geospatial_vectorised_scale_and_zone_function():
    from rmti import geospatial as gs
    from shapely.geometry import LineString, box
    rng = np.random.default_rng(0)
    lines = gpd.GeoDataFrame(geometry=[LineString([(rng.uniform(0, 1), rng.uniform(0, 1)), (rng.uniform(0, 1), rng.uniform(0, 1))])
                                       for _ in range(5000)], crs=4326)
    haz = gpd.GeoDataFrame(geometry=[box(0, 0, 0.5, 1)], crs=4326)
    import time; t0 = time.time()
    f, _ = gs.asset_exposure_fractions(lines, haz)
    assert time.time() - t0 < 10 and f.shape == (5000,) and 0 < f.mean() < 1
    zs = gs.compute_e_sel_by_zone(gpd.GeoDataFrame(geometry=lines.geometry[:50], crs=4326), haz,
                                  gpd.GeoDataFrame(geometry=[box(0, 0, 1, 1), box(5, 5, 6, 6)], crs=4326))
    assert zs["E_sel"].iloc[0] > 0 and np.isnan(zs["E_sel"].iloc[1])


# ---------- oncology ----------
def test_score_table_matches_scalar_and_sorts():
    df = pd.read_csv(S("hcc_patients_synthetic.csv"))
    out = hcc.score_table(df)
    assert len(out) == 200 and out["priority"].tolist() == list(range(1, 201))
    assert (out["tier_n"].diff().dropna() <= 0).all()                         # tiers non-increasing
    r = out.iloc[7]
    sc = hcc.score_patient(r.L, r.E, int(r.albi_grade), r.surveillance, r.bclc_if_missed, "optimised")
    assert r.R == pytest.approx(sc["R"], abs=6e-4) and r.tier == sc["tier"]
    assert (out["R_after"] <= out["R"] + 1e-9).all()


def test_score_table_validation():
    base = dict(L=[0.3], E=[0.6], albi_grade=[1], surveillance=["usual"], bclc_if_missed=["A"])
    hcc.score_table(pd.DataFrame(base))
    with pytest.raises(ValueError):
        hcc.score_table(pd.DataFrame({**base, "surveillance": ["weekly"]}))
    with pytest.raises(ValueError):
        hcc.score_table(pd.DataFrame({**base, "L": [1.4]}))
    with pytest.raises(ValueError):
        hcc.score_table(pd.DataFrame({k: v for k, v in base.items() if k != "albi_grade"}))


def test_access_exposure_and_zone_scoring():
    z = gpd.read_file(S("hcc_districts.geojson")); c = gpd.read_file(S("hcc_centers.geojson"))
    small = hcc_geo.access_exposure(z, c, 5, S("hcc_at_risk.tif"))
    big = hcc_geo.access_exposure(z, c, 80, S("hcc_at_risk.tif"))
    assert (small["E"] <= big["E"] + 1e-9).all() and big["E"].min() > 0.95 and small["E"].max() < 1
    assert big["at_risk_raster_sum"].sum() == pytest.approx(z["n_at_risk"].sum(), rel=0.02)
    z2 = big.assign(rho=hcc_geo.rho_from_uptake(big["uptake"]))
    sc = hcc_geo.score_zones(z2, rho_after=0.65)
    assert (sc["R_after"] < sc["R"]).all() and sc["tier"].notna().all()
    assert hcc_geo.rho_from_uptake(0.05) == 0.15 and hcc_geo.rho_from_uptake(0.9) == 0.50


def test_datasets_match_domain_modules():
    from rmti.domains import urban
    assert datasets.load_urban_cohort() == {k: {kk: vv for kk, vv in v.items()} for k, v in urban.COHORT.items()}
    assert datasets.load_hcc_published() == hcc.PUBLISHED_COHORTS
