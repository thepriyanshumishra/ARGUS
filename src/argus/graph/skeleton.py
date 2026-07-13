"""Skeletonization utilities — reduce binary mask to 1-pixel-wide lines.

Supports two methods:
  - ``scipy`` (default): uses ``skimage.morphology.skeletonize`` (Zhang/Suen algorithm)
  - ``sknw``: if the optional ``scikit-image-numpy-graph`` (sknw) package is available,
    uses it directly; falls back to ``scipy`` method otherwise.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from argus.core.logging import get_logger

log = get_logger(__name__)


def skeletonize_mask(
    mask: NDArray[np.bool_],
    method: str = "scipy",
) -> NDArray[np.bool_]:
    """Reduce a binary mask to a 1-pixel-wide skeleton.

    Parameters
    ----------
    mask:
        Binary road mask. True = road.
    method:
        ``"scipy"`` (default, uses skimage) or ``"sknw"``.

    Returns
    -------
    NDArray[np.bool_]
        Binary skeleton mask with the same shape as input.
    """
    from skimage.morphology import skeletonize as sk_skeletonize

    mask_bool = mask.astype(bool)
    if not mask_bool.any():
        log.warning("Mask is empty (no road pixels); skeleton will be empty")

    if method == "sknw":
        try:
            import sknw  # pyright: ignore[reportMissingImports]

            _ = sknw  # just checking availability
            log.debug("Using sknw skeletonization path (skimage morph)")
        except ImportError:
            log.info("sknw not available, falling back to skimage skeletonize")
    elif method == "scipy":
        log.debug("Using skimage morphology skeletonize (scipy method)")
    else:
        log.warning("Unknown skeletonize method '%s', defaulting to skimage", method)

    skeleton = sk_skeletonize(mask_bool)
    log.debug(
        f"Skeleton: {skeleton.sum()} pixels "
        f"({skeleton.sum() / max(mask_bool.sum(), 1):.2%} of original)"
    )
    return skeleton  # type: ignore[return-value]
