"""Analytics Engine — Criticality metrics computation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import networkx as nx

from argus.core.errors import EmptyGraphError
from argus.core.logging import get_logger
from argus.core.protocols import CriticalityAnalyzer
from argus.core.types import AnalyticsResult, RoadGraph

log = get_logger(__name__)


@dataclass(slots=True)
class AnalyticsConfig:
    """Analytics module configuration."""

    metrics: list[str] = field(
        default_factory=lambda: [
            "betweenness",
            "closeness",
            "degree",
            "articulation",
            "bridges",
        ]
    )
    top_n: int = 10
    betweenness_normalized: bool = True
    closeness_normalized: bool = True
    degree_normalized: bool = True
    betweenness_weighted: bool = False
    k_sample: int | None = None


class CriticalityAnalyzerImpl(CriticalityAnalyzer):
    """Compute graph-theoretic criticality metrics.

    Supported metrics via config.metrics: ``betweenness``, ``closeness``,
    ``degree``, ``articulation``, ``bridges``.
    """

    ALL_METRICS = frozenset(
        {
            "betweenness",
            "closeness",
            "degree",
            "articulation",
            "bridges",
        }
    )

    def __init__(self, config: AnalyticsConfig | None = None):
        self.config = config or AnalyticsConfig()

    def analyze(
        self, road_graph: RoadGraph, config: AnalyticsConfig | None = None
    ) -> AnalyticsResult:
        """Compute criticality metrics on a validated road graph.

        The annotated graph carries metric values as node/edge attributes
        (e.g. ``betweenness``, ``closeness``, ``is_articulation``,
        ``is_bridge``).

        Raises EmptyGraphError if graph has no nodes/edges.
        """
        cfg = config or self.config
        graph = road_graph.graph
        self._validate_graph(graph)

        log.info(
            f"Analyzing criticality: {graph.number_of_nodes()}N, "
            f"{graph.number_of_edges()}E, "
            f"metrics={cfg.metrics}"
        )

        undirected = graph.to_undirected()
        annotated = graph.copy()
        results: dict[str, Any] = {}

        metrics_set = set(cfg.metrics)

        # Optimize k_sample for large graphs if not explicitly set
        k_val = cfg.k_sample
        if k_val is None and graph.number_of_nodes() > 500:
            k_val = 100
            log.info(
                f"Large graph detected ({graph.number_of_nodes()} nodes). "
                f"Optimizing betweenness computation with k={k_val} samples."
            )

        # 1. Betweenness centrality (weighted + unweighted)
        if "betweenness" in metrics_set:
            log.info("Computing betweenness centrality...")
            if cfg.betweenness_weighted:
                weight = _collect_edge_weights(undirected, key="length_px")
                node_bc = (
                    nx.betweenness_centrality(
                        undirected,
                        normalized=cfg.betweenness_normalized,
                        weight="weight",
                        k=k_val,
                    )
                    if weight
                    else nx.betweenness_centrality(
                        undirected,
                        normalized=cfg.betweenness_normalized,
                        k=k_val,
                    )
                )
                edge_bc = (
                    nx.edge_betweenness_centrality(
                        undirected,
                        normalized=cfg.betweenness_normalized,
                        weight="weight",
                        k=k_val,
                    )
                    if weight
                    else nx.edge_betweenness_centrality(
                        undirected,
                        normalized=cfg.betweenness_normalized,
                        k=k_val,
                    )
                )
            else:
                node_bc = nx.betweenness_centrality(
                    undirected,
                    normalized=cfg.betweenness_normalized,
                    k=k_val,
                )
                edge_bc = nx.edge_betweenness_centrality(
                    undirected,
                    normalized=cfg.betweenness_normalized,
                    k=k_val,
                )

            nx.set_node_attributes(annotated, node_bc, "betweenness")
            nx.set_edge_attributes(annotated, edge_bc, "betweenness")
            results["betweenness"] = {"nodes": node_bc, "edges": edge_bc}

        # 2. Closeness centrality
        if "closeness" in metrics_set:
            log.info("Computing closeness centrality...")
            node_cc = nx.closeness_centrality(undirected)
            nx.set_node_attributes(annotated, node_cc, "closeness")
            results["closeness"] = {"nodes": node_cc}

        # 3. Degree centrality
        if "degree" in metrics_set:
            log.info("Computing degree centrality...")
            node_dc = nx.degree_centrality(undirected)
            nx.set_node_attributes(annotated, node_dc, "degree_centrality")
            results["degree"] = {"nodes": node_dc}

        # 4. Articulation points
        if "articulation" in metrics_set:
            log.info("Finding articulation points...")
            art_points = list(nx.articulation_points(undirected))
            flag_map = {n: int(n in art_points) for n in graph.nodes()}
            nx.set_node_attributes(annotated, flag_map, "is_articulation")
            results["articulation_points"] = art_points

        # 5. Bridges
        if "bridges" in metrics_set:
            log.info("Finding bridges...")
            bridges = list(nx.bridges(undirected))
            _annotate_bridges(annotated, bridges)
            results["bridges"] = bridges

        # 6. Connected components (always computed)
        components = list(nx.connected_components(undirected))
        results["components"] = {
            "count": len(components),
            "sizes": [len(c) for c in components],
            "largest_size": max(len(c) for c in components) if components else 0,
        }

        # 7. Resilience summary
        summary = self._compute_summary(undirected, results, cfg)

        report = self._generate_report(graph, results, cfg.top_n)

        return AnalyticsResult(
            annotated_graph=RoadGraph(
                graph=annotated,
                crs=road_graph.crs,
                bounds=road_graph.bounds,
                metadata=road_graph.metadata,
            ),
            report=report,
            summary=summary,
        )

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_graph(graph: nx.MultiDiGraph) -> None:
        if graph.number_of_nodes() == 0:
            raise EmptyGraphError("Graph has no nodes")

    # ------------------------------------------------------------------
    # Resilience summary
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_summary(
        undirected: nx.Graph,
        results: dict[str, Any],
        _cfg: AnalyticsConfig,
    ) -> dict[str, Any]:
        summary: dict[str, Any] = {
            "metrics_computed": sorted(k for k in results if k not in ("components",)),
            "graph_stats": {
                "nodes": undirected.number_of_nodes(),
                "edges": undirected.number_of_edges(),
                "connected_components": results.get("components", {}).get("count", 0),
                "largest_component_size": results.get("components", {}).get("largest_size", 0),
            },
            "resilience": {},
        }

        # Network level metrics on largest component
        comps = results.get("components", {})
        if comps.get("count", 0) > 0 and comps.get("largest_size", 1) > 1:
            largest_nodes = max(nx.connected_components(undirected), key=len, default=set())
            if len(largest_nodes) > 1:
                subgraph = undirected.subgraph(largest_nodes).copy()
                try:
                    summary["resilience"]["avg_path_length"] = float(
                        nx.average_shortest_path_length(subgraph)
                    )
                except nx.NetworkXError:
                    summary["resilience"]["avg_path_length"] = None

                try:
                    summary["resilience"]["diameter"] = int(nx.diameter(subgraph))
                except nx.NetworkXError:
                    summary["resilience"]["diameter"] = None

        # Count articulation points and bridges
        art_count = len(results.get("articulation_points", []))
        bridge_count = len(results.get("bridges", []))
        summary["resilience"]["articulation_points_count"] = art_count
        summary["resilience"]["bridges_count"] = bridge_count

        # Vulnerability score: fraction of nodes that are articulation
        total_nodes = undirected.number_of_nodes()
        if total_nodes > 0:
            summary["resilience"]["vulnerability_ratio"] = round(art_count / total_nodes, 4)

        return summary

    # ------------------------------------------------------------------
    # Report generation
    # ------------------------------------------------------------------

    @staticmethod
    def _generate_report(
        graph: nx.MultiDiGraph, results: dict[str, Any], top_n: int
    ) -> dict[str, Any]:
        report: dict[str, Any] = {}

        if "betweenness" in results:
            node_bc = results["betweenness"]["nodes"]
            edge_bc = results["betweenness"]["edges"]
            report["top_nodes_betweenness"] = sorted(
                node_bc.items(), key=lambda x: x[1], reverse=True
            )[:top_n]
            report["top_edges_betweenness"] = sorted(
                edge_bc.items(), key=lambda x: x[1], reverse=True
            )[:top_n]

        if "closeness" in results:
            node_cc = results["closeness"]["nodes"]
            report["top_nodes_closeness"] = sorted(
                node_cc.items(), key=lambda x: x[1], reverse=True
            )[:top_n]

        if "degree" in results:
            node_dc = results["degree"]["nodes"]
            report["top_nodes_degree"] = sorted(node_dc.items(), key=lambda x: x[1], reverse=True)[
                :top_n
            ]

        if "articulation_points" in results:
            aps = results["articulation_points"][:top_n]
            report["articulation_points"] = aps

            aps_coords = []
            for n in aps:
                node_data = graph.nodes[n]
                aps_coords.append(
                    {
                        "id": n,
                        "lat": float(node_data.get("lat", 0.0)),
                        "lon": float(node_data.get("lon", 0.0)),
                    }
                )
            report["articulation_points_with_coordinates"] = aps_coords

        if "bridges" in results:
            bg = results["bridges"][:top_n]
            report["bridges"] = bg

            bridges_coords = []
            for u, v in bg:
                u_data = graph.nodes[u]
                v_data = graph.nodes[v]
                bridges_coords.append(
                    {
                        "u": u,
                        "v": v,
                        "u_lat": float(u_data.get("lat", 0.0)),
                        "u_lon": float(u_data.get("lon", 0.0)),
                        "v_lat": float(v_data.get("lat", 0.0)),
                        "v_lon": float(v_data.get("lon", 0.0)),
                    }
                )
            report["bridges_with_coordinates"] = bridges_coords

        return report


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _collect_edge_weights(undirected: nx.Graph, key: str = "length_px") -> bool:
    """Attach edge weights from node/edge data.  Returns True if weights exist."""
    found = False
    for _u, _v, data in undirected.edges(data=True):
        w = data.get(key)
        if w is not None:
            data["weight"] = float(w)
            found = True
    return found


def _annotate_bridges(graph: nx.MultiDiGraph, bridges: list[tuple[int, int]]) -> None:
    """Mark edges that are bridges with ``is_bridge`` attribute on the copy."""
    bridge_set = {(min(a, b), max(a, b)) for a, b in bridges}
    for n_u, n_v, key in graph.edges(keys=True):
        pair = (min(n_u, n_v), max(n_u, n_v))
        graph[n_u][n_v][key]["is_bridge"] = int(pair in bridge_set)


def load_analytics_config_from_yaml() -> AnalyticsConfig:
    """Load analytics config from ``configs/analytics.yaml``."""
    from omegaconf import OmegaConf  # pyright: ignore[reportMissingImports]

    from argus.core.config import load_config

    raw = load_config("analytics")
    cfg_dict = OmegaConf.to_container(raw, resolve=True)  # type: ignore[union-attr, call-overload]

    metrics_list = cfg_dict.get("metrics", [])  # type: ignore[union-attr]
    if "all" in metrics_list or not metrics_list:
        metrics_list = sorted(CriticalityAnalyzerImpl.ALL_METRICS)  # type: ignore[operator]

    betweenness_cfg = cfg_dict.get("betweenness", {})  # type: ignore[union-attr]
    closeness_cfg = cfg_dict.get("closeness", {})  # type: ignore[union-attr]
    degree_cfg = cfg_dict.get("degree", {})  # type: ignore[union-attr]

    return AnalyticsConfig(
        metrics=metrics_list,
        top_n=cfg_dict.get("top_n", 10),  # type: ignore[union-attr]
        betweenness_normalized=betweenness_cfg.get("normalized", True),
        closeness_normalized=closeness_cfg.get("normalized", True),
        degree_normalized=degree_cfg.get("normalized", True),
        betweenness_weighted=betweenness_cfg.get("weighted", False),
        k_sample=betweenness_cfg.get("k", None),
    )
