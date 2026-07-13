"""Graph cleaning utilities.

Operations executed in order after skeleton-to-graph conversion:
  - Remove small isolated components
  - Merge close nodes (within pixel-distance threshold)
  - Snap dangling endpoints to nearby edges
  - Remove short dangling edges (degree-1 nodes with tiny edges)
  - Simplify degree-2 chains (Douglas-Peucker)
"""

from __future__ import annotations

from typing import Any

import networkx as nx
import numpy as np
from numpy.typing import NDArray

from argus.core.logging import get_logger

log = get_logger(__name__)


def _clean_edge_data(data: dict, key: int) -> dict[str, Any]:
    """Extract only string-keyed attributes from edge data."""
    clean: dict[str, Any] = {}
    for k, v in data.items():
        if isinstance(k, str):
            clean[k] = v
    clean.setdefault("key", key)
    return clean


def remove_isolated_small_components(
    graph: nx.MultiDiGraph,
    min_nodes: int = 10,
) -> nx.MultiDiGraph:
    """Remove connected components smaller than *min_nodes*.

    Keeps the largest component, discards the rest.
    """
    if graph.number_of_nodes() == 0:
        return graph

    undirected = graph.to_undirected()
    components = list(nx.connected_components(undirected))
    if len(components) <= 1:
        return graph

    largest = max(components, key=len)
    removed = 0
    for comp in components:
        if comp == largest or len(comp) >= min_nodes:
            continue
        graph.remove_nodes_from(comp)
        removed += len(comp)

    if removed > 0:
        log.debug(f"Removed {removed} nodes from small components")
    return graph


def merge_close_nodes(
    graph: nx.MultiDiGraph,
    merge_distance: float = 5.0,
) -> nx.MultiDiGraph:
    """Merge nodes whose pixel distance is less than *merge_distance*.

    Retains the node with the higher degree.  Reconnects all edges of the
    redundant node to the surviving node.
    """
    if graph.number_of_nodes() < 2:
        return graph

    node_list = list(graph.nodes(data=True))
    coords: dict[int, NDArray[np.float64]] = {}

    for nid, data in node_list:
        px = float(data.get("x", 0))
        py = float(data.get("y", 0))
        coords[nid] = np.array([px, py], dtype=np.float64)

    coord_array = np.array(list(coords.values()), dtype=np.float64)
    node_ids = list(coords.keys())

    from scipy.spatial import cKDTree

    tree = cKDTree(coord_array)
    pairs = tree.query_pairs(merge_distance)

    if not pairs:
        return graph

    # Build merge groups (connected components in the merge graph)
    merge_graph = nx.Graph()
    merge_graph.add_nodes_from(node_ids)
    for i, j in pairs:
        merge_graph.add_edge(node_ids[i], node_ids[j])

    merged_count = 0
    for group in nx.connected_components(merge_graph):
        if len(group) <= 1:
            continue

        survivors = sorted(group, key=lambda n: graph.degree(n), reverse=True)
        survivor = survivors[0]
        victims = survivors[1:]

        survivor_data = graph.nodes[survivor]
        survivor_coord = (float(survivor_data.get("x", 0)), float(survivor_data.get("y", 0)))

        for victim in victims:
            if victim == survivor:
                continue
            if victim not in graph:
                continue

            # Collect all edges involving the victim, adjusting geometry endpoints
            edges_to_reroute: list[tuple[int, int, dict]] = []
            for pred, _, key, data in graph.in_edges(victim, data=True, keys=True):
                if pred != survivor and pred != victim:
                    ed = _clean_edge_data(data, key)
                    if "path_pixels" in ed and len(ed["path_pixels"]) > 0:
                        pix = list(ed["path_pixels"])
                        pix[-1] = survivor_coord
                        ed["path_pixels"] = pix
                    edges_to_reroute.append((pred, survivor, ed))
            for _, succ, key, data in graph.out_edges(victim, data=True, keys=True):
                if succ != survivor and succ != victim:
                    ed = _clean_edge_data(data, key)
                    if "path_pixels" in ed and len(ed["path_pixels"]) > 0:
                        pix = list(ed["path_pixels"])
                        pix[0] = survivor_coord
                        ed["path_pixels"] = pix
                    edges_to_reroute.append((survivor, succ, ed))

            graph.remove_node(victim)

            for u, v, edata in edges_to_reroute:
                k = edata.pop("key", None)
                if not graph.has_edge(u, v, key=k):
                    graph.add_edge(u, v, key=k, **edata)
            merged_count += 1

    if merged_count > 0:
        log.debug(f"Merged {merged_count} nodes within distance {merge_distance}")
    return graph


