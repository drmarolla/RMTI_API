"""Self-contained geospatial demo on synthetic layers (needs: pip install "rmti-py[geo]")."""
import tempfile, os
import numpy as np, geopandas as gpd, rasterio
from rasterio.transform import from_origin
from shapely.geometry import LineString, box
from rmti.geospatial import compute_spatial_exposure
from rmti import score

d = tempfile.mkdtemp(); path = os.path.join(d, "pop.tif")
with rasterio.open(path, "w", driver="GTiff", height=10, width=10, count=1, dtype="float32", crs="EPSG:4326",
                   transform=from_origin(3.30, 6.60, 0.01, 0.01), nodata=-9999) as dst:
    dst.write(np.full((10, 10), 5000, dtype="float32"), 1)          # 500,000 people
city = gpd.GeoDataFrame(geometry=[box(3.30, 6.50, 3.40, 6.60)], crs="EPSG:4326")
flood = gpd.GeoDataFrame(geometry=[box(3.30, 6.50, 3.36, 6.55), box(3.33, 6.50, 3.40, 6.56)], crs="EPSG:4326")
transit = gpd.GeoDataFrame(geometry=[LineString([(3.30, 6.52), (3.40, 6.52)]), LineString([(3.35, 6.50), (3.35, 6.60)])], crs="EPSG:4326")
x = compute_spatial_exposure(transit, flood, city, path)
print(x)
print(score(L=0.9, E_sel=x.E_sel, V=0.8, rho=0.2, C=5))   # E_sel feeds the index; L, V, rho remain analyst inputs
