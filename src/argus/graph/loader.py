"""Mask loading — load RoadMask from saved files (PNG, NPZ, NPY)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from argus.core.errors import InvalidMaskError
from argus.core.logging import get_logger
from argus.core.types import RoadMask

log = get_logger(__name__)


def load_mask_from_file(
    path: Path | str,
    crs: str = "EPSG:4326",
    transform: tuple[float, float, float, float, float, float] = (
        1.0,
        0.0,
        0.0,
        0.0,
        -1.0,
        0.0,
    ),
    bounds: tuple[float, float, float, float] = (0.0, 0.0, 1.0, 1.0),
    model_name: str = "unknown",
    model_version: str = "0.0",
) -> RoadMask:
    """Load a binary mask from a PNG, NPY, or NPZ file.

    For PNG: white (>=128) pixels = road, else background.
    For NPY/NPZ: any non-zero = road.

    Parameters
    ----------
    path:
        Path to the mask file.
    crs:
        CRS string (should match the original image CRS).
    transform:
        Affine transform tuple (a, b, c, d, e, f).
    bounds:
        Geographic bounds (left, bottom, right, top).
    model_name:
        Name of the model that produced the mask.
    model_version:
        Version of the model.

    Returns
    -------
    RoadMask
        Loaded binary mask with metadata.
    """
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix == ".png":
        img = Image.open(path).convert("L")
        arr = np.array(img)
        mask_arr = arr >= 128
    elif suffix == ".npy":
        arr = np.load(path)
        mask_arr = arr > 0
    elif suffix == ".npz":
        with np.load(path) as npz:
            keys = list(npz.keys())
            if not keys:
                raise InvalidMaskError(f"No arrays in NPZ: {path}")
            arr = npz[keys[0]]
            mask_arr = arr > 0
    else:
        raise InvalidMaskError(f"Unsupported mask format: {suffix}")

    if mask_arr.ndim != 2:
        raise InvalidMaskError(f"Mask must be 2D, got shape {mask_arr.shape}")

    return RoadMask(
        mask=mask_arr.astype(bool),
        crs=crs,
        transform=transform,
        bounds=bounds,
        model_name=model_name,
        model_version=model_version,
    )
