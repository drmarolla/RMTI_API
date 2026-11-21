import numpy as np
import pytest

gpd = pytest.importorskip("geopandas")
rasterio = pytest.importorskip("rasterio")
pytest.importorskip("rasterstats")
from rasterio.transform import from_origin
from shapely.geometry import LineString, Point, box

from rmti import geospatial as gs


@pytest.fixture
def pop_raster(tmp_path):
    # 10x10 cells of 0.01 deg, 100 persons each => 10,000 total; EPSG:4326, origin (36.0, -1.0)
    path = tmp_path / "pop.tif"
    data = np.full((10, 10), 100.0, dtype="float32")
    with rasterio.open(path, "w", driver="GTiff", height=10, width=10, count=1, dtype="float32",
                       crs="EPSG:4326", transform=from_origin(36.0, -1.0, 0.01, 0.01), nodata=-9999) as dst:
        dst.write(data, 1)
    return str(path)


def test_line_exposure_by_length_with_overlapping_hazards_not_double_counted():
    roads = gpd.GeoDataFrame(geometry=[LineString([(36.00, -1.05), (36.10, -1.05)])], crs="EPSG:4326")
    # two overlapping polygons that together cover x in [36.00, 36.05] => half the road
    haz = gpd.GeoDataFrame(geometry=[box(36.00, -1.1, 36.04, -1.0), box(36.02, -1.1, 36.05, -1.0)], crs="EPSG:4326")
    assert gs.compute_e_sel(roads, haz) == pytest.approx(0.5, abs=0.01)


def test_polygon_area_and_weight_col_and_crs_independence():
    a = gpd.GeoDataFrame({"value": [3.0, 1.0]}, geometry=[box(36.00, -1.05, 36.02, -1.03), box(36.06, -1.05, 36.08, -1.03)], crs="EPSG:4326")
    haz = gpd.GeoDataFrame(geometry=[box(36.0, -1.1, 36.03, -1.0)], crs="EPSG:4326")
    assert gs.compute_e_sel(a, haz, "value") == pytest.approx(3.0 / 4.0, rel=1e-3)
    # same answer after reprojecting the hazard to a different CRS
    assert gs.compute_e_sel(a, haz.to_crs(haz.estimate_utm_crs()), "value") == pytest.approx(0.75, rel=1e-3)


def test_points_need_weights_and_mixed_layers_rejected():
    pts = gpd.GeoDataFrame({"users": [10, 30]}, geometry=[Point(36.01, -1.01), Point(36.08, -1.08)], crs="EPSG:4326")
    haz = gpd.GeoDataFrame(geometry=[box(36.0, -1.05, 36.05, -1.0)], crs="EPSG:4326")
    with pytest.raises(ValueError):
        gs.compute_e_sel(pts, haz)
    assert gs.compute_e_sel(pts, haz, "users") == pytest.approx(10 / 40)


def test_full_pipeline_population(pop_raster):
    juris = gpd.GeoDataFrame(geometry=[box(36.0, -1.1, 36.1, -1.0)], crs="EPSG:4326")
    # hazard covers the left 3 columns of 10 => 30% of population
    haz = gpd.GeoDataFrame(geometry=[box(35.9, -1.2, 36.03, -0.9)], crs="EPSG:4326")
    roads = gpd.GeoDataFrame(geometry=[LineString([(36.0, -1.05), (36.1, -1.05)])], crs="EPSG:4326")
    r = gs.compute_spatial_exposure(roads, haz, juris, pop_raster)
    assert r.N == 10_000 and r.N_exposed == 3_000
    assert r.E_pop == pytest.approx(0.3) and r.E_sel == pytest.approx(0.3, abs=0.01)
    assert 0 < r.E_log < 1


def test_jurisdiction_in_projected_crs_is_reprojected_to_raster(pop_raster):
    juris = gpd.GeoDataFrame(geometry=[box(36.0, -1.1, 36.1, -1.0)], crs="EPSG:4326")
    utm = juris.to_crs(juris.estimate_utm_crs())
    assert gs.raster_sum(utm, pop_raster) == pytest.approx(10_000, rel=0.02)


def test_missing_crs_raises():
    a = gpd.GeoDataFrame(geometry=[LineString([(0, 0), (1, 1)])])
    with pytest.raises(ValueError):
        gs.compute_e_sel(a, a)
