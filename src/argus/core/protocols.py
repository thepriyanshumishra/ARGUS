"""Interface protocols for all ARGUS modules.

These protocols define the contracts between modules. Any implementation
satisfying a protocol can be swapped without changing downstream code.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

from argus.core.types import (
    AnalyticsResult,
    RasterImage,
    RoadGraph,
    RoadMask,
    RouteResult,
    SimulationResult,
)


class DataInput(Protocol):
    """Data loading interface (M1)."""

    def load_imagery(self, source: str, config: Any) -> RasterImage: ...
    def load_vector(self, source: str, config: Any) -> Any: ...  # GeoDataFrame
    def cache_artifact(self, key: str, data: Any, format: str) -> Path: ...
    def load_artifact(self, key: str, format: str) -> Any: ...


class RoadExtractor(Protocol):
    """Road extraction interface (M2 Vision)."""

    def extract(self, image: RasterImage, config: Any) -> RoadMask: ...


class RoadGraphBuilder(Protocol):
    """Graph construction interface (M3 Graph)."""

    def build(self, mask: RoadMask, config: Any) -> RoadGraph: ...


class CriticalityAnalyzer(Protocol):
    """Criticality analysis interface (M4 Analytics)."""

    def analyze(self, road_graph: RoadGraph, config: Any) -> AnalyticsResult: ...


class DisasterSimulator(Protocol):
    """Disaster simulation interface (M5 Simulation)."""

    def simulate(self, road_graph: RoadGraph, scenario: Any) -> SimulationResult: ...


class Router(Protocol):
    """Routing interface (M6 Routing)."""

    def find_route(self, road_graph: RoadGraph, query: Any) -> RouteResult: ...
    def accessibility(self, road_graph: RoadGraph, query: Any) -> Any: ...
