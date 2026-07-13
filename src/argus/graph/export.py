"""Graph export utilities (GraphML, GeoJSON, Pickle)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import networkx as nx
from shapely.geometry import LineString, Point, mapping

from argus.core.logging import get_logger
from argus.core.types import RoadGraph

log = get_logger(__name__)


def export_graphml(road_graph: RoadGraph, path: Path) -> Path:
    """Export RoadGraph to GraphML.

    MultiDiGraph is converted to a simple Graph for export (GraphML does not
    support multiple edges between the same node pair).
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    wx_graph = nx.Graph()
    for node, data in road_graph.graph.nodes(data=True):
        wx_graph.add_node(node, **_node_attrs_for_export(data))
    added: set[tuple[int, int]] = set()
    for u, v, _key, data in road_graph.graph.edges(data=True, keys=True):
        pair = (min(u, v), max(u, v))
        if pair in added:
            continue
        added.add(pair)
        wx_graph.add_edge(u, v, **_edge_attrs_for_export(data))

    nx.write_graphml(wx_graph, str(path))
    log.info(
        f"Exported GraphML ({wx_graph.number_of_nodes()}N, {wx_graph.number_of_edges()}E) → {path}"
    )
    return path


def export_geojson(road_graph: RoadGraph, path: Path) -> Path:
    """Export RoadGraph to GeoJSON (one file for nodes, one for edges)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    nodes_path = path.parent / f"{path.stem}_nodes.geojson"
    edges_path = path.parent / f"{path.stem}_edges.geojson"

    _write_nodes_geojson(road_graph, nodes_path)
    _write_edges_geojson(road_graph, edges_path)

    log.info(f"Exported GeoJSON → {nodes_path.name} + {edges_path.name}")
    return path


def export_pickle(road_graph: RoadGraph, path: Path) -> Path:
    """Export RoadGraph as pickle (preserves full NetworkX structure)."""
    import pickle

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(road_graph, f)
    log.info(f"Exported pickle → {path}")
    return path


def load_pickle(path: Path) -> RoadGraph:
    """Load RoadGraph from pickle."""
    import pickle

    with open(path, "rb") as f:
        road_graph = pickle.load(f)
    log.info(f"Loaded pickle from {path}")
    return road_graph


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------


def _node_attrs_for_export(data: dict[str, Any]) -> dict[str, float | int]:
    return {
        "x": float(data.get("x", 0)),
        "y": float(data.get("y", 0)),
        "lat": float(data.get("lat", 0)),
        "lon": float(data.get("lon", 0)),
        "degree": int(data.get("degree", 0)),
    }


def _edge_attrs_for_export(data: dict[str, Any]) -> dict[str, float]:
    return {"length_px": float(data.get("length_px", 0))}


def _write_nodes_geojson(road_graph: RoadGraph, path: Path) -> None:
    features: list[dict[str, Any]] = []
    for node_id, data in road_graph.graph.nodes(data=True):
        lon = data.get("lon", 0.0)
        lat = data.get("lat", 0.0)
        features.append(
            {
                "type": "Feature",
                "geometry": mapping(Point(lon, lat)),
                "properties": {
                    "id": node_id,
                    "x": float(data.get("x", 0)),
                    "y": float(data.get("y", 0)),
                    "degree": int(data.get("degree", 0)),
                },
            }
        )
    _write_collection(features, path)


def _write_edges_geojson(road_graph: RoadGraph, path: Path) -> None:
    features: list[dict[str, Any]] = []
    for u, v, key, data in road_graph.graph.edges(data=True, keys=True):
        geom = _edge_geometry(road_graph, u, v, data)
        features.append(
            {
                "type": "Feature",
                "geometry": mapping(geom),
                "properties": {
                    "u": u,
                    "v": v,
                    "key": key,
                    "length_px": float(data.get("length_px", 0)),
                },
            }
        )
    _write_collection(features, path)


def _edge_geometry(
    road_graph: RoadGraph,
    u: int,
    v: int,
    data: dict[str, Any],
) -> LineString:
    """Build a geo LineString for an edge using path_pixels or node positions."""
    path_pixels = data.get("path_pixels", [])
    if path_pixels and len(path_pixels) >= 2:
        a, b, c, d, e, f = _get_affine(road_graph)
        coords = [(a * px + b * py + c, d * px + e * py + f) for px, py in path_pixels]
        return LineString(coords)

    u_lon = road_graph.graph.nodes[u].get("lon", 0)
    u_lat = road_graph.graph.nodes[u].get("lat", 0)
    v_lon = road_graph.graph.nodes[v].get("lon", 0)
    v_lat = road_graph.graph.nodes[v].get("lat", 0)
    return LineString([(u_lon, u_lat), (v_lon, v_lat)])


def _get_affine(road_graph: RoadGraph) -> tuple[float, float, float, float, float, float]:
    """Get the affine transform from graph metadata (stored by builder).

    Falls back to identity if not available.
    """
    transform = road_graph.metadata.get("transform")
    if transform and len(transform) == 6:
        return tuple(float(v) for v in transform)  # type: ignore[return-value]
    return (1.0, 0.0, 0.0, 0.0, -1.0, 0.0)


def _write_collection(features: list[dict[str, Any]], path: Path) -> None:
    collection = {"type": "FeatureCollection", "features": features}
    with open(path, "w") as f:
        json.dump(collection, f, indent=2)
