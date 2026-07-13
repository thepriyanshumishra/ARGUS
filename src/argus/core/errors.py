"""Custom exceptions for ARGUS."""

from __future__ import annotations


class ArgusError(Exception):
    """Base exception for ARGUS errors."""

    pass


class MissingCRSError(ArgusError):
    """Raised when raster/vector data is missing CRS information."""

    pass


class UnsupportedFormatError(ArgusError):
    """Raised when file format is not supported."""

    pass


class EmptyRasterError(ArgusError):
    """Raised when raster data is empty or invalid."""

    pass


class InvalidMaskError(ArgusError):
    """Raised when road mask is invalid (not binary, wrong shape, etc.)."""

    pass


class DimensionMismatchError(ArgusError):
    """Raised when mask/image dimensions don't match."""

    pass


class MissingGeoMetadataError(ArgusError):
    """Raised when required geospatial metadata is missing."""

    pass


class EmptyGraphError(ArgusError):
    """Raised when graph has no nodes/edges."""

    pass


class MissingCoordinateError(ArgusError):
    """Raised when graph nodes are missing lat/lon coordinates."""

    pass


class MissingEdgeLengthError(ArgusError):
    """Raised when graph edges are missing length attribute."""

    pass


class InvalidScenarioError(ArgusError):
    """Raised when disaster scenario config is invalid."""

    pass
