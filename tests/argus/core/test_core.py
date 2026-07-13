"""Smoke tests for core module."""

import networkx as nx
import numpy as np
from argus.core.config import load_config
from argus.core.logging import get_logger, setup_logging
from argus.core.protocols import (
    CriticalityAnalyzer,
    DisasterSimulator,
    RoadExtractor,
    RoadGraphBuilder,
    Router,
)
from argus.core.types import RasterImage, RoadGraph, RoadMask


class TestCoreTypes:
    """Test core data types."""

    def test_raster_image_creation(self):
        # Data shape is (H, W, C) = (256, 256, 3)
        data = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
        img = RasterImage(
            data=data,
            crs="EPSG:4326",
            transform=(1.0, 0.0, 0.0, 0.0, -1.0, 0.0),
            bounds=(0, 0, 1, 1),
        )
        assert img.height == 256
        assert img.width == 256
        assert img.channels == 3

    def test_road_mask_creation(self):
        mask = np.zeros((256, 256), dtype=bool)
        mask[100:150, 100:150] = True
        road_mask = RoadMask(
            mask=mask,
            crs="EPSG:4326",
            transform=(1.0, 0.0, 0.0, 0.0, -1.0, 0.0),
            bounds=(0, 0, 1, 1),
            model_name="test",
            model_version="1.0",
        )
        assert road_mask.mask.shape == (256, 256)
        assert road_mask.mask.sum() == 2500

    def test_road_graph_creation(self):
        graph = nx.MultiDiGraph()
        graph.add_node(0, x=0.0, y=0.0, lat=12.97, lon=77.59)
        graph.add_node(1, x=1.0, y=1.0, lat=12.98, lon=77.60)
        graph.add_edge(0, 1, length=100.0)

        road_graph = RoadGraph(
            graph=graph,
            crs="EPSG:4326",
            bounds=(77.59, 12.97, 77.60, 12.98),
        )
        assert road_graph.node_count == 2
        assert road_graph.edge_count == 1


class TestProtocols:
    """Test that protocols are properly defined."""

    def test_protocols_exist(self):
        assert RoadExtractor is not None
        assert RoadGraphBuilder is not None
        assert CriticalityAnalyzer is not None
        assert DisasterSimulator is not None
        assert Router is not None


class TestConfig:
    """Test configuration loading."""

    def test_load_data_config(self):
        config = load_config("data")
        assert config is not None
        assert hasattr(config, "target_crs")

    def test_load_vision_config(self):
        config = load_config("vision")
        assert config is not None
        assert hasattr(config, "model")
        assert config.model.type == "sam_road"


class TestLogging:
    """Test logging setup."""

    def test_setup_logging(self):
        setup_logging("DEBUG")
        logger = get_logger("test")
        assert logger is not None
