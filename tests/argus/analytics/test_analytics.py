"""Tests for M4 Criticality Analytics."""

import json
import os

import networkx as nx
import pytest
from argus.analytics.analyzer import (
    AnalyticsConfig,
    CriticalityAnalyzerImpl,
    load_analytics_config_from_yaml,
)
from argus.analytics.report import generate_report
from argus.core.errors import EmptyGraphError
from argus.core.types import RoadGraph

# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


def _make_chain_graph(n: int = 5) -> RoadGraph:
    g = nx.MultiDiGraph()
    for i in range(n):
        g.add_node(i, x=float(i), y=0.0, lat=12.97 + i * 0.01, lon=77.59)
        g.add_node(i, x=float(i), y=0.0, lat=12.97 + i * 0.01, lon=77.59 + i * 0.01)
    for i in range(n - 1):
        g.add_edge(i, i + 1, length_px=100.0)
    return RoadGraph(
        graph=g, crs="EPSG:4326", bounds=(77.59, 12.97, 77.59 + n * 0.01, 12.97 + n * 0.01)
    )


def _make_star_graph() -> RoadGraph:
    """Hub-and-spoke: node 0 connects to nodes 1..4."""
    g = nx.MultiDiGraph()
    g.add_node(0, x=0.0, y=0.0, lat=12.97, lon=77.59)
    for i in range(1, 5):
        g.add_node(i, x=float(i), y=0.0, lat=12.97 + i * 0.01, lon=77.59 + i * 0.01)
        g.add_edge(i, 0, length_px=100.0)
    return RoadGraph(graph=g, crs="EPSG:4326", bounds=(77.59, 12.97, 77.63, 13.01))


# ------------------------------------------------------------------
# Analyzer
# ------------------------------------------------------------------


