"""Routing Engine — Pathfinding and accessibility."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import networkx as nx

from argus.core.logging import get_logger
from argus.core.protocols import Router
from argus.core.types import RoadGraph, RouteResult

log = get_logger(__name__)


@dataclass(slots=True)
class RouteQuery:
    origin: tuple[float, float]
    destination: tuple[float, float]
    algorithm: str = "dijkstra"
    k: int = 3


@dataclass(slots=True)
class AccessibilityQuery:
    origins: list[tuple[float, float]]
    destinations: list[tuple[float, float]]
    max_distance: float | None = None


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in metres between two lat/lon points."""
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class RouterImpl(Router):
    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self.default_algorithm = self.config.get("default_algorithm", "dijkstra")
        self._speed_kmh = float(self.config.get("accessibility", {}).get("speed_kmh", 40))
        self._speed_ms = self._speed_kmh / 3.6

    def find_route(self, road_graph: RoadGraph, query: RouteQuery | dict) -> RouteResult:
        if isinstance(query, dict):
            query = RouteQuery(**query)

        log.info(f"Route: {query.origin} → {query.destination} [{query.algorithm}]")

        graph = road_graph.graph
        weight_attr = self._detect_weight_attr(graph)
        origin_node = self._nearest_node(graph, query.origin)
        dest_node = self._nearest_node(graph, query.destination)

        if origin_node is None or dest_node is None:
            log.warning("No valid nodes found")
            return RouteResult(routes=[], accessibility={}, comparison=None)

        routes: list[dict[str, Any]] = []
        try:
            if query.algorithm == "dijkstra":
                path = nx.shortest_path(graph, origin_node, dest_node, weight=weight_attr)
                routes.append(self._path_to_geojson(graph, path))
            elif query.algorithm == "astar":
                heuristic = _make_astar_heuristic(graph, dest_node, weight_attr)
                path = nx.astar_path(
                    graph,
                    origin_node,
                    dest_node,
                    heuristic=heuristic,
                    weight=weight_attr,
                )
                routes.append(self._path_to_geojson(graph, path))
            elif query.algorithm == "k_shortest":
                simple_g = nx.Graph(graph)
                for u, v, data in graph.edges(data=True):
                    w = float(data.get(weight_attr, data.get("length_px", 1.0)))
                    if simple_g.has_edge(u, v):
                        simple_g[u][v]["weight"] = min(
                            simple_g[u][v].get("weight", float("inf")), w
                        )
                    else:
                        simple_g.add_edge(u, v, weight=w)
                paths = list(
                    nx.shortest_simple_paths(simple_g, origin_node, dest_node, weight="weight")
                )
                for path in paths[: query.k]:
                    routes.append(self._path_to_geojson(graph, path))
            else:
                log.warning(f"Unknown algorithm '{query.algorithm}', falling back to dijkstra")
                path = nx.shortest_path(graph, origin_node, dest_node, weight=weight_attr)
                routes.append(self._path_to_geojson(graph, path))
        except nx.NetworkXNoPath:
            log.warning("No path found")

        return RouteResult(routes=routes, accessibility={}, comparison=None)

    def accessibility(
        self, road_graph: RoadGraph, query: AccessibilityQuery | dict
    ) -> dict[str, Any]:
        if isinstance(query, dict):
            query = AccessibilityQuery(**query)

        graph = road_graph.graph
        weight_attr = self._detect_weight_attr(graph)
        results: dict[str, Any] = {}

        for origin in query.origins:
            origin_node = self._nearest_node(graph, origin)
            if origin_node is None:
                continue
            try:
                lengths = nx.single_source_dijkstra_path_length(
                    graph, origin_node, weight=weight_attr
                )
            except nx.NetworkXError:
                continue

            reachable = []
            unreachable = []
            for dest in query.destinations:
                dest_node = self._nearest_node(graph, dest)
                if dest_node in lengths:
                    reachable.append({"destination": dest, "distance_m": lengths[dest_node]})
                else:
                    unreachable.append(dest)

            results[str(origin)] = {
                "reachable": reachable,
                "unreachable": unreachable,
                "reachable_count": len(reachable),
                "total": len(query.destinations),
            }

        return results

    def compare_routes(
        self,
        base: list[dict[str, Any]],
        modified: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Compare baseline routes to post-disaster routes."""
        base_len = base[0]["properties"]["length_m"] if base else None
        base_time = base[0]["properties"]["travel_time_s"] if base else None
        mod_len = modified[0]["properties"]["length_m"] if modified else None
        mod_time = modified[0]["properties"]["travel_time_s"] if modified else None

        delta_len = (mod_len - base_len) if base_len and mod_len else None
        delta_time = (mod_time - base_time) if base_time and mod_time else None
        
        status = "unchanged"
        tolerance = 0.1  # 10 cm tolerance for float comparisons
        if not modified:
            status = "unreachable"
        elif delta_len is not None and delta_len > tolerance:
            status = "detour"
        else:
            status = "unchanged"

        return {
            "baseline_length_m": base_len,
            "baseline_time_s": base_time,
            "modified_length_m": mod_len,
            "modified_time_s": mod_time,
            "delta_length_m": delta_len,
            "delta_time_s": delta_time,
            "status": status,
            "alternative_count": max(0, len(modified) - 1),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _detect_weight_attr(self, graph: nx.MultiDiGraph) -> str:
        """Detect which edge attribute to use for routing weight.

        Tries ``length`` first (M5 simulation adds this), falls back
        to ``length_px`` (from M3 graph builder).
        """
        # Sample a few edges
        for _u, _v, _k, data in graph.edges(data=True, keys=True):
            if "length" in data:
                return "length"
            if "length_px" in data:
                return "length_px"
            break
        return "length"  # default

    def _nearest_node(self, graph: nx.MultiDiGraph, point: tuple[float, float]) -> Any | None:
        lat, lon = point
        best_node = None
        best_dist = float("inf")
        for node, data in graph.nodes(data=True):
            node_lat = data.get("lat", 0)
            node_lon = data.get("lon", 0)
            d = (lat - node_lat) ** 2 + (lon - node_lon) ** 2
            if d < best_dist:
                best_dist = d
                best_node = node
        return best_node

    def _path_to_geojson(self, graph: nx.MultiDiGraph, path: list[Any]) -> dict[str, Any]:
        coords: list[list[float]] = []
        total_length = 0.0

        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            edge_data = graph[u][v]
            first_key = next(iter(edge_data))
            edge = edge_data[first_key]
            u_data = graph.nodes[u]
            coords.append([u_data.get("lon", 0), u_data.get("lat", 0)])
            edge_length = float(edge.get("length", edge.get("length_px", 0)))
            total_length += edge_length

        v_data = graph.nodes[path[-1]]
        coords.append([v_data.get("lon", 0), v_data.get("lat", 0)])
        travel_time = total_length / self._speed_ms if self._speed_ms > 0 else 0.0

        return {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": coords},
            "properties": {
                "length_m": total_length,
                "travel_time_s": travel_time,
                "speed_kmh": self._speed_kmh,
                "nodes": path,
            },
        }


def _estimate_heuristic_scale(graph: nx.MultiDiGraph, weight_attr: str) -> float:
    """Estimate a scaling factor so the A* heuristic remains admissible.

    Calculates the minimum ratio of edge weight to geographical distance.
    """
    ratios: list[float] = []
    for u, v, data in graph.edges(data=True):
        w = float(data.get(weight_attr, 1.0))
        u_lat = graph.nodes[u].get("lat", 0.0)
        u_lon = graph.nodes[u].get("lon", 0.0)
        v_lat = graph.nodes[v].get("lat", 0.0)
        v_lon = graph.nodes[v].get("lon", 0.0)
        dist = _haversine(u_lat, u_lon, v_lat, v_lon)
        if dist > 1e-3:
            ratios.append(w / dist)
    return min(ratios) if ratios else 1.0


def _make_astar_heuristic(graph: nx.MultiDiGraph, target: Any, weight_attr: str) -> Any:
    """Return a heuristic function for A* using haversine distance to target."""
    t_lat = graph.nodes[target].get("lat", 0)
    t_lon = graph.nodes[target].get("lon", 0)
    scale = _estimate_heuristic_scale(graph, weight_attr)

    def heuristic(u: Any, v: Any) -> float:  # noqa: ARG001
        u_lat = graph.nodes[u].get("lat", 0)
        u_lon = graph.nodes[u].get("lon", 0)
        return _haversine(u_lat, u_lon, t_lat, t_lon) * scale

    return heuristic


def export_route_geojson(routes: list[dict[str, Any]], path: Any) -> None:
    """Write routes as a GeoJSON FeatureCollection file."""
    import json

    fc = {"type": "FeatureCollection", "features": routes}
    with open(str(path), "w") as f:
        json.dump(fc, f, indent=2)
    log.info(f"Exported {len(routes)} route(s) → {path}")
