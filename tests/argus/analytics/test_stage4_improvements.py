"""Unit tests for Stage 4 improvements."""

import pytest
import networkx as nx
import numpy as np
from pathlib import Path

from argus.core.types import RoadGraph
from argus.analytics.analyzer import CriticalityAnalyzerImpl, AnalyticsConfig
from argus.analytics.report import generate_report


def test_criticality_report_includes_coordinates(tmp_path):
    """Verify that articulation points and bridges include lat/lon coordinates in the report."""
    g = nx.MultiDiGraph()
    # Node 1 is an articulation point connecting component {0} to component {2}
    g.add_node(0, x=0.0, y=0.0, lat=12.0, lon=77.0)
    g.add_node(1, x=10.0, y=0.0, lat=12.1, lon=77.1)
    g.add_node(2, x=20.0, y=0.0, lat=12.2, lon=77.2)
    
    g.add_edge(0, 1, key=0, length_px=10.0)
    g.add_edge(1, 2, key=0, length_px=10.0)

    road_graph = RoadGraph(graph=g, crs="EPSG:4326", bounds=(77.0, 12.0, 77.2, 12.2))
    
    analyzer = CriticalityAnalyzerImpl()
    result = analyzer.analyze(road_graph)

    # Verify report contains the new coordinate-annotated keys
    report = result.report
    assert "articulation_points_with_coordinates" in report
    assert "bridges_with_coordinates" in report

    # Verify articulation point details
    aps = report["articulation_points_with_coordinates"]
    assert len(aps) == 1
    assert aps[0]["id"] == 1
    assert aps[0]["lat"] == 12.1
    assert aps[0]["lon"] == 77.1

    # Verify bridge details
    bridges = report["bridges_with_coordinates"]
    assert len(bridges) == 2
    # Verify first bridge (0, 1) or (1, 2)
    b0 = bridges[0]
    assert {b0["u"], b0["v"]} in [{0, 1}, {1, 2}]
    assert "u_lat" in b0
    assert "u_lon" in b0
    assert "v_lat" in b0
    assert "v_lon" in b0


def test_report_writes_csv_files(tmp_path):
    """Verify that generate_report writes list-of-dict data formats to CSV."""
    g = nx.MultiDiGraph()
    g.add_node(0, x=0.0, y=0.0, lat=12.0, lon=77.0)
    g.add_node(1, x=10.0, y=0.0, lat=12.1, lon=77.1)
    g.add_edge(0, 1, key=0, length_px=10.0)

    road_graph = RoadGraph(graph=g, crs="EPSG:4326", bounds=(77.0, 12.0, 77.1, 12.1))
    
    analyzer = CriticalityAnalyzerImpl()
    result = analyzer.analyze(road_graph)

    output = generate_report(result, tmp_path, format="both")

    # CSV files should be written under the output directory
    csv_dir = output["csv"]
    assert Path(csv_dir).exists()
    
    ap_csv = csv_dir / "articulation_points_with_coordinates.csv"
    bridges_csv = csv_dir / "bridges_with_coordinates.csv"

    # In a 2-node connected line, 0-1 is a bridge, but there are no articulation points
    assert bridges_csv.exists()
    
    # Read the bridges CSV content to verify columns
    with open(bridges_csv, "r") as f:
        header = f.readline().strip()
    assert "u,v,u_lat,u_lon,v_lat,v_lon" in header


def test_betweenness_large_graph_optimization(monkeypatch):
    """Verify that betweenness calculation defaults to k=100 on large graphs (>500 nodes)."""
    g = nx.MultiDiGraph()
    # Build a star graph of 505 nodes
    g.add_node(0, x=0.0, y=0.0, lat=12.0, lon=77.0)
    for i in range(1, 505):
        g.add_node(i, x=1.0, y=1.0, lat=12.0, lon=77.0)
        g.add_edge(0, i, key=0, length_px=1.0)
        
    road_graph = RoadGraph(graph=g, crs="EPSG:4326", bounds=(77.0, 12.0, 77.0, 12.0))
    
    analyzer = CriticalityAnalyzerImpl()
    
    # We will patch nx.betweenness_centrality to capture the k argument
    captured_k = []
    original_bc = nx.betweenness_centrality
    
    def mock_bc(G, normalized=True, weight=None, endpoints=False, seed=None, k=None):
        captured_k.append(k)
        return original_bc(G, normalized=normalized, weight=weight, endpoints=endpoints, seed=seed, k=k)
        
    monkeypatch.setattr(nx, "betweenness_centrality", mock_bc)
    
    result = analyzer.analyze(road_graph)
    
    # k should be set to 100 because G has 505 nodes and no k was explicitly provided
    assert len(captured_k) > 0
    assert captured_k[0] == 100
