"""Mask post-processing utilities."""

from __future__ import annotations

import cv2
import numpy as np

from argus.core.logging import get_logger

log = get_logger(__name__)


def postprocess_mask(
    mask: np.ndarray,
    min_area: int = 50,
    close_kernel: int = 3,
    open_kernel: int = 3,
) -> np.ndarray:
    """Post-process binary road mask."""
    mask = mask.astype(np.uint8)

    # Morphological closing (fill small gaps)
    if close_kernel > 0:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close_kernel, close_kernel))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    # Morphological opening (remove noise)
    if open_kernel > 0:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (open_kernel, open_kernel))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    # Remove small connected components
    if min_area > 0:
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
        for i in range(1, num_labels):
            if stats[i, cv2.CC_STAT_AREA] < min_area:
                mask[labels == i] = 0

    return mask


def fill_gaps(mask: np.ndarray, max_gap: int = 10) -> np.ndarray:
    """Fill small gaps in roads using morphological dilation."""
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (max_gap, max_gap))
    return cv2.dilate(mask.astype(np.uint8), kernel, iterations=1)


def skeletonize(mask: np.ndarray) -> np.ndarray:
    """Skeletonize binary mask to single-pixel width."""
    from skimage.morphology import skeletonize as sk_skeletonize

    # Ensure binary
    binary = (mask > 0).astype(np.uint8)
    skeleton = sk_skeletonize(binary)
    return skeleton.astype(np.uint8)
