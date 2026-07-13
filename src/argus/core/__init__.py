"""ARGUS Core Infrastructure - Shared types, protocols, config, logging."""

from argus.core.config import get_config_path, load_config, merge_configs
from argus.core.logging import get_logger, setup_logging
from argus.core.protocols import (
    CriticalityAnalyzer,
    DataInput,
    DisasterSimulator,
    RoadExtractor,
    RoadGraphBuilder,
    Router,
)
from argus.core.types import (
    AnalyticsResult,
    RasterImage,
    RoadGraph,
    RoadMask,
    RouteResult,
    SimulationResult,
)

__all__ = [
    # Types
    "RasterImage",
    "RoadMask",
    "RoadGraph",
    "AnalyticsResult",
    "SimulationResult",
    "RouteResult",
    # Protocols
    "DataInput",
    "RoadExtractor",
    "RoadGraphBuilder",
    "CriticalityAnalyzer",
    "DisasterSimulator",
    "Router",
    # Config
    "load_config",
    "merge_configs",
    "get_config_path",
    # Logging
    "setup_logging",
    "get_logger",
]
