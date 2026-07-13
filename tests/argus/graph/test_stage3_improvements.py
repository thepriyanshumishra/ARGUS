"""Unit tests for Stage 3 improvements."""

import pytest
import networkx as nx
import numpy as np

from argus.graph.cleaning import merge_close_nodes, snap_endpoints


def test_merge_close_nodes_snaps_geometry():
    """Verify that merging nodes adjusts edge path_pixels endpoints."""
    g = nx.MultiDiGraph()
    # Node 0 (survivor) and Node 1 (victim, to be merged) are at distance 2.0 (under threshold 5.0)
    g.add_node(0, x=0.0, y=0.0, lat=12.0, lon=77.0)
    g.add_node(1, x=2.0, y=0.0, lat=12.0, lon=77.0)
    
    # Node 2 and Node 3 to create edges
    g.add_node(2, x=10.0, y=0.0, lat=12.0, lon=77.0)
    g.add_node(3, x=-10.0, y=0.0, lat=12.0, lon=77.0)
    
    # Connect Node 0 with 2 edges (degree 2)
    g.add_edge(2, 0, key=0)
    g.add_edge(0, 3, key=0)
    
    # Connect Node 1 with 1 edge (degree 1)
    # The edge from 2 to 1 ends at (2.0, 0.0) which is Node 1's position
    path_pixels = [(10.0, 0.0), (5.0, 0.0), (2.0, 0.0)]
    g.add_edge(2, 1, key=1, path_pixels=path_pixels, length_px=8.0)

    # Perform merge
    merged = merge_close_nodes(g, merge_distance=5.0)

    # Node 1 should be gone, merged into Node 0
    assert 1 not in merged
    assert 0 in merged
    assert merged.has_edge(2, 0)

    # The edge 2 -> 0's path_pixels should now end at Node 0's position (0.0, 0.0)
    # Since we added key=1 for the edge 2 -> 1, after merging it will be added to 2 -> 0
    edata = merged.get_edge_data(2, 0, 1)
    assert edata is not None
    assert edata["path_pixels"][-1] == (0.0, 0.0)


def test_snap_endpoints_splits_nearby_edges():
    """Verify that snapping endpoints close to edges splits the target edge."""
    g = nx.MultiDiGraph()
    
    # Create a long edge (horizontal highway from 0 to 1)
    g.add_node(0, x=0.0, y=0.0, lat=12.0, lon=77.0, degree=2)
    g.add_node(1, x=100.0, y=0.0, lat=12.0, lon=77.1, degree=2)
    
    # Path pixels of highway
    highway_pixels = [(0.0, 0.0), (50.0, 0.0), (100.0, 0.0)]
    g.add_edge(0, 1, key=0, path_pixels=highway_pixels, length_px=100.0)

    # Create a dangling segment (Node 2 -> Node 3)
    # Node 3 is an endpoint (degree 1) located at (50.0, 3.0), which is close to the highway midpoint (50.0, 0.0)
    g.add_node(2, x=50.0, y=20.0, lat=12.01, lon=77.05, degree=2)
    g.add_node(3, x=50.0, y=3.0, lat=12.0003, lon=77.05, degree=1)
    dangling_pixels = [(50.0, 20.0), (50.0, 3.0)]
    g.add_edge(2, 3, key=0, path_pixels=dangling_pixels, length_px=17.0)

    # Sanity check: degree of 3 is 1
    assert g.degree(3) == 1

    # Perform snapping with threshold 5.0 (Node 3 is at distance 3.0 from highway midpoint)
    snapped = snap_endpoints(g, snap_distance=5.0)

    # Endpoint Node 3 should be gone (merged/snapped to new node)
    assert 3 not in snapped
    
    # There should be a new node representing the split point
    # Since original nodes were 0, 1, 2, 3, the new node will be 4
    assert 4 in snapped
    new_node_data = snapped.nodes[4]
    
    # New node should be located at the split point (50.0, 0.0)
    assert new_node_data["x"] == 50.0
    assert new_node_data["y"] == 0.0

    # The original highway edge 0 -> 1 should be split into 0 -> 4 and 4 -> 1
    assert snapped.has_edge(0, 4)
    assert snapped.has_edge(4, 1)
    assert not snapped.has_edge(0, 1)

    # Node 2 should be connected to the new split node 4
    assert snapped.has_edge(2, 4)
