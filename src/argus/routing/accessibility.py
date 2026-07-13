"""Accessibility analysis utilities."""

from __future__ import annotations

from typing import Any

import networkx as nx

from argus.core.logging import get_logger

log = get_logger(__name__)


class AccessibilityAnalyzer:
    """Analyze reachability and accessibility on road networks."""

    def __init__(self, config: dict | None = None):
        self.config = config or {}

    def compute_service_area(
        self,
        graph: nx.MultiDiGraph,
        origin: Any,
        max_distance: float,
    ) -> set:
        """Compute all nodes reachable within max_distance from origin."""
        try:
            lengths = nx.single_source_dijkstra_path_length(graph, origin, weight="length")
            return {n for n, d in lengths.items() if d <= max_distance}
        except nx.NetworkXError:
            return set()

    def compute_iso_curve(
        self,
        graph: nx.MultiDiGraph,
        origin: Any,
        distances: list[float],
    ) -> dict[float, set]:
        """Compute isochrones (nodes reachable within each distance threshold)."""
        try:
            lengths = nx.single_source_dijkstra_path_length(graph, origin, weight="length")
            _ = max(distances)  # used for validation
            results = {}
            for d in distances:
                results[d] = {n for n, dist in lengths.items() if dist <= d}
            return results
        except nx.NetworkXError:
            return {d: set() for d in distances}

    def compute_coverage(
        self,
        graph: nx.MultiDiGraph,
        facilities: list[Any],
        max_distance: float,
    ) -> dict[str, float]:
        """Compute population/area coverage by facilities."""
        # TODO: Implement with population data
        return {}