def snap_endpoints(
    graph: nx.MultiDiGraph,
    snap_distance: float = 10.0,
) -> nx.MultiDiGraph:
    """Snap degree-1 (endpoint) nodes to nearby nodes or edges.

    If an endpoint is within *snap_distance* of another node, merge it into
    that node.  If it is close to an edge midpoint, split that edge and
    connect the endpoint.
    """
    if graph.number_of_nodes() < 2:
        return graph

    node_list = list(graph.nodes(data=True))
    endpoints: dict[int, NDArray[np.float64]] = {}
    non_endpoints: dict[int, NDArray[np.float64]] = {}

    for nid, data in node_list:
        px = float(data.get("x", 0))
        py = float(data.get("y", 0))
        coord = np.array([px, py], dtype=np.float64)
        if graph.degree(nid) == 1:
            endpoints[nid] = coord
        else:
            non_endpoints[nid] = coord

    if not endpoints:
        return graph

    from scipy.spatial import cKDTree

    ep_ids = list(endpoints.keys())
    ep_arr = np.array(list(endpoints.values()), dtype=np.float64)

    # 1. Snap endpoints to nearby non-endpoint nodes
    if non_endpoints:
        ne_ids = list(non_endpoints.keys())
        ne_arr = np.array(list(non_endpoints.values()), dtype=np.float64)
        ne_tree = cKDTree(ne_arr)

        distances, indices = ne_tree.query(ep_arr, distance_upper_bound=snap_distance)
        for i, (dist, nidx) in enumerate(zip(distances, indices, strict=True)):
            if dist > snap_distance:
                continue
            ep = ep_ids[i]
            target = ne_ids[nidx]
            if ep not in graph:
                continue
            
            target_data = graph.nodes[target]
            target_coord = (float(target_data.get("x", 0)), float(target_data.get("y", 0)))

            # Collect edges to reroute then merge, adjusting geometry
            edges_to_reroute: list[tuple[int, int, dict[str, Any]]] = []
            for pred, _, key, data in graph.in_edges(ep, data=True, keys=True):
                if pred != target and pred != ep:
                    ed = _clean_edge_data(data, key)
                    if "path_pixels" in ed and len(ed["path_pixels"]) > 0:
                        pix = list(ed["path_pixels"])
                        pix[-1] = target_coord
                        ed["path_pixels"] = pix
                    edges_to_reroute.append((pred, target, ed))
            for _, succ, key, data in graph.out_edges(ep, data=True, keys=True):
                if succ != target and succ != ep:
                    ed = _clean_edge_data(data, key)
                    if "path_pixels" in ed and len(ed["path_pixels"]) > 0:
                        pix = list(ed["path_pixels"])
                        pix[0] = target_coord
                        ed["path_pixels"] = pix
                    edges_to_reroute.append((target, succ, ed))

            graph.remove_node(ep)
            for u, v, edata in edges_to_reroute:
                k = edata.pop("key", None)
                if not graph.has_edge(u, v, key=k):
                    graph.add_edge(u, v, key=k, **edata)
            log.debug(f"Snapped endpoint {ep} to node {target}")

    # 2. Snap remaining endpoints to nearby edge midpoints (splitting the edge)
    endpoints_active = {nid: coord for nid, coord in endpoints.items() if nid in graph and graph.degree(nid) == 1}

    for ep, ep_coord in list(endpoints_active.items()):
        if ep not in graph or graph.degree(ep) != 1:
            continue

        best_edge = None
        best_dist = float("inf")
        best_idx = -1
        best_point = None

        for u, v, key, edata in list(graph.edges(data=True, keys=True)):
            if u == ep or v == ep:
                continue

            pixels = edata.get("path_pixels", [])
            if len(pixels) < 2:
                continue

            for idx in range(len(pixels)):
                px, py = pixels[idx]
                dist = np.hypot(px - ep_coord[0], py - ep_coord[1])
                if dist < best_dist:
                    best_dist = dist
                    best_edge = (u, v, key, edata)
                    best_idx = idx
                    best_point = (px, py)

        if best_edge and best_dist <= snap_distance:
            u, v, key, edata = best_edge
            pixels = edata.get("path_pixels", [])

            # Split the edge u -> v at best_idx
            new_node = max(graph.nodes()) + 1

            u_data = graph.nodes[u]
            v_data = graph.nodes[v]
            u_lat, u_lon = u_data.get("lat", 0.0), u_data.get("lon", 0.0)
            v_lat, v_lon = v_data.get("lat", 0.0), v_data.get("lon", 0.0)

            frac = best_idx / (len(pixels) - 1) if len(pixels) > 1 else 0.5
            new_lat = u_lat + (v_lat - u_lat) * frac
            new_lon = u_lon + (v_lon - u_lon) * frac

            # Add split node
            graph.add_node(new_node, x=best_point[0], y=best_point[1], lat=new_lat, lon=new_lon)

            # Split path_pixels
            left_pixels = pixels[:best_idx + 1]
            right_pixels = pixels[best_idx:]

            # Remove original edge
            graph.remove_edge(u, v, key)

            # Add split edges
            if len(left_pixels) >= 2:
                graph.add_edge(u, new_node, key=0, path_pixels=left_pixels, length_px=float(len(left_pixels)))
            else:
                graph.add_edge(u, new_node, key=0, path_pixels=[(u_data["x"], u_data["y"]), best_point], length_px=2.0)

            if len(right_pixels) >= 2:
                graph.add_edge(new_node, v, key=0, path_pixels=right_pixels, length_px=float(len(right_pixels)))
            else:
                graph.add_edge(new_node, v, key=0, path_pixels=[best_point, (v_data["x"], v_data["y"])], length_px=2.0)

            # Reroute ep edges to new_node, snapping their endpoints
            edges_to_reroute = []
            for pred, _, k, data in graph.in_edges(ep, data=True, keys=True):
                ed = _clean_edge_data(data, k)
                if "path_pixels" in ed and len(ed["path_pixels"]) > 0:
                    pix = list(ed["path_pixels"])
                    pix[-1] = best_point
                    ed["path_pixels"] = pix
                edges_to_reroute.append((pred, new_node, ed))
            for _, succ, k, data in graph.out_edges(ep, data=True, keys=True):
                ed = _clean_edge_data(data, k)
                if "path_pixels" in ed and len(ed["path_pixels"]) > 0:
                    pix = list(ed["path_pixels"])
                    pix[0] = best_point
                    ed["path_pixels"] = pix
                edges_to_reroute.append((new_node, succ, ed))

            graph.remove_node(ep)
            for pred, succ, ed in edges_to_reroute:
                if not graph.has_edge(pred, succ):
                    graph.add_edge(pred, succ, **ed)

            log.debug(f"Snapped endpoint {ep} to split edge between {u} and {v}")

    return graph


