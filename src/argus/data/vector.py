"""Vector data loading with GeoPandas."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
from geopandas import GeoDataFrame

from argus.core.logging import get_logger

log = get_logger(__name__)


def load_vector_data(path: str | Path, target_crs: str = "EPSG:4326") -> GeoDataFrame:
    """Load vector data (GeoJSON, Shapefile) as GeoDataFrame."""
    path = Path(path)
    log.info(f"Loading vector data: {path}")

    gdf = gpd.read_file(path)

    if gdf.crs is None:
        log.warning("No CRS found in vector data; assuming EPSG:4326")
        gdf = gdf.set_crs("EPSG:4326")

    if gdf.crs is not None and str(gdf.crs) != target_crs:
        log.info(f"Reprojecting from {gdf.crs} to {target_crs}")
        gdf = gdf.to_crs(target_crs)

    return gdf
