"""Integration tests for M6 Routing Engine CLI."""

import json
import pickle
import subprocess
import sys
from pathlib import Path

import networkx as nx
import pytest

from argus.core.types import RoadGraph
from argus.graph.export import export_pickle


def _make_test_graph(path: Path) -> Path:
    """Create a geographically-coordinated test graph pickle."""
    g = nx.MultiDiGraph()
    lat0, lon0 = 12.970, 77.590
    step = 0.005
    for i in range(9):
        x, y = i % 3, i // 3
        g.add_node(i, lat=lat0 + y * step, lon=lon0 + x * step)
    for i in range(9):
        if i % 3 < 2:
            g.add_edge(i, i + 1, length=100.0)
        if i // 3 < 2:
            g.add_edge(i, i + 3, length=100.0)
    rg = RoadGraph(
        graph=g,
        crs="EPSG:4326",
        bounds=(lon0, lat0, lon0 + 2 * step, lat0 + 2 * step),
    )
    export_pickle(rg, path)
    return path


class TestCLIRoute:
    """Integration tests for `argus route` CLI command."""

    @pytest.fixture
    def graph_pickle(self, tmp_path):
        p = tmp_path / "test_graph.pkl"
        _make_test_graph(p)
        return p

    def test_route_dijkstra(self, graph_pickle, tmp_path):
        """Test basic routing via CLI."""
        out = tmp_path / "route.geojson"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "argus.cli.main",
                "route",
                str(graph_pickle),
                "--origin",
                "12.970,77.590",
                "--destination",
                "12.980,77.600",
                "--algorithm",
                "dijkstra",
                "-o",
                str(out),
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        assert out.exists()
        data = json.loads(out.read_text())
        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) >= 1
        feat = data["features"][0]
        assert feat["geometry"]["type"] == "LineString"
        assert len(feat["geometry"]["coordinates"]) >= 2
        assert feat["properties"]["length_m"] > 0

    def test_route_astar(self, graph_pickle, tmp_path):
        """Test A* routing via CLI."""
        out = tmp_path / "route_astar.geojson"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "argus.cli.main",
                "route",
                str(graph_pickle),
                "--origin",
                "12.970,77.590",
                "--destination",
                "12.980,77.600",
                "--algorithm",
                "astar",
                "-o",
                str(out),
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        assert out.exists()

    def test_route_k_shortest(self, graph_pickle, tmp_path):
        """Test k_shortest routing via CLI."""
        out = tmp_path / "route_k.geojson"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "argus.cli.main",
                "route",
                str(graph_pickle),
                "--origin",
                "12.970,77.590",
                "--destination",
                "12.980,77.600",
                "--algorithm",
                "k_shortest",
                "--k",
                "3",
                "-o",
                str(out),
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        assert out.exists()


class TestCLIRouteComparison:
    """Integration tests for `argus route --compare-graph` CLI command."""

    @pytest.fixture
    def graph_pickle(self, tmp_path):
        p = tmp_path / "test_graph.pkl"
        _make_test_graph(p)
        return p

    def test_route_with_compare_graph(self, graph_pickle, tmp_path):
        """Test route comparison via CLI."""
        with open(graph_pickle, "rb") as f:
            rg = pickle.load(f)
        modified_g = rg.graph.copy()
        edges = list(modified_g.edges(keys=True))
        if edges:
            u, v, k = edges[0]
            modified_g.remove_edge(u, v, k)
        mod_pickle = tmp_path / "modified_graph.pkl"
        mod_rg = RoadGraph(graph=modified_g, crs=rg.crs, bounds=rg.bounds)
        export_pickle(mod_rg, mod_pickle)

        out = tmp_path / "route_cmp.geojson"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "argus.cli.main",
                "route",
                str(graph_pickle),
                "--origin",
                "12.970,77.590",
                "--destination",
                "12.980,77.600",
                "--algorithm",
                "dijkstra",
                "--compare-graph",
                str(mod_pickle),
                "-o",
                str(out),
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        assert out.exists()


class TestRouterCompareRoutes:
    """Integration tests for router compare_routes method."""

    def test_compare_routes_after_simulation(self, tmp_path):
        """End-to-end: simulate then route, verify comparison."""
        from argus.routing import RouteQuery, RouterImpl
        from argus.simulation import DisasterSimulatorImpl, load_scenario

        g = nx.MultiDiGraph()
        lat0, lon0 = 12.97, 77.59
        step = 0.005
        for i in range(9):
            x, y = i % 3, i // 3
            g.add_node(i, lat=lat0 + y * step, lon=lon0 + x * step)
        for i in range(9):
            if i % 3 < 2:
                g.add_edge(i, i + 1, length=100.0)
            if i // 3 < 2:
                g.add_edge(i, i + 3, length=100.0)
        rg = RoadGraph(
            graph=g,
            crs="EPSG:4326",
            bounds=(lon0, lat0, lon0 + 2 * step, lat0 + 2 * step),
        )

        scen_path = Path("configs/scenarios/flood_zone_a.yaml")
        if not scen_path.exists():
            pytest.skip("flood_zone_a.yaml scenario not available")

        scen = load_scenario(str(scen_path))
        sim = DisasterSimulatorImpl()
        sim_result = sim.simulate(rg, scen)

        router = RouterImpl()
        q = RouteQuery(
            origin=(lat0, lon0),
            destination=(lat0 + 2 * step, lon0 + 2 * step),
        )
        base_result = router.find_route(rg, q)
        mod_result = router.find_route(sim_result.modified_graph, q)

        cmp = router.compare_routes(base_result.routes, mod_result.routes)
        assert cmp is not None
        assert "status" in cmp
        assert cmp["status"] in ("unchanged", "detour", "unreachable")


class TestRoutingPipeline:
    """End-to-end: analyze graph, simulate, route, and verify."""

    def test_route_after_analyze_and_simulate(self):
        """Test that routing works after criticality analysis and simulation."""
        from argus.analytics import CriticalityAnalyzerImpl
        from argus.routing import RouteQuery, RouterImpl
        from argus.simulation import DisasterSimulatorImpl, load_scenario

        g = nx.MultiDiGraph()
        lat0, lon0 = 12.97, 77.59
        step = 0.005
        for i in range(25):
            x, y = i % 5, i // 5
            g.add_node(i, lat=lat0 + y * step, lon=lon0 + x * step)
        for i in range(25):
            if i % 5 < 4:
                g.add_edge(i, i + 1, length=100.0)
            if i // 5 < 4:
                g.add_edge(i, i + 5, length=100.0)
        rg = RoadGraph(
            graph=g,
            crs="EPSG:4326",
            bounds=(lon0, lat0, lon0 + 4 * step, lat0 + 4 * step),
        )

        analyzer = CriticalityAnalyzerImpl()
        criticality = analyzer.analyze(rg)
        assert criticality is not None

        scen_path = Path("configs/scenarios/flood_zone_a.yaml")
        if not scen_path.exists():
            pytest.skip("flood_zone_a.yaml scenario not available")
        scen = load_scenario(str(scen_path))
        sim = DisasterSimulatorImpl()
        sim_result = sim.simulate(rg, scen)

        router = RouterImpl()
        q = RouteQuery(
            origin=(lat0, lon0),
            destination=(lat0 + 4 * step, lon0 + 4 * step),
        )
        base = router.find_route(rg, q)
        mod = router.find_route(sim_result.modified_graph, q)

        assert base is not None
        assert mod is not None

        cmp = router.compare_routes(base.routes, mod.routes)
        assert cmp is not None
        assert cmp["status"] in ("unchanged", "detour", "unreachable")
