"""Generate the SYNTHETIC demo datasets shipped in src/rmti/data/sample (seeded; deterministic).
None of this is real data: places are generic grids, patients are simulated."""
import csv, json, os
import numpy as np
import geopandas as gpd, rasterio
from rasterio.transform import from_origin
from shapely.geometry import LineString, Point, box

OUT = os.path.join(os.path.dirname(__file__), "..", "src", "rmti", "data", "sample")
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(2026)

# ---------------- urban demo ("Demo City", 0.1 x 0.1 deg, 100 x 100 px) -----------------
W, S, E_, N_ = 3.30, 6.45, 3.40, 6.55
px = 0.001
tr = from_origin(W, N_, px, px)
yy, xx = np.mgrid[0:100, 0:100]
river_row = (70 + 8 * np.sin(xx / 12.0)).astype(float)
dist = np.abs(yy - river_row)
def bands(flood_extra):
    water = dist < (3 + flood_extra)
    veg = np.clip(0.55 - 0.004 * np.abs(yy - 30) + rng.normal(0, 0.03, (100, 100)), 0.05, 0.9)
    green = np.where(water, 0.12, 0.08 + 0.05 * veg) + rng.normal(0, 0.005, (100, 100))
    red = np.where(water, 0.07, 0.10 + 0.08 * (1 - veg))
    nir = np.where(water, 0.03, 0.15 + 0.35 * veg)
    swir1 = np.where(water, 0.02, 0.12 + 0.18 * (1 - veg) + 0.1 * veg * 0.3)
    return np.stack([green, red, nir, swir1]).astype("float32")
for name, extra in (("pre", 0), ("post", 9)):
    with rasterio.open(f"{OUT}/urban_bands_{name}.tif", "w", driver="GTiff", height=100, width=100, count=4,
                       dtype="float32", crs="EPSG:4326", transform=tr, compress="deflate") as d:
        d.write(bands(extra))
        d.descriptions = ("green", "red", "nir", "swir1")
pop = (3000 * np.exp(-dist / 18.0) + rng.uniform(200, 800, (100, 100))).astype("float32")
with rasterio.open(f"{OUT}/urban_population.tif", "w", driver="GTiff", height=100, width=100, count=1,
                   dtype="float32", crs="EPSG:4326", transform=tr, nodata=-9999, compress="deflate") as d:
    d.write(pop, 1)
aoi = gpd.GeoDataFrame({"name": ["Demo City"]}, geometry=[box(W, S, E_, N_)], crs=4326)
aoi.to_file(f"{OUT}/urban_aoi.geojson", driver="GeoJSON")
lines = [LineString([(W + 0.005, S + 0.01 * k + 0.004), (E_ - 0.005, S + 0.01 * k + 0.004 + 0.003 * ((k % 3) - 1))]) for k in range(1, 10)]
lines += [LineString([(W + 0.01 * k, S + 0.005), (W + 0.01 * k + 0.004, N_ - 0.005)]) for k in range(1, 10)]
gpd.GeoDataFrame({"name": [f"Transit line {i + 1}" for i in range(len(lines))], "asset": "transit"},
                 geometry=lines, crs=4326).to_file(f"{OUT}/urban_assets_lines.geojson", driver="GeoJSON")
pts = [Point(W + rng.uniform(0.005, 0.095), S + rng.uniform(0.005, 0.095)) for _ in range(30)]
gpd.GeoDataFrame({"name": [f"Facility {i + 1}" for i in range(30)], "users": rng.integers(2000, 60000, 30)},
                 geometry=pts, crs=4326).to_file(f"{OUT}/urban_assets_points.geojson", driver="GeoJSON")
cells = [box(W + 0.02 * i, S + 0.02 * j, W + 0.02 * (i + 1), S + 0.02 * (j + 1)) for j in range(5) for i in range(5)]
gpd.GeoDataFrame({"name": [f"Ward {j * 5 + i + 1}" for j in range(5) for i in range(5)]}, geometry=cells,
                 crs=4326).to_file(f"{OUT}/urban_zones.geojson", driver="GeoJSON")

