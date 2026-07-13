"""Simulation Engine — Disaster scenario simulation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import networkx as nx
import yaml
from shapely.geometry import LineString, Point, shape

from argus.core.errors import InvalidScenarioError
from argus.core.logging import get_logger
from argus.core.protocols import DisasterSimulator
from argus.core.types import RoadGraph, SimulationResult

log = get_logger(__name__)

_VALID_TYPES = {"flood", "bridge_collapse", "road_blockage"}


def pixel_to_coords(px_x: float, px_y: float, transform: list[float] | None) -> tuple[float, float]:
    if not transform or len(transform) != 6:
        return px_x, px_y
    a, b, c, d, e, f = transform
    lon = a * px_x + b * px_y + c
    lat = d * px_x + e * px_y + f
    return lon, lat


def get_edge_geom(
    u_data: dict, v_data: dict, edata: dict, transform: list[float] | None
) -> LineString:
    pixels = edata.get("path_pixels", [])
    if len(pixels) >= 2:
        coords = [pixel_to_coords(px, py, transform) for px, py in pixels]
    else:
        u_lon = u_data.get("lon", u_data.get("x", 0.0))
        u_lat = u_data.get("lat", u_data.get("y", 0.0))
        v_lon = v_data.get("lon", v_data.get("x", 0.0))
        v_lat = v_data.get("lat", v_data.get("y", 0.0))
        coords = [(u_lon, u_lat), (v_lon, v_lat)]
    return LineString(coords)


@dataclass(slots=True)
class ScenarioConfig:
    """Disaster scenario configuration."""

    scenario_id: str
    scenario_type: str
    affected_region: dict
    severity: float = 1.0
    parameters: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        """Validate after construction."""
        if not self.scenario_id:
            raise InvalidScenarioError("scenario_id must not be empty")
        if self.scenario_type not in _VALID_TYPES:
            raise InvalidScenarioError(
                f"Unknown scenario_type '{self.scenario_type}'. "
                f"Valid: {', '.join(sorted(_VALID_TYPES))}"
            )
        if not isinstance(self.affected_region, dict):
            raise InvalidScenarioError("affected_region must be a GeoJSON geometry dict")
        region_type = self.affected_region.get("type")
        if region_type not in ("Polygon", "MultiPolygon"):
            raise InvalidScenarioError(
                f"affected_region must be Polygon or MultiPolygon, got '{region_type}'"
            )
        coords = self.affected_region.get("coordinates")
        if coords is None or not (isinstance(coords, (list, tuple))):
            raise InvalidScenarioError("affected_region must have coordinates")
        if not 0 <= self.severity <= 1:
            raise InvalidScenarioError(f"severity must be 0–1, got {self.severity}")

    @classmethod
    def from_yaml(cls, path: Path) -> ScenarioConfig:
        """Load and validate scenario from YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            raise InvalidScenarioError(f"Scenario YAML must be a mapping, got {type(data)}")
        required = {"scenario_id", "scenario_type", "affected_region"}
        missing = required - set(data.keys())
        if missing:
            raise InvalidScenarioError(f"Missing required fields: {', '.join(sorted(missing))}")
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class _SimDelta:
    """Mutable record of what the simulation removed or changed."""

    removed_nodes: list[dict[str, Any]] = field(default_factory=list)
    removed_edges: list[dict[str, Any]] = field(default_factory=list)
    reweighted_edges: list[dict[str, Any]] = field(default_factory=list)


def load_scenario(path: str | Path) -> ScenarioConfig:
    """Load scenario from YAML file."""
    return ScenarioConfig.from_yaml(Path(path))