def remove_dangling_nodes(
    graph: nx.MultiDiGraph,
    max_length: float = 5.0,
) -> nx.MultiDiGraph:
    """Remove degree-1 nodes connected by edges shorter than *max_length* pixels.

    Operates iteratively — removing one dangling node may expose a new one.
    """
    changed = True
    removed = 0
    while changed:
        changed = False
        for node in list(graph.nodes()):
            if graph.degree(node) != 1:
                continue
            removal_candidate: tuple[int, float] | None = None
            for _, _, _, data in graph.in_edges(node, data=True, keys=True):
                length_px = float(data.get("length_px", 0))
                if length_px <= 0 or length_px > max_length:
                    continue
                removal_candidate = (node, length_px)
                break
            else:
                for _, _, _, data in graph.out_edges(node, data=True, keys=True):
                    length_px = float(data.get("length_px", 0))
                    if length_px <= 0 or length_px > max_length:
                        continue
                    removal_candidate = (node, length_px)
                    break

            if removal_candidate is None:
                continue
            node_to_remove, _ = removal_candidate
            graph.remove_node(node_to_remove)
            changed = True
            removed += 1
            break
    if removed > 0:
        log.debug(f"Removed {removed} dangling nodes (max_length={max_length})")
    return graph


def simplify_chains(
    graph: nx.MultiDiGraph,
    tolerance: float = 2.0,
) -> nx.MultiDiGraph:
    """Simplify degree-2 node chains using Douglas-Peucker on edge geometry.

    For each degree-2 node, combine its incoming and outgoing edges if they
    form a near-linear path, removing the intermediate node and merging the
    edge geometry.
    """
    from shapely.geometry import LineString

    changed = True
    simplified = 0
    while changed:
        changed = False
        for node in list(graph.nodes()):
            if graph.degree(node) != 2:
                continue

            preds = list(graph.predecessors(node))
            succs = list(graph.successors(node))
            if not preds or not succs:
                continue

            pred = preds[0]
            succ = succs[0]

            # Get the two edge geometries
            in_edata = _first_edge_data(graph, pred, node)
            out_edata = _first_edge_data(graph, node, succ)
            if not in_edata or not out_edata:
                continue

            in_pixels = _edge_pixels(in_edata)
            out_pixels = _edge_pixels(out_edata)
            if not in_pixels or not out_pixels:
                continue

            # Build combined line and check Douglas-Peucker
            combined = np.array(in_pixels + out_pixels[1:], dtype=np.float64)
            if len(combined) < 2:
                continue

            line = LineString([(p[0], p[1]) for p in combined])
            simplified_line = line.simplify(tolerance, preserve_topology=False)
            simp_pixels = [
                (x, y) for x, y in zip(simplified_line.xy[0], simplified_line.xy[1], strict=True)
            ]

            if len(simp_pixels) < 2:
                continue

            # Connect pred → succ directly with merged geometry
            graph.add_edge(
                pred,
                succ,
                key=0,
                path_pixels=simp_pixels,
                length_px=float(len(simp_pixels)),
            )
            graph.remove_node(node)
            changed = True
            simplified += 1

    if simplified > 0:
        log.debug(f"Simplified {simplified} degree-2 chain nodes (tolerance={tolerance})")
    return graph


def _first_edge_data(graph: nx.MultiDiGraph, u: int, v: int) -> dict[str, Any] | None:
    """Extract the first edge's attribute dict from a MultiDiGraph edge."""
    raw = graph.get_edge_data(u, v, default=None)
    if raw is None:
        return None
    for _, edata in raw.items():
        return edata
    return None


def _edge_pixels(edge_data: dict[str, Any]) -> list[tuple[float, float]]:
    """Extract the ``path_pixels`` list from edge data."""
    return edge_data.get("path_pixels", [])
