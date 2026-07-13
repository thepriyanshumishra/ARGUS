"""Core shared data types for ARGUS."""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Any

import geopandas as gpd
import networkx as nx
import numpy as np
from numpy.typing import NDArray


@dataclass(slots=True)
class RasterImage:
    """Normalized raster image with geospatial metadata.

    Data shape: (H, W) for grayscale, (H, W, C) for RGB (C=3).
    """

    data: NDArray[np.uint8]  # Shape: (H, W) or (H, W, C)
    crs: str  # CRS as WKT or EPSG code (e.g., "EPSG:4326")
    transform: tuple[
        float, float, float, float, float, float
    ]  # Affine transform (a, b, c, d, e, f)
    bounds: tuple[float, float, float, float]  # (left, bottom, right, top)
    metadata: dict[str, Any] = dataclasses.field(default_factory=dict)

    @property
    def height(self) -> int:
        return self.data.shape[0] if self.data.ndim >= 2 else 0

    @property
    def width(self) -> int:
        return self.data.shape[1] if self.data.ndim >= 2 else 0

    @property
    def channels(self) -> int:
        return self.data.shape[2] if self.data.ndim == 3 else 1


@dataclass(slots=True)
class RoadMask:
    """Binary road segmentation mask with metadata."""

    mask: NDArray[np.bool_]  # Shape: (H, W), True = road
    crs: str
    transform: tuple[float, float, float, float, float, float]
    bounds: tuple[float, float, float, float]
    model_name: str
    model_version: str
    metadata: dict[str, Any] = dataclasses.field(default_factory=dict)


@dataclass(slots=True)
class RoadGraph:
    """Validated road network graph with geospatial attributes."""

    graph: nx.MultiDiGraph
    crs: str
    bounds: tuple[float, float, float, float]
    metadata: dict[str, Any] = dataclasses.field(default_factory=dict)

    @property
    def node_count(self) -> int:
        return self.graph.number_of_nodes()

    @property
    def edge_count(self) -> int:
        return self.graph.number_of_edges()

    def to_geodataframe_nodes(self) -> gpd.GeoDataFrame:
        """Export nodes as GeoDataFrame with geometry."""
        nodes = []
        for node_id, data in self.graph.nodes(data=True):
            nodes.append(
                {
                    "id": node_id,
                    "x": data.get("x"),
                    "y": data.get("y"),
                    "lat": data.get("lat"),
                    "lon": data.get("lon"),
                    "degree": data.get("degree", 0),
                }
            )
        gdf = gpd.GeoDataFrame(
            nodes,
            geometry=gpd.points_from_xy([n["x"] for n in nodes], [n["y"] for n in nodes]),
            crs=self.crs,
        )
        return gdf

    def to_geodataframe_edges(self) -> gpd.GeoDataFrame:
        """Export edges as GeoDataFrame with geometry."""
        edges = []
        for u, v, key, data in self.graph.edges(data=True, keys=True):
            edges.append(
                {
                    "u": u,
                    "v": v,
                    "key": key,
                    "length": data.get("length"),
                    "geometry": data.get("geometry"),
                }
            )
        gdf = gpd.GeoDataFrame(edges, geometry="geometry", crs=self.crs)
        return gdf


@dataclass(slots=True)
class AnalyticsResult:
    """Criticality analysis results."""

    annotated_graph: RoadGraph
    report: dict[str, Any]
    summary: dict[str, Any]


@dataclass(slots=True)
class SimulationResult:
    """Disaster simulation results."""

    modified_graph: RoadGraph
    impact_report: dict[str, Any]
    scenario_metadata: dict[str, Any]


@dataclass(slots=True)
class RouteResult:
    """Routing results."""

    routes: list[dict[str, Any]]  # GeoJSON LineStrings with metadata
    accessibility: dict[str, Any]
    comparison: dict[str, Any] | None = None