# ---------------- HCC demo (12 districts, 0.6 x 0.45 deg) -----------------
W2, S2 = 36.70, -1.45
dists = [box(W2 + 0.15 * i, S2 + 0.15 * j, W2 + 0.15 * (i + 1), S2 + 0.15 * (j + 1)) for j in range(3) for i in range(4)]
n_at = rng.integers(800, 6000, 12)
L_z = np.round(rng.uniform(0.15, 0.65, 12), 2)
V_z = np.round(rng.uniform(0.40, 0.65, 12), 2)
upt = np.round(rng.uniform(0.15, 0.50, 12), 2)
z = gpd.GeoDataFrame({"name": [f"District {i + 1}" for i in range(12)], "n_at_risk": n_at, "L": L_z, "V": V_z,
                      "uptake": upt}, geometry=dists, crs=4326)
z.to_file(f"{OUT}/hcc_districts.geojson", driver="GeoJSON")
ctr = gpd.GeoDataFrame({"name": ["Hepatology centre A", "Regional clinic B", "District hospital C"]},
                       geometry=[Point(W2 + 0.10, S2 + 0.10), Point(W2 + 0.45, S2 + 0.30), Point(W2 + 0.20, S2 + 0.40)], crs=4326)
ctr.to_file(f"{OUT}/hcc_centers.geojson", driver="GeoJSON")
# at-risk count raster: 60 x 45 cells of 0.01 deg; each district's count spread uniformly over its 15 x 15 cells
arr = np.zeros((45, 60), dtype="float32")
for k in range(12):
    i, j = k % 4, k // 4
    r0, c0 = (2 - j) * 15, i * 15
    arr[r0:r0 + 15, c0:c0 + 15] = n_at[k] / 225.0
with rasterio.open(f"{OUT}/hcc_at_risk.tif", "w", driver="GTiff", height=45, width=60, count=1, dtype="float32",
                   crs="EPSG:4326", transform=from_origin(W2, S2 + 0.45, 0.01, 0.01), nodata=-9999, compress="deflate") as d:
    d.write(arr, 1)
# patients (simulated)
surv = rng.choice(["none", "usual", "outreach", "specialist", "optimised"], 200, p=[.2, .4, .15, .15, .1])
rows = []
for i in range(200):
    alb, bil = float(np.round(rng.normal(38, 6), 1)), float(np.round(np.exp(rng.normal(2.8, 0.6)), 1))
    rows.append(dict(id=f"P{i + 1:03d}", L=round(float(rng.uniform(0.10, 0.80)), 2), E=round(float(rng.uniform(0.45, 0.8)), 2),
                     albumin=alb, bilirubin=bil, surveillance=surv[i],
                     bclc_if_missed=rng.choice(["0", "A", "early-int", "B", "C-D"], p=[.1, .25, .15, .2, .3]),
                     improved_surveillance="optimised"))
with open(f"{OUT}/hcc_patients_synthetic.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print("written to", os.path.abspath(OUT)); print(sorted(os.listdir(OUT)))

# ---------------- SAR demo (dB; own RNG so earlier files are unchanged) -----------------
rs = np.random.default_rng(7)
def sar_scene(extra, city_patch=True):
    water = dist < (3 + extra)
    base = np.where(water, -21.0, -9.5)                      # calm water dark, land brighter
    lin = 10 ** (base / 10) * rs.gamma(4.4, 1 / 4.4, (100, 100))   # multiplicative speckle (4.4 looks)
    vv = 10 * np.log10(lin)
    vh = 10 * np.log10(10 ** ((base - 6.0) / 10) * rs.gamma(4.4, 1 / 4.4, (100, 100)))
    return np.stack([vv, vh]).astype("float32")
for name, extra in (("pre", 0), ("post", 9)):
    with rasterio.open(f"{OUT}/urban_sar_{name}.tif", "w", driver="GTiff", height=100, width=100, count=2, dtype="float32",
                       crs="EPSG:4326", transform=tr, compress="deflate") as d:
        d.write(sar_scene(extra)); d.descriptions = ("vv", "vh")
print("SAR written")
