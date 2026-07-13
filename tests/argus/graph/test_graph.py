"""Tests for M3 Graph Pipeline."""

import networkx as nx
import numpy as np
import pytest
from argus.core.errors import InvalidMaskError, MissingGeoMetadataError
from argus.core.types import RoadGraph, RoadMask
from argus.graph.builder import RoadGraphBuilderImpl
from argus.graph.cleaning import (
    merge_close_nodes,
    remove_dangling_nodes,
    remove_isolated_small_components,
    simplify_chains,
)
from argus.graph.export import (
    export_geojson,
    export_graphml,
    export_pickle,
    load_pickle,
)
from argus.graph.loader import load_mask_from_file
from argus.graph.skeleton import skeletonize_mask
from argus.graph.trace import skeleton_to_graph, skeleton_to_graph_custom

# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


def _make_simple_cross_mask(h=64, w=64) -> RoadMask:
    """Create a cross-shaped test mask."""
    mask_arr = np.zeros((h, w), dtype=bool)
    mask_arr[h // 2, 10 : w - 10] = True
    mask_arr[10 : h - 10, w // 2] = True
    return RoadMask(
        mask=mask_arr,
        crs="EPSG:4326",
        transform=(0.001, 0.0, 12.97, 0.0, -0.001, 77.59),
        bounds=(12.97, 77.59, 13.03, 77.65),
        model_name="test",
        model_version="1.0",
    )


# ------------------------------------------------------------------
# Skeletonization
# ------------------------------------------------------------------


class TestSkeletonization:
    def test_skeletonize_empty_mask(self):
        skel = skeletonize_mask(np.zeros((32, 32), dtype=bool))
        assert skel.sum() == 0

    def test_skeletonize_cross(self):
        mask = np.zeros((64, 64), dtype=bool)
        mask[32, 10:54] = True
        mask[10:54, 32] = True
        skel = skeletonize_mask(mask)
        assert skel.sum() > 0

    def test_skeletonize_multi_part(self):
        mask = np.zeros((100, 100), dtype=bool)
        mask[30, 10:50] = True
        mask[70, 50:90] = True
        skel = skeletonize_mask(mask)
        assert skel.sum() > 0


# ------------------------------------------------------------------
# Tracing
# ------------------------------------------------------------------


class TestSkeletonToGraph:
    def test_empty_skeleton(self):
        g = skeleton_to_graph(np.zeros((32, 32), dtype=bool))
        assert g.number_of_nodes() == 0

    def test_simple_line(self):
        skel = np.zeros((64, 64), dtype=bool)
        skel[32, 10:54] = True
        g = skeleton_to_graph_custom(skel)
        assert g.number_of_nodes() >= 2  # at least endpoints
        assert g.number_of_edges() >= 1

    def test_cross_graph(self):
        mask = _make_simple_cross_mask()
        skel = skeletonize_mask(mask.mask)
        g = skeleton_to_graph_custom(skel)
        assert g.number_of_nodes() >= 5  # 4 endpoints + junction cluster
        assert g.number_of_edges() >= 4

    def test_nodes_have_coordinates(self):
        mask = _make_simple_cross_mask()
        skel = skeletonize_mask(mask.mask)
        g = skeleton_to_graph_custom(skel)
        for _, data in g.nodes(data=True):
            assert "x" in data
            assert "y" in data


# ------------------------------------------------------------------
# Cleaning
# ------------------------------------------------------------------


class TestCleaning:
    def test_remove_small_components(self):
        g = nx.MultiDiGraph()
        g.add_node(0, x=0.0, y=0.0)
        g.add_node(1, x=1.0, y=1.0)
        g.add_edge(0, 1, length_px=1.0)
        g.add_node(2, x=100.0, y=100.0)  # isolated
        g.add_node(3, x=101.0, y=101.0)  # isolated
        g.add_edge(2, 3, length_px=1.0)

        cleaned = remove_isolated_small_components(g, min_nodes=3)
        assert cleaned.number_of_nodes() == 2

    def test_keep_larger_component(self):
        g = nx.MultiDiGraph()
        # 5-node component
        for i in range(5):
            g.add_node(i, x=float(i), y=0.0)
        for i in range(4):
            g.add_edge(i, i + 1, length_px=1.0)
        # 2-node small component
        g.add_node(100, x=100.0, y=100.0)
        g.add_node(101, x=101.0, y=101.0)
        g.add_edge(100, 101, length_px=1.0)

        cleaned = remove_isolated_small_components(g, min_nodes=3)
        assert cleaned.number_of_nodes() == 5

    def test_merge_close_nodes(self):
        g = nx.MultiDiGraph()
        g.add_node(0, x=0.0, y=0.0)
        g.add_node(1, x=1.0, y=1.0)  # close to 0
        g.add_node(2, x=100.0, y=100.0)
        g.add_edge(0, 1, length_px=1.0)
        g.add_edge(0, 2, length_px=100.0)

        merged = merge_close_nodes(g, merge_distance=3.0)
        assert merged.number_of_nodes() < 3

    def test_remove_dangling_nodes(self):
        g = nx.MultiDiGraph()
        g.add_node(0, x=0.0, y=0.0)
        g.add_node(1, x=10.0, y=0.0)
        g.add_node(2, x=10.0, y=1.0)  # short dangling
        g.add_edge(0, 1, length_px=10.0)
        g.add_edge(1, 2, length_px=1.5)

        cleaned = remove_dangling_nodes(g, max_length=3.0)
        assert cleaned.number_of_nodes() == 2

    def test_simplify_chains(self):
        g = nx.MultiDiGraph()
        g.add_node(0, x=0.0, y=0.0)
        g.add_node(1, x=5.0, y=0.0)  # degree-2 intermediate
        g.add_node(2, x=10.0, y=0.0)
        g.add_edge(0, 1, path_pixels=[(0.0, 0.0), (5.0, 0.0)], length_px=5.0)
        g.add_edge(1, 2, path_pixels=[(5.0, 0.0), (10.0, 0.0)], length_px=5.0)

        simplified = simplify_chains(g, tolerance=2.0)
        assert simplified.number_of_nodes() == 2
        assert simplified.has_edge(0, 2)


# ------------------------------------------------------------------
# Builder
# ------------------------------------------------------------------


class TestGraphBuilder:
    def test_builder_creation(self):
        builder = RoadGraphBuilderImpl()
        assert builder is not None

    def test_builder_with_config(self):
        config = {
            "simplification": {"tolerance": 1.0},
            "cleaning": {
                "merge_distance": 3.0,
                "min_component_size": 5,
            },
        }
        builder = RoadGraphBuilderImpl(config)
        assert builder.simplification_tolerance == 1.0
        assert builder.merge_distance == 3.0
        assert builder.min_component_size == 5

    def test_build_from_mask(self):
        mask = _make_simple_cross_mask()
        builder = RoadGraphBuilderImpl(
            {
                "cleaning": {"merge_close_nodes": True, "merge_distance": 3.0},
                "simplification": {"enabled": True, "tolerance": 2.0},
            }
        )
        graph = builder.build(mask)
        assert isinstance(graph, RoadGraph)
        assert graph.node_count > 0
        assert graph.edge_count > 0
        assert graph.crs == "EPSG:4326"

        # Node attributes present per IP-3 contract
        for _, data in graph.graph.nodes(data=True):
            assert "lat" in data
            assert "lon" in data
            assert "x" in data
            assert "y" in data
            assert "degree" in data

    def test_metadata_stores_transform(self):
        """RoadGraph.metadata should contain the affine transform for accurate exports."""
        mask = _make_simple_cross_mask()
        builder = RoadGraphBuilderImpl()
        graph = builder.build(mask)
        assert "transform" in graph.metadata
        assert graph.metadata["transform"] == mask.transform

    def test_config_override_works(self):
        """Passing config override to build() should take effect."""
        mask = _make_simple_cross_mask()
        builder = RoadGraphBuilderImpl()
        # Override with a large merge_distance to collapse everything
        builder.build(mask, config={"cleaning": {"merge_distance": 100.0}})
        assert builder.merge_distance == 100.0

    def test_build_empty_mask(self):
        mask = RoadMask(
            mask=np.zeros((32, 32), dtype=bool),
            crs="EPSG:4326",
            transform=(1.0, 0.0, 0.0, 0.0, -1.0, 0.0),
            bounds=(0, 0, 1, 1),
            model_name="test",
            model_version="1.0",
        )
        builder = RoadGraphBuilderImpl()
        graph = builder.build(mask)
        assert graph.node_count == 0

    def test_invalid_mask_raises(self):
        builder = RoadGraphBuilderImpl()
        with pytest.raises(InvalidMaskError):
            builder.build(
                RoadMask(
                    mask=np.array([]),  # type: ignore[arg-type]
                    crs="EPSG:4326",
                    transform=(1.0, 0.0, 0.0, 0.0, -1.0, 0.0),
                    bounds=(0, 0, 1, 1),
                    model_name="test",
                    model_version="1.0",
                )
            )

    def test_missing_crs_raises(self):
        builder = RoadGraphBuilderImpl()
        with pytest.raises(MissingGeoMetadataError):
            builder.build(
                RoadMask(
                    mask=np.zeros((32, 32), dtype=bool),
                    crs="",
                    transform=(1.0, 0.0, 0.0, 0.0, -1.0, 0.0),
                    bounds=(0, 0, 1, 1),
                    model_name="test",
                    model_version="1.0",
                )
            )


# ------------------------------------------------------------------
# Export
# ------------------------------------------------------------------


class TestGraphExport:
    def test_export_pickle_roundtrip(self, tmp_path):
        g = nx.MultiDiGraph()
        g.add_node(0, x=0.0, y=0.0, lat=12.97, lon=77.59)
        g.add_node(1, x=1.0, y=1.0, lat=12.98, lon=77.60)
        g.add_edge(0, 1, length_px=100.0)

        road_graph = RoadGraph(
            graph=g,
            crs="EPSG:4326",
            bounds=(77.59, 12.97, 77.60, 12.98),
        )

        path = tmp_path / "test.pkl"
        export_pickle(road_graph, path)
        assert path.exists()

        loaded = load_pickle(path)
        assert isinstance(loaded, RoadGraph)
        assert loaded.node_count == 2
        assert loaded.edge_count == 1

    def test_export_graphml(self, tmp_path):
        road_graph = RoadGraph(
            graph=nx.MultiDiGraph(),
            crs="EPSG:4326",
            bounds=(0, 0, 1, 1),
        )
        road_graph.graph.add_node(0, x=1.0, y=0.0, lat=0.0, lon=1.0)
        road_graph.graph.add_node(1, x=2.0, y=0.0, lat=0.0, lon=2.0)
        road_graph.graph.add_edge(0, 1, length_px=1.0)

        path = tmp_path / "test.graphml"
        export_graphml(road_graph, path)
        assert path.exists()
        assert path.stat().st_size > 0

    def test_export_geojson(self, tmp_path):
        road_graph = RoadGraph(
            graph=nx.MultiDiGraph(),
            crs="EPSG:4326",
            bounds=(0, 0, 1, 1),
        )
        road_graph.graph.add_node(0, x=1.0, y=0.0, lat=0.0, lon=1.0)
        road_graph.graph.add_node(1, x=2.0, y=0.0, lat=0.0, lon=2.0)
        road_graph.graph.add_edge(0, 1, path_pixels=[(1.0, 0.0), (2.0, 0.0)], length_px=1.0)

        path = tmp_path / "test.geojson"
        export_geojson(road_graph, path)
        nodes_path = tmp_path / "test_nodes.geojson"
        edges_path = tmp_path / "test_edges.geojson"
        assert nodes_path.exists()
        assert edges_path.exists()

    def test_export_geojson_valid(self, tmp_path):
        """GeoJSON should be parseable as valid JSON."""
        import json

        g = nx.MultiDiGraph()
        g.add_node(0, x=0.0, y=0.0, lat=0.0, lon=0.0)
        g.add_node(1, x=1.0, y=0.0, lat=0.0, lon=1.0)
        g.add_edge(0, 1, path_pixels=[(0.0, 0.0), (1.0, 0.0)], length_px=1.0)

        road_graph = RoadGraph(graph=g, crs="EPSG:4326", bounds=(0, 0, 1, 1))
        path = tmp_path / "test.geojson"
        export_geojson(road_graph, path)

        with open(tmp_path / "test_nodes.geojson") as f:
            node_json = json.load(f)
        assert node_json["type"] == "FeatureCollection"
        assert len(node_json["features"]) == 2

        with open(tmp_path / "test_edges.geojson") as f:
            edge_json = json.load(f)
        assert edge_json["type"] == "FeatureCollection"
        assert len(edge_json["features"]) == 1

    def test_export_geojson_uses_stored_transform(self, tmp_path):
        """GeoJSON edge geometry should use the exact transform from metadata."""
        import json

        g = nx.MultiDiGraph()
        g.add_node(0, x=0.0, y=0.0, lat=77.59, lon=12.97)
        g.add_node(1, x=10.0, y=0.0, lat=77.59, lon=12.98)
        g.add_edge(0, 1, path_pixels=[(0.0, 0.0), (5.0, 0.0), (10.0, 0.0)], length_px=10.0)

        # Non-trivial transform: scale = 0.001, offset = (12.97, 77.59)
        road_graph = RoadGraph(
            graph=g,
            crs="EPSG:4326",
            bounds=(12.97, 77.59, 12.98, 77.60),
            metadata={"transform": (0.001, 0.0, 12.97, 0.0, 0.001, 77.59)},
        )
        path = tmp_path / "test.geojson"
        export_geojson(road_graph, path)

        with open(tmp_path / "test_edges.geojson") as f:
            edge_json = json.load(f)
        coords = edge_json["features"][0]["geometry"]["coordinates"]
        # First point: (0,0) → (12.97, 77.59)
        assert coords[0] == [12.97, 77.59]
        # Middle point: (5,0) → (12.975, 77.59)
        assert abs(coords[1][0] - 12.975) < 0.0001
        assert abs(coords[1][1] - 77.59) < 0.0001


# ------------------------------------------------------------------
# Mask loader
# ------------------------------------------------------------------


class TestMaskLoader:
    def test_load_png(self, tmp_path):
        from PIL import Image

        arr = np.zeros((32, 32), dtype=np.uint8)
        arr[16, 8:24] = 255
        path = tmp_path / "test.png"
        Image.fromarray(arr).save(path)

        mask = load_mask_from_file(path)
        assert mask.mask.shape == (32, 32)
        assert mask.mask.sum() == 16

    def test_load_npy(self, tmp_path):
        arr = np.zeros((32, 32), dtype=np.bool_)
        arr[16, 8:24] = True
        path = tmp_path / "test.npy"
        np.save(path, arr)

        mask = load_mask_from_file(path)
        assert mask.mask.shape == (32, 32)
        assert mask.mask.sum() == 16

    def test_load_invalid_raises(self, tmp_path):
        path = tmp_path / "test.xyz"
        path.write_text("not a mask")
        with pytest.raises(InvalidMaskError):
            load_mask_from_file(path)


# ------------------------------------------------------------------
# Integration
# ------------------------------------------------------------------


class TestFullPipeline:
    """End-to-end: synthetic mask → build → export → reload."""

    def test_pipeline(self, tmp_path):
        # 1. Create mask
        mask = _make_simple_cross_mask()

        # 2. Build graph
        builder = RoadGraphBuilderImpl(
            {
                "cleaning": {
                    "merge_close_nodes": True,
                    "merge_distance": 3.0,
                    "remove_dangling": True,
                    "max_dangling_length": 3.0,
                },
                "simplification": {"enabled": True, "tolerance": 2.0},
            }
        )
        graph = builder.build(mask)
        assert graph.node_count > 0
        assert graph.edge_count > 0

        # 3. Export pickle
        pkl_path = tmp_path / "graph.pkl"
        export_pickle(graph, pkl_path)
        assert pkl_path.exists()

        # 4. Reload and verify
        reloaded = load_pickle(pkl_path)
        assert reloaded.node_count == graph.node_count
        assert reloaded.edge_count == graph.edge_count
        assert reloaded.crs == graph.crs

        # 5. Export GraphML
        gml_path = tmp_path / "graph.graphml"
        export_graphml(graph, gml_path)
        assert gml_path.exists()

        # 6. Export GeoJSON
        geojson_path = tmp_path / "graph.geojson"
        export_geojson(graph, geojson_path)
        assert (tmp_path / "graph_nodes.geojson").exists()
        assert (tmp_path / "graph_edges.geojson").exists()
