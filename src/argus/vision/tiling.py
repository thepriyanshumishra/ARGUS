"""Tiling utilities for large image inference."""

from __future__ import annotations

from collections.abc import Iterator

import numpy as np

from argus.core.logging import get_logger

log = get_logger(__name__)


def generate_tiles(
    image: np.ndarray,
    tile_size: int,
    overlap: int,
) -> Iterator[tuple[np.ndarray, tuple[int, int], tuple[int, int]]]:
    """Generate tiles with overlap from image.

    Yields:
        (tile, (y, x), (y_end, x_end))
    """
    h, w = image.shape[:2]
    step = tile_size - overlap

    for y in range(0, h, step):
        for x in range(0, w, step):
            y_end = min(y + tile_size, h)
            x_end = min(x + tile_size, w)

            tile = image[y:y_end, x:x_end]
            yield tile, (y, x), (y_end, x_end)


def stitch_predictions(
    predictions: list[tuple[np.ndarray, tuple[int, int]]],
    output_shape: tuple[int, int],
    tile_size: int,
    overlap: int,
) -> np.ndarray:
    """Stitch tile predictions with weighted averaging in overlap regions."""
    h, w = output_shape
    result = np.zeros((h, w), dtype=np.float32)
    weights = np.zeros((h, w), dtype=np.float32)

    # Weight map for blending (cosine window)
    weight_map = _create_weight_map(tile_size, overlap)

    for pred, (y, x) in predictions:
        y_end = min(y + tile_size, h)
        x_end = min(x + tile_size, w)
        pred_h, pred_w = y_end - y, x_end - x

        # Apply weight map
        w_map = weight_map[:pred_h, :pred_w]
        result[y:y_end, x:x_end] += pred[:pred_h, :pred_w] * w_map
        weights[y:y_end, x:x_end] += w_map

    # Normalize
    mask = weights > 0
    result[mask] /= weights[mask]
    return result


def _create_weight_map(tile_size: int, overlap: int) -> np.ndarray:
    """Create cosine weight map for smooth blending."""
    # 1D weight
    if overlap == 0:
        return np.ones((tile_size, tile_size), dtype=np.float32)

    ramp = np.linspace(0, 1, overlap)
    cosine = (1 - np.cos(np.pi * ramp)) / 2  # 0 to 1

    weight_1d = np.ones(tile_size)
    weight_1d[:overlap] = cosine
    weight_1d[-overlap:] = cosine[::-1]

    # 2D weight map
    weight_2d = weight_1d[:, None] * weight_1d[None, :]
    return weight_2d.astype(np.float32)
