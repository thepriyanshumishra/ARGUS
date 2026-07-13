"""Unit tests for Stage 6 improvements."""

import pytest
import networkx as nx

from argus.core.types import RoadGraph, RouteResult
from argus.routing.router import RouterImpl, RouteQuery


def test_astar_admissible_heuristic():
    """Verify that self-calibrating A* heuristic finds the correct shortest path."""
    g = nx.MultiDiGraph()
    # Coordinates in lat/lon space (very small distances)
    # Target path: 0 -> 1 -> 2
    # Alternate path: 0 -> 2 (but it's longer in weight space)
    g.add_node(0, x=0.0, y=0.0, lat=12.000, lon=77.000)
    g.add_node(1, x=50.0, y=0.0, lat=12.001, lon=77.001)
    g.add_node(2, x=100.0, y=0.0, lat=12.002, lon=77.002)

    g.add_edge(0, 1, key=0, length_px=10.0)
    g.add_edge(1, 2, key=0, length_px=10.0)
    g.add_edge(0, 2, key=0, length_px=50.0)

    road_graph = RoadGraph(graph=g, crs="EPSG:4326", bounds=(77.0, 12.0, 77.002, 12.002))
    router = RouterImpl()
    
    # A* search should correctly find the path [0, 1, 2] instead of [0, 2] because heuristic is scaled
    res = router.find_route(road_graph, RouteQuery(origin=(12.0, 77.0), destination=(12.002, 77.002), algorithm="astar"))
    assert len(res.routes) == 1
    assert res.routes[0]["properties"]["nodes"] == [0, 1, 2]
    assert res.routes[0]["properties"]["length_m"] == 20.0


def test_compare_routes_tolerance():
    """Verify that compare_routes uses a float tolerance to check status."""
    router = RouterImpl()

    base_route = [{
        "type": "Feature",
        "geometry": {"type": "LineString", "coordinates": [[77.0, 12.0], [77.1, 12.1]]},
        "properties": {
            "length_m": 100.00,
            "travel_time_s": 10.0,
            "speed_kmh": 40.0,
            "nodes": [0, 1]
        }
    }]

    # Case 1: Change is very small (0.05m) -> should be "unchanged"
    mod_route_small_diff = [{
        "type": "Feature",
        "geometry": {"type": "LineString", "coordinates": [[77.0, 12.0], [77.1, 12.1]]},
        "properties": {
            "length_m": 100.05,
            "travel_time_s": 10.005,
            "speed_kmh": 40.0,
            "nodes": [0, 1]
        }
    }]

    comparison = router.compare_routes(base_route, mod_route_small_diff)
    assert comparison["status"] == "unchanged"
    assert comparison["delta_length_m"] == pytest.approx(0.05)

    # Case 2: Change is larger (0.2m) -> should be "detour"
    mod_route_large_diff = [{
        "type": "Feature",
        "geometry": {"type": "LineString", "coordinates": [[77.0, 12.0], [77.1, 12.1]]},
        "properties": {
            "length_m": 100.20,
            "travel_time_s": 10.02,
            "speed_kmh": 40.0,
            "nodes": [0, 2, 1]
        }
    }]

    comparison = router.compare_routes(base_route, mod_route_large_diff)
    assert comparison["status"] == "detour"
    assert comparison["delta_length_m"] == pytest.approx(0.20)
