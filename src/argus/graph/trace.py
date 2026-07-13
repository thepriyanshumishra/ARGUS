"""Skeleton-to-graph conversion.

Converts a 1-pixel-wide binary skeleton into a NetworkX graph where:
  - Nodes = skeleton junction points (degree >= 3) and endpoints (degree == 1)
  - Edges = traced pixel paths between nodes, with geometry LineString

If the optional ``sknw`` package is available it is used directly.
Otherwise a custom tracer handles the conversion.
"""

from __future__ import annotations

import networkx as nx
import numpy as np
from numpy.typing import NDArray

from argus.core.logging import get_logger

log = get_logger(__name__)

_NEIGHBOURS = [
    (-1, -1),
    (-1, 0),
    (-1, 1),
    (0, -1),
    (0, 1),
    (1, -1),
    (1, 0),
    (1, 1),
]


def _count_neighbours(skeleton: NDArray[np.bool_]) -> NDArray[np.int32]:
    """Return an array where each True pixel is marked with its 8-neighbour count."""
    h, w = skeleton.shape
    skel_int = skeleton.astype(np.int32)
    count = np.zeros_like(skeleton, dtype=np.int32)
    for dy, dx in _NEIGHBOURS:
        shifted = np.zeros((h, w), dtype=np.int32)
        sy0 = max(0, -dy)
        sy1 = min(h, h - dy)
        sx0 = max(0, -dx)
        sx1 = min(w, w - dx)
        ty0 = max(0, dy)
        ty1 = min(h, h + dy)
        tx0 = max(0, dx)
        tx1 = min(w, w + dx)
        shifted[ty0:ty1, tx0:tx1] = skel_int[sy0:sy1, sx0:sx1]
        count += shifted * skel_int
    return count


def _trace_path(
    skeleton: NDArray[np.bool_],
    start: tuple[int, int],
    prev: tuple[int, int],
    visited: NDArray[np.bool_],
    is_node: NDArray[np.bool_],
    h: int,
    w: int,
) -> list[tuple[float, float]] | None:
    """Trace a single path from *start* (coming from *prev*) until hitting a node.

    Returns the path (list of (x, y) pixel coords including start but excluding
    the final node pixel), or None if no valid path was found.
    """
    path: list[tuple[float, float]] = []
    cy, cx = start
    py, px = prev

    while True:
        next_pixel: tuple[int, int] | None = None
        for dy, dx in _NEIGHBOURS:
            n_y, n_x = cy + dy, cx + dx
            if 0 <= n_y < h and 0 <= n_x < w and skeleton[n_y, n_x]:
                if n_y == py and n_x == px:
                    continue
                if is_node[n_y, n_x]:
                    # Arrived at target node
                    path.append((float(n_x), float(n_y)))
                    return path if len(path) > 1 else None
                if not visited[n_y, n_x]:
                    next_pixel = (n_y, n_x)
                    break

        if next_pixel is None:
            return path if len(path) > 1 else None

        n_y, n_x = next_pixel
        visited[n_y, n_x] = True
        path.append((float(n_x), float(n_y)))

        if is_node[n_y, n_x]:
            return path if len(path) > 1 else None

        py, px = cy, cx
        cy, cx = n_y, n_x


def skeleton_to_graph_custom(
    skeleton: NDArray[np.bool_],
) -> nx.MultiDiGraph:
    """Build a NetworkX graph from a skeleton using a custom tracer.

    Nodes = junction points + endpoints.  Edges = traced pixel paths.
    """
    h, w = skeleton.shape

    neighbour_count = _count_neighbours(skeleton)
    is_node = (neighbour_count == 1) | (neighbour_count >= 3)
    is_node |= (neighbour_count == 0) & skeleton

    node_coords = np.argwhere(is_node)
    if len(node_coords) == 0:
        log.debug("No junction/endpoint pixels in skeleton")
        return nx.MultiDiGraph()

    node_id_map: dict[tuple[int, int], int] = {}
    for i, (y, x) in enumerate(node_coords):
        node_id_map[(int(y), int(x))] = i

    graph = nx.MultiDiGraph()
    for i, (y, x) in enumerate(node_coords):
        graph.add_node(i, x=float(x), y=float(y))

    visited = np.zeros_like(skeleton, dtype=bool)
    for y, x in node_coords:
        visited[int(y), int(x)] = True

    for i, (y, x) in enumerate(node_coords):
        cy, cx = int(y), int(x)
        for dy, dx in _NEIGHBOURS:
            n_y, n_x = cy + dy, cx + dx
            if 0 <= n_y < h and 0 <= n_x < w and skeleton[n_y, n_x]:
                if is_node[n_y, n_x]:
                    # Direct node-to-node connection (single-pixel edge)
                    target_key = (n_y, n_x)
                    if target_key in node_id_map:
                        target = node_id_map[target_key]
                        if not graph.has_edge(i, target) and not graph.has_edge(target, i):
                            graph.add_edge(
                                i,
                                target,
                                key=0,
                                path_pixels=[(float(cx), float(cy)), (float(n_x), float(n_y))],
                                length_px=1.0,
                            )
                    continue
                if visited[n_y, n_x]:
                    continue
                visited[n_y, n_x] = True
                path = _trace_path(skeleton, (n_y, n_x), (cy, cx), visited, is_node, h, w)
                if path is None or len(path) == 0:
                    continue
                end_x, end_y = path[-1]
                end_key = (int(end_y), int(end_x))
                if end_key in node_id_map:
                    target = node_id_map[end_key]
                    full_path = [(float(cx), float(cy))] + path
                    graph.add_edge(
                        i,
                        target,
                        key=0,
                        path_pixels=full_path,
                        length_px=float(len(full_path) - 1),
                    )

    remaining = skeleton & ~visited
    if remaining.any():
        log.debug(f"Cycle detection: {remaining.sum()} unvisited skeleton pixels")
        first_node_id = len(node_id_map)
        for sy, sx in np.argwhere(remaining):
            sy, sx = int(sy), int(sx)
            if visited[sy, sx]:
                continue
            visited[sy, sx] = True
            new_id = first_node_id
            first_node_id += 1
            graph.add_node(new_id, x=float(sx), y=float(sy))
            path = _trace_path(skeleton, (sy, sx), (sy, sx), visited, is_node, h, w)
            if path is None or len(path) == 0:
                continue
            end_x, end_y = path[-1]
            end_key = (int(end_y), int(end_x))
            if end_key in node_id_map:
                target = node_id_map[end_key]
                full_path = [(float(sx), float(sy))] + path
                graph.add_edge(
                    new_id, target, key=0, path_pixels=full_path, length_px=float(len(full_path))
                )

    return graph


def skeleton_to_graph(skeleton: NDArray[np.bool_]) -> nx.MultiDiGraph:
    """Convert a skeletonized mask to a NetworkX MultiDiGraph.

    Tries ``sknw`` first, falls back to a custom tracer.
    """
    try:
        import sknw  # pyright: ignore[reportMissingImports]

        log.debug("Using sknw for skeleton-to-graph conversion")
        sknw_graph = sknw.build_sknw(skeleton.astype(np.uint8))
        return nx.MultiDiGraph(sknw_graph)
    except ImportError:
        log.debug("sknw not available, using custom tracer")
        return skeleton_to_graph_custom(skeleton)
