"""Tests for M6 Routing Engine."""

import json
import tempfile
from pathlib import Path

import networkx as nx
from argus.core.types import RoadGraph
from argus.routing.router import (
    AccessibilityQuery,
    RouteQuery,
    RouterImpl,
    export_route_geojson,
)


def _make_grid_graph(lat0: float = 12.97, lon0: float = 77.59, step: float = 0.01):
    g = nx.MultiDiGraph()
    for i in range(9):
        x, y = i % 3, i // 3
        g.add_node(i, lat=lat0 + y * step, lon=lon0 + x * step)
    for i in range(9):
        if i % 3 < 2:
            g.add_edge(i, i + 1, length=100.0)
        if i // 3 < 2:
            g.add_edge(i, i + 3, length=100.0)
    return g


def _make_grid_road_graph():
    g = _make_grid_graph()
    return RoadGraph(
        graph=g,
        crs="EPSG:4326",
        bounds=(77.59, 12.97, 77.61, 12.99),
    )


class TestRouter:
    def test_router_creation(self):
        r = RouterImpl()
        assert r.default_algorithm == "dijkstra"

    def test_router_with_config(self):
        r = RouterImpl({"default_algorithm": "astar", "accessibility": {"speed_kmh": 60}})
        assert r.default_algorithm == "astar"
        assert r._speed_kmh == 60

    def test_dijkstra_shortest_path(self):
        rg = _make_grid_road_graph()
        router = RouterImpl()
        q = RouteQuery(origin=(12.97, 77.59), destination=(12.99, 77.61))
        result = router.find_route(rg, q)

        assert len(result.routes) == 1
        route = result.routes[0]
        assert route["geometry"]["type"] == "LineString"
        coords = route["geometry"]["coordinates"]
        assert len(coords) >= 2
        props = route["properties"]
        assert props["length_m"] > 0
        assert props["travel_time_s"] > 0
        assert "nodes" in props

    def test_astar_shortest_path(self):
        rg = _make_grid_road_graph()
        router = RouterImpl()
        q = RouteQuery(origin=(12.97, 77.59), destination=(12.99, 77.61), algorithm="astar")
        result = router.find_route(rg, q)
        assert len(result.routes) == 1
        assert result.routes[0]["geometry"]["type"] == "LineString"

    def test_k_shortest_multiple_routes(self):
        g = nx.MultiDiGraph()
        g.add_node(0, lat=12.97, lon=77.59)
        g.add_node(1, lat=12.97, lon=77.60)
        g.add_node(2, lat=12.975, lon=77.595)
        g.add_node(3, lat=12.98, lon=77.60)
        g.add_edge(0, 1, length=100.0)
        g.add_edge(0, 2, length=70.0)
        g.add_edge(2, 1, length=70.0)
        g.add_edge(2, 3, length=70.0)
        g.add_edge(1, 3, length=100.0)
        rg = RoadGraph(
            graph=g,
            crs="EPSG:4326",
            bounds=(77.59, 12.97, 77.60, 12.98),
        )
        router = RouterImpl()
        q = RouteQuery(
            origin=(12.97, 77.59), destination=(12.98, 77.60), algorithm="k_shortest", k=3
        )
        result = router.find_route(rg, q)
        assert len(result.routes) >= 1

    def test_no_path_returns_empty(self):
        g = nx.MultiDiGraph()
        g.add_node(0, lat=12.97, lon=77.59)
        g.add_node(1, lat=13.00, lon=77.70)
        rg = RoadGraph(
            graph=g,
            crs="EPSG:4326",
            bounds=(77.59, 12.97, 77.70, 13.00),
        )
        router = RouterImpl()
        q = RouteQuery(origin=(12.97, 77.59), destination=(13.00, 77.70))
        result = router.find_route(rg, q)
        assert len(result.routes) == 0

    def test_travel_time_uses_speed(self):
        rg = _make_grid_road_graph()
        router = RouterImpl({"accessibility": {"speed_kmh": 72}})
        q = RouteQuery(origin=(12.97, 77.59), destination=(12.99, 77.61))
        result = router.find_route(rg, q)
        travel_time = result.routes[0]["properties"]["travel_time_s"]
        # 72 km/h = 20 m/s, so travel_time < length/20 approx
        assert travel_time > 0

    def test_length_px_fallback(self):
        """Router detects length_px as weight when length is absent."""
        g = nx.MultiDiGraph()
        g.add_node(0, lat=12.97, lon=77.59)
        g.add_node(1, lat=12.97, lon=77.60)
        g.add_edge(0, 1, length_px=100.0)
        rg = RoadGraph(
            graph=g,
            crs="EPSG:4326",
            bounds=(77.59, 12.97, 77.60, 12.97),
        )
        router = RouterImpl()
        q = RouteQuery(origin=(12.97, 77.59), destination=(12.97, 77.60))
        result = router.find_route(rg, q)
        assert len(result.routes) == 1
        assert result.routes[0]["properties"]["length_m"] == 100.0

    def test_unknown_algorithm_falls_back(self):
        rg = _make_grid_road_graph()
        router = RouterImpl()
        q = RouteQuery(origin=(12.97, 77.59), destination=(12.99, 77.61), algorithm="nonsense")
        result = router.find_route(rg, q)
        assert len(result.routes) == 1


