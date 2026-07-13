"""Unit tests for Stage 1 improvements."""

import networkx as nx
import numpy as np
import pytest
import rasterio
from argus.core.types import RasterImage, RoadGraph
from argus.data.cache import ArtifactCache, calculate_array_hash
from argus.data.imagery import RasterImageLoader
from argus.data.preprocessing import estimate_utm_crs, normalize_image
from omegaconf.errors import ValidationError
from rasterio.crs import CRS
from rasterio.transform import from_bounds


def test_config_type_validation_invalid():
    """Verify that configuration schema validation catches type errors."""
    # Try loading a valid config to make sure loading works
    config = load_config("data")
    assert config is not None

    # Verify that load_config raises ValidationError if schema is violated
    from argus.core.config import SCHEMAS
    from omegaconf import OmegaConf

    schema = OmegaConf.structured(SCHEMAS["data"])

    # Passing an invalid type to supported_formats (e.g., integer instead of list)
    with pytest.raises(ValidationError):
        OmegaConf.merge(schema, {"supported_formats": 1234})


def test_estimate_utm_crs():
    """Verify that UTM zone estimation works correctly for known regions."""
    # Bengaluru area (~12.97, 77.59)
    crs = estimate_utm_crs((77.5, 12.9, 77.6, 13.0))
    # Bengaluru is in UTM Zone 43N (EPSG:32643)
    assert crs.to_epsg() == 32643

    # London area (~51.5, -0.12)
    crs_london = estimate_utm_crs((-0.2, 51.4, 0.0, 51.6))
    # London is in UTM Zone 30N (EPSG:32630)
    assert crs_london.to_epsg() == 32630


def test_percentile_normalization():
    """Verify that percentile normalization clips extreme outliers and standardizes to [0, 1]."""
    # Create array with extreme outliers
    data = np.array([0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 10000], dtype=np.float32)
    norm = normalize_image(data, method="percentile", percentiles=(10.0, 90.0))

    assert norm.min() == 0.0
    assert norm.max() == 1.0
    # Outliers should be clipped (the 10000 should be clipped to the 90th percentile)
    assert norm[-1] == 1.0
    assert norm[0] == 0.0


def test_raster_loader_band_mapping_and_normalization(tmp_path):
    """Verify band mapping and percentile normalization during ingestion."""
    # Create a 4-band synthetic 16-bit GeoTIFF (like Sentinel-2)
    path = tmp_path / "sentinel.tif"
    height, width = 64, 64
    # Outlier values in 16-bit range
    data = np.random.randint(500, 2000, (4, height, width), dtype=np.uint16)
    data[0, 10, 10] = 60000  # Highlight/Outlier

    transform = from_bounds(0, 0, 1, 1, width, height)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=4,
        dtype=np.uint16,
        crs=CRS.from_epsg(4326),
        transform=transform,
    ) as dst:
        dst.write(data)

    # Load only bands 4, 3, 2 (RGB for Sentinel)
    loader = RasterImageLoader(
        target_crs=CRS.from_epsg(4326),
        band_indices=[4, 3, 2],
        normalize_method="percentile",
    )
    img = loader.load(path)

    assert img.height == height
    assert img.width == width
    assert img.channels == 3
    assert img.data.dtype == np.uint8  # Must be uint8 after scaling!
    assert img.metadata["loaded_bands"] == [4, 3, 2]


def test_cache_checksum_validation(tmp_path):
    """Verify hash validation during cache load."""
    cache = ArtifactCache(cache_dir=tmp_path)

    img1 = RasterImage(
        data=np.random.randint(0, 255, (32, 32, 3), dtype=np.uint8),
        crs="EPSG:4326",
        transform=(1.0, 0.0, 0.0, 0.0, -1.0, 0.0),
        bounds=(0, 0, 1, 1),
    )
    img2 = RasterImage(
        data=np.random.randint(0, 255, (32, 32, 3), dtype=np.uint8),
        crs="EPSG:4326",
        transform=(1.0, 0.0, 0.0, 0.0, -1.0, 0.0),
        bounds=(0, 0, 1, 1),
    )

    h1 = calculate_array_hash(img1.data)
    h2 = calculate_array_hash(img2.data)

    # Save img1 to cache
    cache.save("my_image", img1, format="npz")

    # Load with correct expected hash -> succeeds
    loaded = cache.load("my_image", format="npz", expected_hash=h1)
    assert np.array_equal(loaded.data, img1.data)

    # Load with mismatched expected hash -> raises FileNotFoundError (cache validation miss)
    with pytest.raises(FileNotFoundError):
        cache.load("my_image", format="npz", expected_hash=h2)


def test_road_graph_cache_checksum_validation(tmp_path):
    """Verify hash validation on RoadGraph loading."""
    cache = ArtifactCache(cache_dir=tmp_path)

    g = nx.MultiDiGraph()
    g.add_node(0, x=0.0, y=0.0, lat=12.9, lon=77.5, degree=1)
    g.add_node(1, x=1.0, y=1.0, lat=13.0, lon=77.6, degree=1)
    g.add_edge(0, 1, length=10.0)

    road_graph = RoadGraph(graph=g, crs="EPSG:4326", bounds=(77.5, 12.9, 77.6, 13.0))

    # Save with a specific source image hash
    source_hash = "abc123xyz"
    cache.save_road_graph("my_graph", road_graph, source_hash=source_hash)

    # Load with correct expected hash -> succeeds
    loaded = cache.load_road_graph("my_graph", expected_hash=source_hash)
    assert loaded.node_count == 2

    # Load with incorrect expected hash -> raises FileNotFoundError
    with pytest.raises(FileNotFoundError):
        cache.load_road_graph("my_graph", expected_hash="wronghash")