class TestAnalyzer:
    def test_default_config(self):
        cfg = AnalyticsConfig()
        assert "betweenness" in cfg.metrics
        assert len(cfg.metrics) == 5

    def test_metric_subset(self):
        cfg = AnalyticsConfig(metrics=["articulation", "bridges"])
        analyzer = CriticalityAnalyzerImpl(cfg)
        rg = _make_chain_graph(4)
        result = analyzer.analyze(rg)
        assert "top_nodes_betweenness" not in result.report
        assert "articulation_points" in result.report
        assert "bridges" in result.report

    def test_chain_betweenness(self):
        """Chain: middle nodes > end nodes."""
        cfg = AnalyticsConfig(metrics=["betweenness"])
        analyzer = CriticalityAnalyzerImpl(cfg)
        result = analyzer.analyze(_make_chain_graph(5))
        bc = dict(result.report["top_nodes_betweenness"])
        # Node 2 (middle) should outrank node 0 (end)
        assert bc[2] > bc[0] or bc.get(1, 0) > bc.get(0, 0)

    def test_chain_articulation_points(self):
        """Chain: internal nodes are articulation."""
        cfg = AnalyticsConfig(metrics=["articulation"])
        analyzer = CriticalityAnalyzerImpl(cfg)
        result = analyzer.analyze(_make_chain_graph(4))
        aps = result.report["articulation_points"]
        assert 1 in aps
        assert 2 in aps

    def test_chain_bridges(self):
        """Chain: all edges are bridges."""
        cfg = AnalyticsConfig(metrics=["bridges"])
        analyzer = CriticalityAnalyzerImpl(cfg)
        result = analyzer.analyze(_make_chain_graph(4))
        assert len(result.report["bridges"]) == 3

    def test_star_hub_betweenness(self):
        """Hub node should have highest betweenness."""
        cfg = AnalyticsConfig(metrics=["betweenness"])
        analyzer = CriticalityAnalyzerImpl(cfg)
        result = analyzer.analyze(_make_star_graph())
        bc = dict(result.report["top_nodes_betweenness"])
        assert max(bc.keys(), key=lambda k: bc[k]) == 0

    def test_star_no_articulation(self):
        """Star graph: hub is NOT an articulation point in the undirected sense
        when there are multiple paths through spokes — actually hub IS articulation
        because removing it disconnects all leaves."""
        cfg = AnalyticsConfig(metrics=["articulation"])
        analyzer = CriticalityAnalyzerImpl(cfg)
        result = analyzer.analyze(_make_star_graph())
        aps = result.report["articulation_points"]
        assert 0 in aps

    def test_weighted_betweenness(self):
        cfg = AnalyticsConfig(metrics=["betweenness"], betweenness_weighted=True)
        analyzer = CriticalityAnalyzerImpl(cfg)
        result = analyzer.analyze(_make_chain_graph(5))
        assert "top_nodes_betweenness" in result.report

    def test_empty_graph_raises(self):
        rg = RoadGraph(graph=nx.MultiDiGraph(), crs="EPSG:4326", bounds=(0, 0, 1, 1))
        analyzer = CriticalityAnalyzerImpl(AnalyticsConfig())
        with pytest.raises(EmptyGraphError):
            analyzer.analyze(rg)

    def test_resilience_summary(self):
        cfg = AnalyticsConfig()
        analyzer = CriticalityAnalyzerImpl(cfg)
        result = analyzer.analyze(_make_chain_graph(5))
        resilience = result.summary["resilience"]
        assert "articulation_points_count" in resilience
        assert "bridges_count" in resilience
        assert "vulnerability_ratio" in resilience
        assert resilience["vulnerability_ratio"] > 0

    def test_avg_path_length(self):
        cfg = AnalyticsConfig()
        analyzer = CriticalityAnalyzerImpl(cfg)
        result = analyzer.analyze(_make_chain_graph(5))
        apl = result.summary["resilience"].get("avg_path_length")
        assert apl is not None
        assert apl > 0

    def test_config_from_yaml(self):
        cfg = load_analytics_config_from_yaml()
        assert isinstance(cfg, AnalyticsConfig)
        assert len(cfg.metrics) >= 3

    def test_annotated_graph_has_metrics(self):
        cfg = AnalyticsConfig(metrics=["betweenness", "articulation"])
        analyzer = CriticalityAnalyzerImpl(cfg)
        result = analyzer.analyze(_make_chain_graph(5))
        annotated = result.annotated_graph.graph
        for _, data in annotated.nodes(data=True):
            assert isinstance(data.get("betweenness", 0), float)
            assert isinstance(data.get("is_articulation", -1), int)

    def test_bridges_annotation(self):
        cfg = AnalyticsConfig(metrics=["bridges"])
        analyzer = CriticalityAnalyzerImpl(cfg)
        result = analyzer.analyze(_make_chain_graph(4))
        annotated = result.annotated_graph.graph
        bridge_count = 0
        for _u, _v, _k, data in annotated.edges(data=True, keys=True):
            if data.get("is_bridge", 0) == 1:
                bridge_count += 1
        assert bridge_count > 0


# ------------------------------------------------------------------
# Report
# ------------------------------------------------------------------


class TestReport:
    def test_generate_json_report(self, tmp_path):
        cfg = AnalyticsConfig()
        analyzer = CriticalityAnalyzerImpl(cfg)
        result = analyzer.analyze(_make_chain_graph(5))
        paths = generate_report(result, tmp_path, format="json")
        json_path = tmp_path / "criticality_report.json"
        assert json_path.exists()
        assert paths.get("json") == json_path

        with open(json_path) as f:
            data = json.load(f)
        assert "report" in data
        assert "summary" in data

    def test_generate_csv_report(self, tmp_path):
        cfg = AnalyticsConfig()
        analyzer = CriticalityAnalyzerImpl(cfg)
        result = analyzer.analyze(_make_chain_graph(5))
        _ = generate_report(result, tmp_path, format="csv")

        csv_files = [f for f in os.listdir(tmp_path) if f.endswith(".csv")]
        assert len(csv_files) > 0

    def test_generate_both(self, tmp_path):
        cfg = AnalyticsConfig()
        analyzer = CriticalityAnalyzerImpl(cfg)
        result = analyzer.analyze(_make_chain_graph(5))
        output = generate_report(result, tmp_path, format="both")
        assert "json" in output
        assert "csv" in output
