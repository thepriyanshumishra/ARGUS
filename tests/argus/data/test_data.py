"""Smoke tests for data module."""

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.transform import from_bounds

from argus.data.cache import ArtifactCache
from argus.data.imagery import RasterImageLoader
from argus.data.preprocessing import create_thumbnail, normalize_image
from argus.data.vector import load_vector_data


class TestImagery:
    """Test raster imagery loading."""

    def test_raster_loader_creation(self):
        loader = RasterImageLoader()
        assert loader is not None
        assert loader.target_crs is not None

    def test_load_synthetic_geotiff(self, tmp_path):
        """Create and load a synthetic GeoTIFF."""
        # Create synthetic GeoTIFF
        path = tmp_path / "test.tif"
        height, width = 100, 100
        data = np.random.randint(0, 255, (3, height, width), dtype=np.uint8)

        transform = from_bounds(0, 0, 1, 1, width, height)
        with rasterio.open(
            path,
            "w",
            driver="GTiff",
            height=height,
            width=width,
            count=3,
            dtype=np.uint8,
            crs=CRS.from_epsg(4326),
            transform=transform,
        ) as dst:
            dst.write(data)

        # Load it
        loader = RasterImageLoader(target_crs=CRS.from_epsg(4326))
        img = loader.load(path)

        assert img.height == height
        assert img.width == width
        assert img.channels == 3
        assert img.crs == "EPSG:4326"
        assert img.bounds == (0.0, 0.0, 1.0, 1.0)

    def test_load_png(self, tmp_path):
        """Load a PNG file."""
        from PIL import Image

        path = tmp_path / "test.png"
        img_pil = Image.fromarray(np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8))
        img_pil.save(path)

        loader = RasterImageLoader(target_crs=CRS.from_epsg(4326))
        img = loader.load(path)

        assert img.height == 100
        assert img.width == 100
        assert img.channels == 3

    def test_crs_conversion(self, tmp_path):
        """Test CRS conversion from Web Mercator to WGS84."""
        # Create synthetic GeoTIFF in EPSG:3857
        path = tmp_path / "test_3857.tif"
        height, width = 100, 100
        data = np.random.randint(0, 255, (3, height, width), dtype=np.uint8)

        # Web Mercator bounds (roughly San Francisco area)
        transform = from_bounds(-13600000, 4500000, -13500000, 4600000, width, height)
        with rasterio.open(
            path,
            "w",
            driver="GTiff",
            height=height,
            width=width,
            count=3,
            dtype=np.uint8,
            crs=CRS.from_epsg(3857),
            transform=transform,
        ) as dst:
            dst.write(data)

        # Load and reproject to EPSG:4326
        loader = RasterImageLoader(target_crs=CRS.from_epsg(4326))
        img = loader.load_and_reproject(path)

        # Should be reprojected to EPSG:4326
        assert img.crs == "EPSG:4326"
        # Bounds should be in lat/lon
        assert -180 <= img.bounds[0] <= 180
        assert -90 <= img.bounds[1] <= 90


class TestVector:
    """Test vector data loading."""

    def test_load_geojson(self, tmp_path):
        """Load a GeoJSON file."""
        # Create synthetic GeoJSON
        path = tmp_path / "test.geojson"
        gdf = gpd.GeoDataFrame(
            {"name": ["A", "B"]},
            geometry=gpd.points_from_xy([0, 1], [0, 1]),
            crs="EPSG:4326",
        )
        gdf.to_file(path, driver="GeoJSON")

        loaded = load_vector_data(path, target_crs="EPSG:4326")
        assert len(loaded) == 2
        assert loaded.crs.to_string() == "EPSG:4326"

    def test_load_shapefile(self, tmp_path):
        """Load a Shapefile."""
        path = tmp_path / "test.shp"
        gdf = gpd.GeoDataFrame(
            {"name": ["A", "B"]},
            geometry=gpd.points_from_xy([0, 1], [0, 1]),
            crs="EPSG:4326",
        )
        gdf.to_file(path)

        loaded = load_vector_data(path, target_crs="EPSG:4326")
        assert len(loaded) == 2

    def test_crs_conversion_vector(self, tmp_path):
        """Test vector CRS conversion."""
        path = tmp_path / "test_3857.geojson"
        gdf = gpd.GeoDataFrame(
            {"name": ["A"]},
            geometry=gpd.points_from_xy([-13600000], [4500000]),
            crs="EPSG:3857",
        )
        gdf.to_file(path, driver="GeoJSON")

        loaded = load_vector_data(path, target_crs="EPSG:4326")
        assert loaded.crs.to_string() == "EPSG:4326"
        # Point should be converted to lat/lon
        assert -180 <= loaded.geometry.x.iloc[0] <= 180


