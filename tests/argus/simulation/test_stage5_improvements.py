"""Unit tests for Stage 5 improvements."""

import networkx as nx
from argus.core.types import RoadGraph
from argus.simulation.simulator import DisasterSimulatorImpl, ScenarioConfig
from shapely.geometry import Polygon, mapping


def test_midsegment_flooding_removes_edge():
    """Verify that an edge is removed if its midpoint intersects the flood polygon,

    even if both endpoint nodes are outside the polygon.
    """
    g = nx.MultiDiGraph()
    # Horizontal line from (0, 0) to (100, 0)
    g.add_node(0, x=0.0, y=0.0, lat=12.0, lon=77.0)
    g.add_node(1, x=100.0, y=0.0, lat=12.0, lon=77.1)

    # Path pixels pass through (50, 0)
    g.add_edge(0, 1, key=0, path_pixels=[(0.0, 0.0), (50.0, 0.0), (100.0, 0.0)], length=100.0)

    road_graph = RoadGraph(graph=g, crs="EPSG:4326", bounds=(77.0, 12.0, 77.1, 12.0))

    # Flood polygon covering longitude 77.04 to 77.06 (the middle of the road segment)
    # The endpoints 77.0 and 77.1 are outside this polygon!
    poly = Polygon([(77.04, 11.9), (77.06, 11.9), (77.06, 12.1), (77.04, 12.1), (77.04, 11.9)])

    scenario = ScenarioConfig(
        scenario_id="midsegment_flood",
        scenario_type="flood",
        affected_region=mapping(poly),
        severity=1.0,
    )

    # We use a dummy transform that maps (px_x, px_y) directly to (lon, lat)
    # Forward: lon = 0.001 * x + 77.0, lat = 0.0 * y + 12.0
    # Let's check: x=0 -> lon=77.0, x=50 -> lon=77.05, x=100 -> lon=77.1
    # This transform aligns perfectly with the coordinates!
    road_graph.metadata["transform"] = [0.001, 0.0, 77.0, 0.0, 0.001, 12.0]

    simulator = DisasterSimulatorImpl()
    result = simulator.simulate(road_graph, scenario)

    # Both nodes should remain in the graph since they are outside the flood polygon
    assert 0 in result.modified_graph.graph
    assert 1 in result.modified_graph.graph

    # The edge 0 -> 1 should be removed because its midpoint (77.05, 12.0) is flooded!
    assert not result.modified_graph.graph.has_edge(0, 1)
    assert len(result.impact_report["removed_edges"]) == 1


def test_midsegment_blockage_reweights_edge():
    """Verify that an edge is reweighted if its midpoint intersects the blockage polygon."""
    g = nx.MultiDiGraph()
    g.add_node(0, x=0.0, y=0.0, lat=12.0, lon=77.0)
    g.add_node(1, x=100.0, y=0.0, lat=12.0, lon=77.1)
    g.add_edge(0, 1, key=0, path_pixels=[(0.0, 0.0), (50.0, 0.0), (100.0, 0.0)], length=100.0)

    road_graph = RoadGraph(graph=g, crs="EPSG:4326", bounds=(77.0, 12.0, 77.1, 12.0))

    poly = Polygon([(77.04, 11.9), (77.06, 11.9), (77.06, 12.1), (77.04, 12.1), (77.04, 11.9)])

    scenario = ScenarioConfig(
        scenario_id="midsegment_blockage",
        scenario_type="road_blockage",
        affected_region=mapping(poly),
        severity=0.5,
    )

    road_graph.metadata["transform"] = [0.001, 0.0, 77.0, 0.0, 0.001, 12.0]

    simulator = DisasterSimulatorImpl()
    result = simulator.simulate(road_graph, scenario)

    # Edge should still exist but have its weight multiplied by severity * blockage_multiplier
    assert result.modified_graph.graph.has_edge(0, 1)

    edata = result.modified_graph.graph.get_edge_data(0, 1, 0)
    # Default blockage multiplier is 1000, severity is 0.5 -> multiplier is 500
    # Original length was 100.0 -> new length should be 50000.0
    assert edata["length"] == 50000.0
    assert edata.get("blocked") is True
