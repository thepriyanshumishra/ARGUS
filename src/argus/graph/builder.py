"""Graph Engine — Mask to NetworkX graph conversion."""

from __future__ import annotations

from typing import Any

import networkx as nx

from argus.core.config import load_config
from argus.core.errors import InvalidMaskError, MissingGeoMetadataError
from argus.core.logging import get_logger
from argus.core.protocols import RoadGraphBuilder
from argus.core.types import RoadGraph, RoadMask
from argus.graph.cleaning import (
    merge_close_nodes,
    remove_dangling_nodes,
    remove_isolated_small_components,
    snap_endpoints,
)
from argus.graph.skeleton import skeletonize_mask
from argus.graph.trace import skeleton_to_graph

log = get_logger(__name__)


class RoadGraphBuilderImpl(RoadGraphBuilder):
    """Build road graphs from segmentation masks.

    Pipeline:  skeletonize  →  trace  →  clean  →  simplify  →  validate
    """

    def __init__(self, config: dict | None = None):
        self._config = config or {}
        self._parse_config()

    def _parse_config(self) -> None:
        """Extract parameters from config dict."""
        self.skeleton_method = self._config.get("skeletonize", {}).get("method", "scipy") or "scipy"

        cleaning = self._config.get("cleaning", {})
        self.remove_self_loops = cleaning.get("remove_self_loops", True)
        self.remove_small_components = cleaning.get("remove_small_components", True)
        self.min_component_size = cleaning.get("min_component_size", 10)
        self.merge_close_nodes_enabled = cleaning.get("merge_close_nodes", True)
        self.merge_distance = cleaning.get("merge_distance", 5.0)
        self.snap_endpoints_enabled = cleaning.get("snap_endpoints", True)
        self.snap_distance = cleaning.get("snap_distance", 10.0)
        self.remove_dangling_enabled = cleaning.get("remove_dangling", True)
        self.max_dangling_length = cleaning.get("max_dangling_length", 5.0)

        simplification = self._config.get("simplification", {})
        self.simplification_enabled = simplification.get("enabled", True)
        self.simplification_tolerance = simplification.get("tolerance", 2.0)

    def build(self, mask: RoadMask, config: dict | None = None) -> RoadGraph:
        """Convert binary mask to validated road graph.

        Parameters
        ----------
        mask:
            Binary road segmentation mask with geospatial metadata.
        config:
            Optional override config dict.  Merges with the builder's base config.

        Returns
        -------
        RoadGraph
            Cleaned, validated road graph with geographic coordinates.

        Raises
        ------
        InvalidMaskError
            If mask is empty or not binary.
        MissingGeoMetadataError
            If CRS or transform is missing from the mask.
        """
        if config:
            self._config = {**self._config, **config}
            self._parse_config()

        log.info(f"Building graph from mask {mask.mask.shape}")

        # Validate mask
        self._validate_mask(mask)

        # 1. Skeletonize
        skeleton = skeletonize_mask(mask.mask, method=self.skeleton_method)
        log.debug(f"Skeleton pixels: {skeleton.sum()}")

        # 2. Convert skeleton to graph
        graph = skeleton_to_graph(skeleton)
        log.debug(f"Raw graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")

        # 3. Annotate geographic coordinates
        self._annotate_coordinates(graph, mask)

        # 4. Clean graph
        graph = self._clean_graph(graph)
        log.debug(
            f"Cleaned graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges"
        )

        # 5. Simplify degree-2 chains
        if self.simplification_enabled:
            graph = self._simplify_graph(graph)
            log.debug(
                f"Simplified graph: {graph.number_of_nodes()} nodes, "
                f"{graph.number_of_edges()} edges"
            )

        # 6. Validate topology
        graph = self._validate_graph(graph)

        # 7. Attach degree to nodes
        for n in graph.nodes():
            graph.nodes[n]["degree"] = graph.degree(n)

        # 8. Build metadata
        metadata: dict[str, Any] = {
            "node_count": graph.number_of_nodes(),
            "edge_count": graph.number_of_edges(),
            "crs": mask.crs,
            "bounds": self._compute_bounds(graph),
            "transform": mask.transform,
            "skeleton_method": self.skeleton_method,
            "model_name": mask.model_name,
            "model_version": mask.model_version,
        }

        return RoadGraph(
            graph=graph,
            crs=mask.crs,
            bounds=metadata["bounds"],
            metadata=metadata,
        )

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_mask(mask: RoadMask) -> None:
        """Raise on invalid/empty mask."""
        if mask.mask is None or mask.mask.size == 0:
            raise InvalidMaskError("Mask is empty or None")
        if not mask.crs:
            raise MissingGeoMetadataError("Mask is missing CRS")
        if not mask.transform or len(mask.transform) != 6:
            raise MissingGeoMetadataError(
                "Mask is missing a valid affine transform (need 6 elements)"
            )

    # ------------------------------------------------------------------
    # Coordinate annotation
    # ------------------------------------------------------------------

    @staticmethod
    def _annotate_coordinates(graph: nx.MultiDiGraph, mask: RoadMask) -> None:
        """Annotate every node with lat/lon from pixel coordinates using the
        mask's affine transform."""
        a, b, c, d, e, f = mask.transform

        for _, data in graph.nodes(data=True):
            px_x = float(data.get("x", 0))
            px_y = float(data.get("y", 0))

            # Affine forward: (lon, lat) = A * (px_x, px_y) + (c, f)
            lon = a * px_x + b * px_y + c
            lat = d * px_x + e * px_y + f

            data["lat"] = lat
            data["lon"] = lon

    # ------------------------------------------------------------------
    # Cleaning pipeline
    # ------------------------------------------------------------------

    def _clean_graph(self, graph: nx.MultiDiGraph) -> nx.MultiDiGraph:
        """Apply all cleaning operations in order."""

        if self.remove_self_loops:
            self_loops = list(nx.selfloop_edges(graph))
            if self_loops:
                log.debug(f"Removing {len(self_loops)} self-loops")
                graph.remove_edges_from(self_loops)

        if self.remove_small_components:
            graph = remove_isolated_small_components(graph, min_nodes=self.min_component_size)

        if self.merge_close_nodes_enabled:
            graph = merge_close_nodes(graph, merge_distance=self.merge_distance)

        if self.snap_endpoints_enabled:
            graph = snap_endpoints(graph, snap_distance=self.snap_distance)

        if self.remove_dangling_enabled:
            graph = remove_dangling_nodes(graph, max_length=self.max_dangling_length)

        return graph

    # ------------------------------------------------------------------
    # Simplification (degree-2 chain reduction)
    # ------------------------------------------------------------------

    def _simplify_graph(self, graph: nx.MultiDiGraph) -> nx.MultiDiGraph:
        """Remove redundant degree-2 nodes, preserving edge geometry."""
        from argus.graph.cleaning import simplify_chains

        return simplify_chains(graph, tolerance=self.simplification_tolerance)

    # ------------------------------------------------------------------
    # Topology validation
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_graph(graph: nx.MultiDiGraph) -> nx.MultiDiGraph:
        """Final validation and topology checks."""
        isolated = list(nx.isolates(graph))
        if isolated:
            log.warning(f"Removing {len(isolated)} final isolated nodes")
            graph.remove_nodes_from(isolated)

        if graph.number_of_nodes() == 0:
            log.error("Graph has 0 nodes after validation")
        else:
            log.debug(
                f"Validated graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges"
            )

        return graph

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_bounds(graph: nx.MultiDiGraph) -> tuple[float, float, float, float]:
        """Compute geographic bounds (min_lon, min_lat, max_lon, max_lat)."""
        lats = [d.get("lat", 0.0) for _, d in graph.nodes(data=True)]
        lons = [d.get("lon", 0.0) for _, d in graph.nodes(data=True)]
        if lats and lons:
            return (min(lons), min(lats), max(lons), max(lats))
        return (0.0, 0.0, 0.0, 0.0)


def build_graph_from_mask(
    mask: RoadMask,
    config: dict | None = None,
) -> RoadGraph:
    """Convenience function — build a graph from a road mask."""
    if config is None:
        from omegaconf import OmegaConf

        raw = load_config("graph")
        config = OmegaConf.to_container(raw, resolve=True)  # type: ignore[union-attr, call-overload]
    builder = RoadGraphBuilderImpl(config=config)
    return builder.build(mask)
