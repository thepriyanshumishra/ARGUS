"""Tests for M5 Simulation Engine."""

import networkx as nx
import pytest
from argus.core.errors import InvalidScenarioError
from argus.core.types import RoadGraph
from argus.simulation.simulator import DisasterSimulatorImpl, ScenarioConfig, load_scenario
from shapely.geometry import Polygon


def _make_grid_graph(n_rows: int = 3, n_cols: int = 3) -> nx.MultiDiGraph:
    """Build a grid graph with lat/lon coordinates."""
    g = nx.MultiDiGraph()
    for i in range(n_rows * n_cols):
        x, y = i % n_cols, i // n_cols
        g.add_node(i, lat=12.97 + y * 0.01, lon=77.59 + x * 0.01)
    for i in range(n_rows * n_cols):
        if i % n_cols < n_cols - 1:
            g.add_edge(i, i + 1, length=100.0)
        if i // n_cols < n_rows - 1:
            g.add_edge(i, i + n_cols, length=100.0)
    return g


def _make_grid_road_graph(n_rows: int = 3, n_cols: int = 3) -> RoadGraph:
    g = _make_grid_graph(n_rows, n_cols)
    return RoadGraph(graph=g, crs="EPSG:4326", bounds=(77.59, 12.97, 77.62, 13.00))


def _region_covering_grid() -> dict:
    return Polygon(
        [(77.59, 12.97), (77.61, 12.97), (77.61, 12.99), (77.59, 12.99)]
    ).__geo_interface__


class TestScenarioConfig:
    """Validation tests for ScenarioConfig."""

    def test_valid_construction(self):
        cfg = ScenarioConfig(
            scenario_id="f1",
            scenario_type="flood",
            affected_region=_region_covering_grid(),
            severity=0.5,
        )
        assert cfg.scenario_id == "f1"
        assert cfg.severity == 0.5

    def test_invalid_type_raises(self):
        with pytest.raises(InvalidScenarioError, match="Unknown scenario_type"):
            ScenarioConfig(
                scenario_id="x",
                scenario_type="earthquake",
                affected_region=_region_covering_grid(),
            )

    def test_invalid_region_type_raises(self):
        with pytest.raises(InvalidScenarioError, match="Polygon or MultiPolygon"):
            ScenarioConfig(
                scenario_id="x",
                scenario_type="flood",
                affected_region={"type": "Point", "coordinates": [0, 0]},
            )

    def test_missing_coordinates_raises(self):
        with pytest.raises(InvalidScenarioError, match="coordinates"):
            ScenarioConfig(
                scenario_id="x",
                scenario_type="flood",
                affected_region={"type": "Polygon"},
            )

    def test_invalid_severity_raises(self):
        with pytest.raises(InvalidScenarioError, match="severity must be 0–1"):
            ScenarioConfig(
                scenario_id="x",
                scenario_type="flood",
                affected_region=_region_covering_grid(),
                severity=2.0,
            )

    def test_empty_id_raises(self):
        with pytest.raises(InvalidScenarioError, match="scenario_id must not be empty"):
            ScenarioConfig(
                scenario_id="",
                scenario_type="flood",
                affected_region=_region_covering_grid(),
            )

    def test_from_yaml_valid(self, tmp_path):
        yaml_path = tmp_path / "scenario.yaml"
        yaml_path.write_text(
            "scenario_id: test\n"
            "scenario_type: flood\n"
            "affected_region:\n"
            "  type: Polygon\n"
            "  coordinates: [[[0, 0], [1, 0], [1, 1], [0, 0]]]\n"
            "severity: 0.8\n"
        )
        cfg = ScenarioConfig.from_yaml(yaml_path)
        assert cfg.scenario_id == "test"
        assert cfg.severity == 0.8

    def test_from_yaml_missing_fields(self, tmp_path):
        yaml_path = tmp_path / "bad.yaml"
        yaml_path.write_text("scenario_id: test\nseverity: 0.5\n")
        with pytest.raises(InvalidScenarioError, match="Missing required fields"):
            ScenarioConfig.from_yaml(yaml_path)