class TestCache:
    """Test artifact caching."""

    def test_cache_creation(self, tmp_path):
        cache = ArtifactCache(cache_dir=tmp_path)
        assert cache.cache_dir.exists()

    def test_cache_save_load_pickle(self, tmp_path):
        cache = ArtifactCache(cache_dir=tmp_path)
        data = {"key": "value", "numbers": [1, 2, 3]}
        cache.save("test", data, format="pickle")
        loaded = cache.load("test", format="pickle")
        assert loaded == data

    def test_cache_save_load_json(self, tmp_path):
        cache = ArtifactCache(cache_dir=tmp_path)
        data = {"key": "value", "numbers": [1, 2, 3]}
        cache.save("test", data, format="json")
        loaded = cache.load("test", format="json")
        assert loaded == data

    def test_cache_save_load_npy(self, tmp_path):
        cache = ArtifactCache(cache_dir=tmp_path)
        data = np.array([1, 2, 3, 4, 5])
        cache.save("test", data, format="npy")
        loaded = cache.load("test", format="npy")
        np.testing.assert_array_equal(loaded, data)

    def test_cache_save_load_geojson(self, tmp_path):
        cache = ArtifactCache(cache_dir=tmp_path)
        gdf = gpd.GeoDataFrame(
            {"name": ["A"]},
            geometry=gpd.points_from_xy([0], [0]),
            crs="EPSG:4326",
        )
        cache.save("test", gdf, format="geojson")
        loaded = cache.load("test", format="geojson")
        assert len(loaded) == 1
        assert loaded.crs.to_string() == "EPSG:4326"

    def test_cache_raster_image_npz(self, tmp_path):
        """Test caching RasterImage via npz format."""
        from argus.core.types import RasterImage

        cache = ArtifactCache(cache_dir=tmp_path)
        img = RasterImage(
            data=np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8),
            crs="EPSG:4326",
            transform=(1.0, 0.0, 0.0, 0.0, -1.0, 0.0),
            bounds=(0, 0, 1, 1),
            metadata={"source": "test"},
        )
        cache.save("test_raster", img, format="npz")
        loaded = cache.load("test_raster", format="npz")

        assert loaded.height == 100
        assert loaded.width == 100
        assert loaded.channels == 3
        assert loaded.crs == "EPSG:4326"
        assert loaded.bounds == (0, 0, 1, 1)
        np.testing.assert_array_equal(loaded.data, img.data)

    def test_cache_road_graph(self, tmp_path):
        """Test caching RoadGraph via graphml + json."""
        import networkx as nx

        from argus.core.types import RoadGraph

        cache = ArtifactCache(cache_dir=tmp_path)
        graph = nx.MultiDiGraph()
        graph.add_node(0, x=0.0, y=0.0, lat=12.97, lon=77.59, degree=1)
        graph.add_node(1, x=1.0, y=1.0, lat=12.98, lon=77.60, degree=1)
        graph.add_edge(0, 1, length=100.0)

        road_graph = RoadGraph(
            graph=graph,
            crs="EPSG:4326",
            bounds=(77.59, 12.97, 77.60, 12.98),
        )

        cache.save_road_graph("test_graph", road_graph)
        loaded = cache.load_road_graph("test_graph")

        assert loaded.node_count == 2
        assert loaded.edge_count == 1
        assert loaded.crs == "EPSG:4326"

    def test_cache_exists(self, tmp_path):
        cache = ArtifactCache(cache_dir=tmp_path)
        cache.save("test", "data", format="pickle")
        assert cache.exists("test", format="pickle")
        assert not cache.exists("missing", format="pickle")

    def test_cache_clear(self, tmp_path):
        cache = ArtifactCache(cache_dir=tmp_path)
        cache.save("test1", "data", format="pickle")
        cache.save("test2", "data", format="pickle")
        cache.clear("test1")
        assert not cache.exists("test1", format="pickle")
        assert cache.exists("test2", format="pickle")
        cache.clear()
        assert not cache.exists("test2", format="pickle")


class TestPreprocessing:
    """Test preprocessing utilities."""

    def test_normalize_minmax(self):
        data = np.array([0, 50, 100, 200, 255], dtype=np.uint8)
        norm = normalize_image(data, method="minmax")
        assert norm.min() == 0.0
        assert norm.max() == 1.0

    def test_normalize_standardize(self):
        data = np.array([10, 20, 30, 40, 50], dtype=np.float32)
        norm = normalize_image(data, method="standardize")
        assert abs(norm.mean()) < 1e-6
        assert abs(norm.std() - 1.0) < 1e-6

    def test_normalize_constant(self):
        data = np.full((10, 10), 100, dtype=np.uint8)
        norm = normalize_image(data, method="minmax")
        assert np.all(norm == 0)

    def test_thumbnail_generation(self):
        from argus.core.types import RasterImage

        img = RasterImage(
            data=np.random.randint(0, 255, (512, 512, 3), dtype=np.uint8),
            crs="EPSG:4326",
            transform=(1.0, 0.0, 0.0, 0.0, -1.0, 0.0),
            bounds=(0, 0, 1, 1),
        )
        thumb = create_thumbnail(img, max_size=64)

        assert thumb.shape[0] <= 64
        assert thumb.shape[1] <= 64
        assert thumb.max() <= 1.0
        assert thumb.min() >= 0.0


class TestIntegration:
    """Integration tests."""

    def test_ingest_roundtrip(self, tmp_path):
        """Test full ingest: load -> cache -> reload -> verify."""
        # Create test GeoTIFF
        path = tmp_path / "test.tif"
        height, width = 200, 200
        data = np.random.randint(0, 255, (3, height, width), dtype=np.uint8)
        transform = from_bounds(0, 0, 1, 1, width, height)

        with rasterio.open(
            path,
            "w",
            driver="GTiff",
            height=height,
            width=width,
            count=3,
            dtype=np.uint8,
            crs=CRS.from_epsg(4326),
            transform=transform,
        ) as dst:
            dst.write(data)

        # Load
        loader = RasterImageLoader(target_crs=CRS.from_epsg(4326))
        img = loader.load(path)

        # Cache
        cache = ArtifactCache(cache_dir=tmp_path / "cache")
        cache.save("roundtrip_test", img, format="npz")

        # Reload
        loaded = cache.load("roundtrip_test", format="npz")

        # Verify
        assert loaded.height == img.height
        assert loaded.width == img.width
        assert loaded.crs == img.crs
        assert loaded.bounds == img.bounds
        np.testing.assert_array_equal(loaded.data, img.data)
