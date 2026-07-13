"""Configuration loading and schema validation for ARGUS."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Optional

from omegaconf import DictConfig, ListConfig, OmegaConf

CONFIG_DIR = Path(__file__).parent.parent.parent.parent / "configs"


# --- Structured Config Schemas for M0 & M1 Validation ---

@dataclass
class ThumbnailConfig:
    max_size: int = 256
    format: str = "PNG"


@dataclass
class DataConfig:
    cache_dir: str = ".cache/argus"
    target_crs: str = "EPSG:4326"
    supported_formats: List[str] = field(default_factory=lambda: ["tif", "tiff", "png", "jpg", "jpeg"])
    thumbnail: ThumbnailConfig = field(default_factory=ThumbnailConfig)


@dataclass
class ModelConfig:
    type: str = "sam_road"
    path: str = "assets/checkpoints/sam_road_plus_plus.pth"
    fallback_path: str = "assets/checkpoints/dlinknet.pth"


@dataclass
class VisionPostprocessConfig:
    min_area: int = 50
    close_kernel: int = 3
    open_kernel: int = 3
    fill_gaps: int = 10


@dataclass
class VisionConfigSchema:
    model: ModelConfig = field(default_factory=ModelConfig)
    device: str = "auto"
    tile_size: int = 512
    overlap: int = 64
    batch_size: int = 1
    threshold: float = 0.5
    postprocess: VisionPostprocessConfig = field(default_factory=VisionPostprocessConfig)
    allow_random_weights: Optional[bool] = None


@dataclass
class SkeletonizeConfig:
    method: str = "scipy"


@dataclass
class SknwConfig:
    enabled: bool = True
    fallback: bool = True


@dataclass
class GraphCleaningConfig:
    remove_self_loops: bool = True
    remove_small_components: bool = True
    min_component_size: int = 10
    merge_close_nodes: bool = True
    merge_distance: float = 5.0
    snap_endpoints: bool = True
    snap_distance: float = 10.0
    remove_dangling: bool = True
    max_dangling_length: float = 5.0


@dataclass
class GraphSimplificationConfig:
    enabled: bool = True
    tolerance: float = 2.0
    method: str = "douglas_peucker"


@dataclass
class GraphExportConfig:
    default_format: str = "graphml"
    graphml_as_simple: bool = True


@dataclass
class GraphConfigSchema:
    skeletonize: SkeletonizeConfig = field(default_factory=SkeletonizeConfig)
    sknw: SknwConfig = field(default_factory=SknwConfig)
    cleaning: GraphCleaningConfig = field(default_factory=GraphCleaningConfig)
    simplification: GraphSimplificationConfig = field(default_factory=GraphSimplificationConfig)
    export: GraphExportConfig = field(default_factory=GraphExportConfig)


@dataclass
class MetricBetweennessConfig:
    normalized: bool = True
    k: Optional[int] = None


@dataclass
class MetricClosenessConfig:
    normalized: bool = True


@dataclass
class MetricDegreeConfig:
    normalized: bool = True


@dataclass
class AnalyticsReportConfig:
    format: str = "json"
    output_dir: str = "outputs/analytics"


@dataclass
class AnalyticsConfigSchema:
    metrics: List[str] = field(default_factory=lambda: ["betweenness", "closeness", "degree", "articulation", "bridges"])
    betweenness: MetricBetweennessConfig = field(default_factory=MetricBetweennessConfig)
    closeness: MetricClosenessConfig = field(default_factory=MetricClosenessConfig)
    degree: MetricDegreeConfig = field(default_factory=MetricDegreeConfig)
    top_n: int = 10
    report: AnalyticsReportConfig = field(default_factory=AnalyticsReportConfig)


@dataclass
class SimulationFloodConfig:
    default_depth_threshold_m: float = 0.5
    default_velocity_threshold_ms: float = 1.0
    removal_method: str = "contains"


@dataclass
class SimulationBridgeConfig:
    removal_method: str = "edge_tag"


@dataclass
class SimulationBlockageConfig:
    weight_multiplier: float = 1000.0
    default_duration_hours: int = 24


@dataclass
class SimulationImpactConfig:
    compute_disconnected_components: bool = True
    compute_reroute_demand: bool = True
    affected_population_estimation: bool = False


@dataclass
class SimulationConfigSchema:
    default_scenario_dir: str = "configs/scenarios"
    flood: SimulationFloodConfig = field(default_factory=SimulationFloodConfig)
    bridge_collapse: SimulationBridgeConfig = field(default_factory=SimulationBridgeConfig)
    road_blockage: SimulationBlockageConfig = field(default_factory=SimulationBlockageConfig)
    impact: SimulationImpactConfig = field(default_factory=SimulationImpactConfig)


@dataclass
class RouteDijkstraConfig:
    weight: str = "length"


@dataclass
class RouteAStarConfig:
    weight: str = "length"
    heuristic: str = "euclidean"


@dataclass
class RouteKShortestConfig:
    k: int = 3
    max_paths: int = 10


@dataclass
class RouteAccessibilityConfig:
    facility_types: List[str] = field(default_factory=lambda: ["hospital", "shelter", "emergency_exit"])
    max_distance_km: float = 10.0
    speed_kmh: float = 40.0


@dataclass
class RouteOutputConfig:
    formats: List[str] = field(default_factory=lambda: ["geojson", "json"])
    include_elevation: bool = False


@dataclass
class RoutingConfigSchema:
    default_algorithm: str = "dijkstra"
    dijkstra: RouteDijkstraConfig = field(default_factory=RouteDijkstraConfig)
    astar: RouteAStarConfig = field(default_factory=RouteAStarConfig)
    k_shortest: RouteKShortestConfig = field(default_factory=RouteKShortestConfig)
    accessibility: RouteAccessibilityConfig = field(default_factory=RouteAccessibilityConfig)
    output: RouteOutputConfig = field(default_factory=RouteOutputConfig)


SCHEMAS: dict[str, Any] = {
    "data": DataConfig,
    "vision": VisionConfigSchema,
    "graph": GraphConfigSchema,
    "analytics": AnalyticsConfigSchema,
    "simulation": SimulationConfigSchema,
    "routing": RoutingConfigSchema,
}


def load_config(name: str) -> DictConfig | ListConfig:
    """Load a configuration file by name and validate against structured schema."""
    config_path = CONFIG_DIR / f"{name}.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")
    yaml_cfg = OmegaConf.load(config_path)

    if name in SCHEMAS:
        schema = OmegaConf.structured(SCHEMAS[name])
        return OmegaConf.merge(schema, yaml_cfg)  # Merges and type validates

    return yaml_cfg


def merge_configs(base: DictConfig, overrides: dict[str, Any]) -> DictConfig | ListConfig:
    """Merge override dict into base config."""
    return OmegaConf.merge(base, OmegaConf.create(overrides))


def get_config_path(name: str) -> Path:
    """Get absolute path to a config file."""
    return CONFIG_DIR / f"{name}.yaml"
