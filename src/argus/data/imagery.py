"""Raster imagery loading with Rasterio."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio
from rasterio.crs import CRS

from argus.core.logging import get_logger
from argus.core.types import RasterImage
from argus.data.preprocessing import normalize_image, reproject_image

log = get_logger(__name__)


@dataclass(slots=True)
class RasterImageLoader:
    """Loads and normalizes raster imagery."""

    target_crs: CRS = CRS.from_epsg(4326)
    band_indices: list[int] | None = None
    normalize_method: str | None = "percentile"

    def load(self, path: str | Path) -> RasterImage:
        """Load a raster image and return a normalized RasterImage."""
        path = Path(path)
        log.info(f"Loading raster: {path}")

        with rasterio.open(path) as src:
            transform = src.transform
            crs = src.crs
            bounds = src.bounds
            nodata = src.nodata
            num_bands = src.count

            # Determine band indices (1-indexed for rasterio)
            if self.band_indices:
                indices = self.band_indices
            elif num_bands >= 3:
                indices = [1, 2, 3]
            else:
                indices = [1]

            # Read selected bands (shape: (len(indices), H, W))
            data = src.read(indices)

            # Transpose to (H, W, C) for multi-band or (H, W) for single band
            if data.shape[0] >= 3:
                img_data = data[:3].transpose(1, 2, 0)
            else:
                img_data = data[0]

            # Normalize values to standard [0, 255] range as np.uint8
            if self.normalize_method:
                if img_data.ndim == 3:
                    normalized = np.zeros_like(img_data, dtype=np.float32)
                    for c in range(img_data.shape[2]):
                        normalized[:, :, c] = normalize_image(
                            img_data[:, :, c], method=self.normalize_method
                        )
                else:
                    normalized = normalize_image(img_data, method=self.normalize_method)
                uint8_data = (normalized * 255.0).astype(np.uint8)
            else:
                if img_data.dtype != np.uint8:
                    # Fallback to simple min-max scaling to uint8 if no method but not uint8
                    normalized = normalize_image(img_data, method="minmax")
                    uint8_data = (normalized * 255.0).astype(np.uint8)
                else:
                    uint8_data = img_data

            return RasterImage(
                data=uint8_data,
                transform=transform.to_gdal(),
                crs=str(crs) if crs else "EPSG:4326",
                bounds=bounds,
                metadata={
                    "source": str(path),
                    "bands": num_bands,
                    "nodata": nodata,
                    "loaded_bands": indices,
                },
            )

    def load_and_reproject(self, path: str | Path) -> RasterImage:
        """Load and reproject to target CRS if needed."""
        img = self.load(path)
        if img.crs != str(self.target_crs):
            log.info(f"Reprojecting from {img.crs} to {self.target_crs}")
            img = reproject_image(img, self.target_crs)
        return img


def load_raster_image(
    path: str | Path,
    target_crs: CRS | None = None,
    band_indices: list[int] | None = None,
    normalize_method: str | None = "percentile",
) -> RasterImage:
    """Convenience function to load a raster image."""
    loader = RasterImageLoader(
        target_crs=target_crs or CRS.from_epsg(4326),
        band_indices=band_indices,
        normalize_method=normalize_method,
    )
    return loader.load(path)