class TestAccessibility:
    def test_reachable_unreachable(self):
        g = nx.MultiDiGraph()
        g.add_node(0, lat=12.97, lon=77.59)
        g.add_node(1, lat=12.97, lon=77.60)
        g.add_node(2, lat=13.00, lon=77.70)
        g.add_edge(0, 1, length=100.0)
        rg = RoadGraph(
            graph=g,
            crs="EPSG:4326",
            bounds=(77.59, 12.97, 77.70, 13.00),
        )
        router = RouterImpl()
        q = AccessibilityQuery(
            origins=[(12.97, 77.59)],
            destinations=[(12.97, 77.60), (13.00, 77.70)],
        )
        result = router.accessibility(rg, q)
        origin_key = str((12.97, 77.59))
        assert len(result[origin_key]["reachable"]) >= 1
        assert len(result[origin_key]["unreachable"]) >= 1


class TestComparison:
    def test_compare_routes(self):
        base = [
            {
                "geometry": {"type": "LineString", "coordinates": [[77.59, 12.97], [77.60, 12.98]]},
                "properties": {"length_m": 100.0, "travel_time_s": 10.0, "nodes": [0, 1, 2]},
            }
        ]
        modified = [
            {
                "geometry": {"type": "LineString", "coordinates": [[77.59, 12.97], [77.61, 12.98]]},
                "properties": {"length_m": 200.0, "travel_time_s": 20.0, "nodes": [0, 3, 2]},
            }
        ]
        router = RouterImpl()
        cmp = router.compare_routes(base, modified)
        assert cmp["baseline_length_m"] == 100.0
        assert cmp["modified_length_m"] == 200.0
        assert cmp["delta_length_m"] == 100.0
        assert cmp["status"] == "detour"

    def test_compare_unreachable(self):
        base = [
            {
                "geometry": {"type": "LineString", "coordinates": [[77.59, 12.97], [77.60, 12.98]]},
                "properties": {"length_m": 100.0, "travel_time_s": 10.0, "nodes": [0, 1, 2]},
            }
        ]
        router = RouterImpl()
        cmp = router.compare_routes(base, [])
        assert cmp["status"] == "unreachable"

    def test_compare_same_route(self):
        route = [
            {
                "geometry": {"type": "LineString", "coordinates": [[77.59, 12.97], [77.60, 12.98]]},
                "properties": {"length_m": 100.0, "travel_time_s": 10.0, "nodes": [0, 1, 2]},
            }
        ]
        router = RouterImpl()
        cmp = router.compare_routes(route, route)
        assert cmp["delta_length_m"] == 0.0
        assert cmp["status"] == "unchanged"


class TestExport:
    def test_export_route_geojson(self):
        routes = [
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[77.59, 12.97], [77.60, 12.98]],
                },
                "properties": {"length_m": 100.0, "travel_time_s": 10.0, "nodes": [0, 1]},
            }
        ]
        with tempfile.NamedTemporaryFile(suffix=".geojson", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        try:
            export_route_geojson(routes, tmp_path)
            assert tmp_path.exists()
            with open(tmp_path) as f:
                data = json.load(f)
            assert data["type"] == "FeatureCollection"
            assert len(data["features"]) == 1
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_export_empty_routes(self):
        with tempfile.NamedTemporaryFile(suffix=".geojson", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        try:
            export_route_geojson([], tmp_path)
            assert tmp_path.exists()
        finally:
            tmp_path.unlink(missing_ok=True)
