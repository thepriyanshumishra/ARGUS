"""Preprocessing utilities for CRS conversion and normalization."""

from __future__ import annotations

import numpy as np
from rasterio.crs import CRS
from rasterio.transform import Affine
from rasterio.warp import Resampling, calculate_default_transform, reproject

from argus.core.logging import get_logger
from argus.core.types import RasterImage

log = get_logger(__name__)


def reproject_image(
    image: RasterImage, target_crs: CRS, target_resolution: float | None = None
) -> RasterImage:
    """Reproject a raster image to target CRS."""
    if image.crs == target_crs:
        return image

    log.info(f"Reprojecting from {image.crs} to {target_crs}")

    # Convert image.crs string to CRS object
    src_crs = CRS.from_string(image.crs) if isinstance(image.crs, str) else image.crs

    # Calculate output transform, width, height
    transform = Affine(*image.transform)
    kwargs = {}
    if target_resolution is not None:
        kwargs["resolution"] = target_resolution
    dst_transform, dst_width, dst_height = calculate_default_transform(
        src_crs,
        target_crs,
        image.width,
        image.height,
        *image.bounds,
        **kwargs,
    )
    assert dst_width is not None and dst_height is not None
    dst_width = int(dst_width)
    dst_height = int(dst_height)

    # Prepare output array
    if image.data.ndim == 3:
        # Output format: (H, W, C) for consistency with RasterImage
        dst_data = np.zeros((dst_height, dst_width, image.channels), dtype=image.data.dtype)
    else:
        dst_data = np.zeros((dst_height, dst_width), dtype=image.data.dtype)

    # Reproject each band
    for i in range(image.channels):
        if image.data.ndim == 3:
            src_band = image.data[:, :, i]
        else:
            src_band = image.data

        reproject(
            source=src_band,
            destination=dst_data[:, :, i] if image.data.ndim == 3 else dst_data,
            src_transform=transform,
            src_crs=src_crs,
            dst_transform=dst_transform,
            dst_crs=target_crs,
            resampling=Resampling.bilinear,
        )

    # Calculate new bounds
    dst_bounds = (
        dst_transform.c,
        dst_transform.f + dst_transform.e * dst_height,
        dst_transform.c + dst_transform.a * dst_width,
        dst_transform.f,
    )

    return RasterImage(
        data=dst_data,
        crs=str(target_crs),
        transform=dst_transform.to_gdal(),
        bounds=dst_bounds,
        metadata={**image.metadata, "reprojected_from": str(src_crs)},
    )


def normalize_image(data: np.ndarray, method: str = "minmax", percentiles: tuple[float, float] = (2.0, 98.0)) -> np.ndarray:
    """Normalize image data to [0, 1] range."""
    if method == "minmax":
        min_val = data.min()
        max_val = data.max()
        if max_val > min_val:
            return (data - min_val) / (max_val - min_val)
        return np.zeros_like(data, dtype=np.float32)
    elif method == "percentile":
        low = np.percentile(data, percentiles[0])
        high = np.percentile(data, percentiles[1])
        if high > low:
            clipped = np.clip(data, low, high)
            return (clipped - low) / (high - low)
        return np.zeros_like(data, dtype=np.float32)
    elif method == "standardize":
        mean = data.mean()
        std = data.std()
        if std > 0:
            return (data - mean) / std
        return np.zeros_like(data, dtype=np.float32)
    else:
        raise ValueError(f"Unknown normalization method: {method}")


def estimate_utm_crs(bounds: tuple[float, float, float, float], src_crs: str = "EPSG:4326") -> CRS:
    """Estimate the best UTM CRS for a given bounding box centroid."""
    from pyproj.aoi import AreaOfInterest
    from pyproj.database import query_utm_crs_info

    # If bounds is in projected CRS, convert to EPSG:4326 first to find lat/lon centroid
    if src_crs != "EPSG:4326":
        from pyproj import Transformer
        transformer = Transformer.from_crs(src_crs, "EPSG:4326", always_xy=True)
        lon1, lat1 = transformer.transform(bounds[0], bounds[1])
        lon2, lat2 = transformer.transform(bounds[2], bounds[3])
        left, bottom, right, top = min(lon1, lon2), min(lat1, lat2), max(lon1, lon2), max(lat1, lat2)
    else:
        left, bottom, right, top = bounds

    # Centroid
    lon = (left + right) / 2
    lat = (bottom + top) / 2

    # Query best UTM zone using pyproj
    utm_crs_list = query_utm_crs_info(
        datum_name="WGS 84",
        area_of_interest=AreaOfInterest(lon, lat, lon, lat),
    )
    if utm_crs_list:
        return CRS.from_epsg(int(utm_crs_list[0].code))

    # Fallback to standard UTM calculations
    zone = int((lon + 180) / 6) + 1
    hemisphere = 32600 if lat >= 0 else 32700
    return CRS.from_epsg(hemisphere + zone)


def create_thumbnail(image: RasterImage, max_size: int = 256) -> np.ndarray:
    """Create a thumbnail for quick preview."""
    from PIL import Image

    h, w = image.data.shape[:2]
    scale = min(max_size / w, max_size / h)
    new_w, new_h = int(w * scale), int(h * scale)

    if image.data.ndim == 3:
        pil_img = Image.fromarray(image.data)
    else:
        pil_img = Image.fromarray(image.data, mode="L")

    pil_img = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    return np.array(pil_img) / 255.0