class DisasterSimulatorImpl(DisasterSimulator):
    """Simulate disaster scenarios on road graphs."""

    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self._blockage_multiplier = float(
            self.config.get("road_blockage", {}).get("weight_multiplier", 1000)
        )

    def simulate(self, road_graph: RoadGraph, scenario: ScenarioConfig | dict) -> SimulationResult:
        """Run disaster simulation on road graph."""
        if isinstance(scenario, dict):
            scenario = ScenarioConfig(**scenario)

        log.info(f"Running scenario: {scenario.scenario_id} ({scenario.scenario_type})")

        modified_graph = road_graph.graph.copy()
        delta = _SimDelta()
        transform = road_graph.metadata.get("transform")

        if scenario.scenario_type == "flood":
            modified_graph = self._apply_flood(modified_graph, scenario, delta, transform)
        elif scenario.scenario_type == "bridge_collapse":
            modified_graph = self._apply_bridge_collapse(modified_graph, scenario, delta, transform)
        elif scenario.scenario_type == "road_blockage":
            modified_graph = self._apply_road_blockage(modified_graph, scenario, delta, transform)

        impact_report = self._compute_impact(road_graph.graph, modified_graph, scenario, delta)

        return SimulationResult(
            modified_graph=RoadGraph(
                graph=modified_graph,
                crs=road_graph.crs,
                bounds=road_graph.bounds,
                metadata=road_graph.metadata,
            ),
            impact_report=impact_report,
            scenario_metadata={
                "scenario_id": scenario.scenario_id,
                "type": scenario.scenario_type,
                "severity": scenario.severity,
            },
        )

    # ------------------------------------------------------------------
    # Scenario applicators
    # ------------------------------------------------------------------

    def _apply_flood(
        self,
        graph: nx.MultiDiGraph,
        scenario: ScenarioConfig,
        delta: _SimDelta,
        transform: list[float] | None = None,
    ) -> nx.MultiDiGraph:
        """Remove nodes and edges within flood polygon."""
        region = shape(scenario.affected_region)

        # 1. Find nodes inside the flood zone
        nodes_to_remove: set[int] = set()
        for node, data in graph.nodes(data=True):
            lat = data.get("lat", data.get("y", 0))
            lon = data.get("lon", data.get("x", 0))
            point = Point(lon, lat)
            if region.intersects(point):
                nodes_to_remove.add(node)

        for node in sorted(nodes_to_remove):
            delta.removed_nodes.append({"id": node, "reason": scenario.scenario_type})

        # 2. Find edges intersecting the flood zone (by endpoints or by geometry)
        edges_to_remove: list[tuple[int, int, int]] = []
        for u, v, k, data in list(graph.edges(data=True, keys=True)):
            if u in nodes_to_remove or v in nodes_to_remove:
                edges_to_remove.append((u, v, k))
                delta.removed_edges.append(
                    {"u": u, "v": v, "key": k, "reason": scenario.scenario_type}
                )
                continue

            u_data = graph.nodes[u]
            v_data = graph.nodes[v]
            edge_geom = get_edge_geom(u_data, v_data, data, transform)
            if region.intersects(edge_geom):
                edges_to_remove.append((u, v, k))
                delta.removed_edges.append({"u": u, "v": v, "key": k, "reason": "flooded_segment"})

        # Remove the edges, then remove the nodes
        for u, v, k in edges_to_remove:
            if graph.has_edge(u, v, k):
                graph.remove_edge(u, v, k)
        graph.remove_nodes_from(nodes_to_remove)

        log.info(f"Flood removed {len(nodes_to_remove)} nodes, {len(edges_to_remove)} edges")
        return graph

    def _apply_bridge_collapse(
        self,
        graph: nx.MultiDiGraph,
        scenario: ScenarioConfig,
        delta: _SimDelta,
        transform: list[float] | None = None,
    ) -> nx.MultiDiGraph:
        """Remove bridge edges within affected region."""
        bridges = [
            (u, v, k, data)
            for u, v, k, data in graph.edges(data=True, keys=True)
            if data.get("is_bridge", False)
        ]

        region = shape(scenario.affected_region)
        removed = 0
        for u, v, k, data in bridges:
            u_data = graph.nodes[u]
            v_data = graph.nodes[v]
            edge_geom = get_edge_geom(u_data, v_data, data, transform)
            if region.intersects(edge_geom):
                graph.remove_edge(u, v, k)
                delta.removed_edges.append(
                    {"u": u, "v": v, "key": k, "reason": scenario.scenario_type}
                )
                removed += 1

        log.info(f"Bridge collapse removed {removed} bridge edges")
        return graph

    def _apply_road_blockage(
        self,
        graph: nx.MultiDiGraph,
        scenario: ScenarioConfig,
        delta: _SimDelta,
        transform: list[float] | None = None,
    ) -> nx.MultiDiGraph:
        """Block roads by increasing edge weights proportionally to severity."""
        region = shape(scenario.affected_region)
        multiplier = self._blockage_multiplier * scenario.severity

        for u, v, k, data in graph.edges(data=True, keys=True):
            u_data = graph.nodes[u]
            v_data = graph.nodes[v]
            edge_geom = get_edge_geom(u_data, v_data, data, transform)

            if region.intersects(edge_geom):
                old = data.get("length", 1.0)
                new = old * multiplier if multiplier > 0 else old * self._blockage_multiplier
                data["length"] = new
                data["blocked"] = True
                delta.reweighted_edges.append(
                    {"u": u, "v": v, "key": k, "old_length": old, "new_length": new}
                )

        log.info(f"Road blockage affected {len(delta.reweighted_edges)} edges")
        return graph

    # ------------------------------------------------------------------
    # Impact computation
    # ------------------------------------------------------------------

    def _compute_impact(
        self,
        original: nx.MultiDiGraph,
        modified: nx.MultiDiGraph,
        scenario: ScenarioConfig,
        delta: _SimDelta,
    ) -> dict[str, Any]:
        """Compute IP-5 compliant impact report."""
        orig_undirected = original.to_undirected()
        mod_undirected = modified.to_undirected()

        orig_components = list(nx.connected_components(orig_undirected))
        mod_components = list(nx.connected_components(mod_undirected))

        orig_largest = max(len(c) for c in orig_components) if orig_components else 0
        mod_largest = max(len(c) for c in mod_components) if mod_components else 0
        new_isolated = max(0, len(mod_components) - len(orig_components))

        region = shape(scenario.affected_region)
        affected_area_m2 = region.area

        disconnected = []
        for comp in mod_components:
            if len(comp) < orig_largest * 0.2:
                lats = [modified.nodes[n].get("lat", 0) for n in comp]
                lons = [modified.nodes[n].get("lon", 0) for n in comp]
                centroids = [
                    float(sum(lats)) / max(len(lats), 1),
                    float(sum(lons)) / max(len(lons), 1),
                ]
                disconnected.append({"node_count": len(comp), "centroid": centroids})

        reroute_demand = orig_largest - mod_largest if mod_largest < orig_largest else 0

        return {
            "removed_edges": delta.removed_edges,
            "removed_nodes": delta.removed_nodes,
            "reweighted_edges": delta.reweighted_edges,
            "affected_area_m2": affected_area_m2,
            "disconnected_components": disconnected,
            "reroute_demand": reroute_demand,
            "original_nodes": original.number_of_nodes(),
            "original_edges": original.number_of_edges(),
            "original_components": len(orig_components),
            "original_largest_component": orig_largest,
            "modified_nodes": modified.number_of_nodes(),
            "modified_edges": modified.number_of_edges(),
            "modified_components": len(mod_components),
            "modified_largest_component": mod_largest,
            "new_isolated_components": new_isolated,
        }