class TestSimulation:
    """Disaster simulation behavioural tests."""

    def test_simulator_creation(self):
        sim = DisasterSimulatorImpl()
        assert sim is not None

    def test_simulator_with_config(self):
        sim = DisasterSimulatorImpl({"road_blockage": {"weight_multiplier": 500}})
        assert sim._blockage_multiplier == 500

    def test_flood_removes_nodes(self):
        rg = _make_grid_road_graph()
        scenario = ScenarioConfig(
            scenario_id="test_flood",
            scenario_type="flood",
            affected_region=_region_covering_grid(),
            severity=1.0,
        )
        sim = DisasterSimulatorImpl()
        result = sim.simulate(rg, scenario)

        assert result.modified_graph.node_count <= rg.node_count
        assert result.scenario_metadata["type"] == "flood"

    def test_flood_impact_report(self):
        rg = _make_grid_road_graph()
        scenario = ScenarioConfig(
            scenario_id="test_flood",
            scenario_type="flood",
            affected_region=_region_covering_grid(),
            severity=1.0,
        )
        sim = DisasterSimulatorImpl()
        result = sim.simulate(rg, scenario)

        impact = result.impact_report
        assert "removed_nodes" in impact
        assert "removed_edges" in impact
        assert "disconnected_components" in impact
        assert "original_nodes" in impact
        assert "modified_nodes" in impact
        assert impact["original_nodes"] > 0

    def test_bridge_collapse_removes_edges(self):
        g = nx.MultiDiGraph()
        for i in range(4):
            g.add_node(i, lat=12.97 + i * 0.01, lon=77.59)
        g.add_edge(0, 1, length=100.0, is_bridge=False)
        g.add_edge(1, 2, length=100.0, is_bridge=True)
        g.add_edge(2, 3, length=100.0, is_bridge=False)
        rg = RoadGraph(graph=g, crs="EPSG:4326", bounds=(77.59, 12.97, 77.60, 13.01))

        scenario = ScenarioConfig(
            scenario_id="test_bridge",
            scenario_type="bridge_collapse",
            affected_region=Polygon(
                [(77.58, 12.96), (77.61, 12.96), (77.61, 13.01), (77.58, 13.01)]
            ).__geo_interface__,
            severity=1.0,
        )
        sim = DisasterSimulatorImpl()
        result = sim.simulate(rg, scenario)

        assert result.modified_graph.edge_count < rg.edge_count
        removed = result.impact_report["removed_edges"]
        assert len(removed) >= 1
        assert removed[0]["reason"] == "bridge_collapse"

    def test_road_blockage_reweights(self):
        g = nx.MultiDiGraph()
        for i in range(4):
            g.add_node(i, lat=12.97 + i * 0.01, lon=77.59)
        g.add_edge(0, 1, length=100.0)
        g.add_edge(1, 2, length=100.0)
        g.add_edge(2, 3, length=100.0)
        rg = RoadGraph(graph=g, crs="EPSG:4326", bounds=(77.59, 12.97, 77.60, 13.01))

        scenario = ScenarioConfig(
            scenario_id="test_blockage",
            scenario_type="road_blockage",
            affected_region=Polygon(
                [(77.58, 12.96), (77.61, 12.96), (77.61, 13.01), (77.58, 13.01)]
            ).__geo_interface__,
            severity=1.0,
        )
        sim = DisasterSimulatorImpl()
        result = sim.simulate(rg, scenario)

        reweighted = result.impact_report["reweighted_edges"]
        assert len(reweighted) >= 1
        assert reweighted[0]["new_length"] > reweighted[0]["old_length"]

    def test_severity_scales_blockage_weight(self):
        g = nx.MultiDiGraph()
        g.add_node(0, lat=12.97, lon=77.59)
        g.add_node(1, lat=12.98, lon=77.59)
        g.add_edge(0, 1, length=100.0)
        rg = RoadGraph(graph=g, crs="EPSG:4326", bounds=(77.59, 12.97, 77.60, 12.98))

        region = Polygon(
            [(77.58, 12.96), (77.60, 12.96), (77.60, 12.99), (77.58, 12.99)]
        ).__geo_interface__

        scenario_full = ScenarioConfig(
            scenario_id="s",
            scenario_type="road_blockage",
            affected_region=region,
            severity=1.0,
        )
        scenario_half = ScenarioConfig(
            scenario_id="s",
            scenario_type="road_blockage",
            affected_region=region,
            severity=0.5,
        )

        sim = DisasterSimulatorImpl()
        r_full = sim.simulate(rg, scenario_full)
        rg2 = RoadGraph(graph=g.copy(), crs="EPSG:4326", bounds=(77.59, 12.97, 77.60, 12.98))
        r_half = sim.simulate(rg2, scenario_half)

        full_len = r_full.impact_report["reweighted_edges"][0]["new_length"]
        half_len = r_half.impact_report["reweighted_edges"][0]["new_length"]
        assert half_len < full_len

    def test_scenario_outside_graph_no_effect(self):
        """Scenario region outside graph bounds removes nothing."""
        rg = _make_grid_road_graph()
        far_region = Polygon(
            [(80.0, 20.0), (81.0, 20.0), (81.0, 21.0), (80.0, 21.0)]
        ).__geo_interface__

        scenario = ScenarioConfig(
            scenario_id="noop",
            scenario_type="flood",
            affected_region=far_region,
            severity=1.0,
        )
        sim = DisasterSimulatorImpl()
        result = sim.simulate(rg, scenario)

        assert result.modified_graph.node_count == rg.node_count
        assert result.modified_graph.edge_count == rg.edge_count

    def test_load_scenario(self, tmp_path):
        yaml_path = tmp_path / "s.yaml"
        yaml_path.write_text(
            "scenario_id: x\n"
            "scenario_type: flood\n"
            "affected_region:\n"
            "  type: Polygon\n"
            "  coordinates: [[[0,0],[1,0],[1,1],[0,0]]]\n"
        )
        cfg = load_scenario(yaml_path)
        assert cfg.scenario_id == "x"
