# Module Map

Detailed specification for every ARGUS module. Implementation tasks follow these specifications.

> This document defines the contract each module must fulfill. It does not prescribe internal implementation.

---

## Module Summary

| ID | Module | Layer | Owner | Priority | Depends On |
|---|---|---|---|---|---|
| M1 | Data Layer | L1 | Shared | P0 | None |
| M2 | Vision Module | L2 | AI / Backend | P1 | M1 |
| M3 | Graph Engine | L3 | Backend | P1 | M2, M1 |
| M4 | Analytics Engine | L4 | Backend | P2 | M3 |
| M5 | Simulation Engine | L5 | Backend | P2 | M3, M4 |
| M6 | Routing Engine | L6 | Backend | P3 | M3, M5 |
| M7 | Dashboard Engine | L7 | Frontend | P3 | M4, M5, M6 |
| M8 | Core Infrastructure | Cross | Shared | P0 | None |

**Priority**: P0 = foundation (must exist first); P1 = core pipeline; P2 = intelligence; P3 = presentation.
**Owner**: AI = model/inference work; Backend = Python/graph/sim/routing logic; Frontend = dashboard/visualization; Shared = infrastructure used by all.

---

## M1 — Data Layer

| Field | Value |
|---|---|
| Purpose | Standardized input loading, format normalization, CRS handling, caching of intermediate artifacts |
| Layer | L1 Data |
| Owner | Shared |
| Priority | P0 |
| Implementation Phase | M0 Foundation |

### Responsibilities

- Load satellite imagery (GeoTIFF, PNG, JPEG) into normalized raster arrays
- Load GIS overlays (GeoJSON, Shapefile) into GeoDataFrames
- Handle CRS (coordinate reference system) conversion and validation
- Cache intermediate artifacts (masks, graphs, results) for fast re-runs
- Provide a unified data access interface for all modules

### Inputs

- File path or URL to imagery/GIS data
- Config specifying target CRS, resolution, cache location

### Outputs

- Normalized raster image (numpy array + geospatial metadata)
- GeoDataFrames for vector overlays
- Cached artifacts in `configs/`-specified paths

### Dependencies

- **Libraries**: Rasterio, GeoPandas, Shapely, NumPy
- **Reusable repos**: OSMnx (for OSM data fetching where needed)
- **Modules**: None (foundation layer)

### Interface Contract

```python
class DataInput(Protocol):
    def load_imagery(self, source: str, config: DataConfig) -> RasterImage: ...
    def load_vector(self, source: str, config: DataConfig) -> GeoDataFrame: ...
    def cache_artifact(self, key: str, data: Any, format: str) -> Path: ...
    def load_artifacts(self, key: str, format: str) -> Any: ...
```

---

## M2 — Vision Module

| Field | Value |
|---|---|
| Purpose | Extract road network segmentation masks from satellite imagery with occlusion robustness |
| Layer | L2 Vision |
| Owner | AI / Backend |
| Priority | P1 |
| Implementation Phase | M2 Vision Pipeline |

### Responsibilities

- Image preprocessing (normalization, tiling for large images, CRS-aware handling)
- Road extraction (semantic segmentation → binary road mask)
- Occlusion recovery (cloud shadow, building occlusion handling via model capabilities)
- Mask post-processing (noise removal, morphological operations, gap filling)
- Model inference (GPU when available, CPU fallback)

### Inputs

- Normalized raster image (from M1)
- Model checkpoint path (from config)
- Inference config (tile size, overlap, device)

### Outputs

- Binary road segmentation mask (numpy array, same spatial dims as input)
- Model metadata (model name, version, confidence scores if available)

### Dependencies

- **Libraries**: PyTorch, OpenCV, NumPy, Rasterio (for geospatial metadata)
- **Reusable repos**: SAM-Road++ (primary model source), D-LinkNet (fallback)
- **Modules**: M1 Data Layer

### Interface Contract

```python
class RoadExtractor(Protocol):
    def extract(self, image: RasterImage, config: VisionConfig) -> RoadMask: ...

class RoadMask:
    mask: np.ndarray       # binary, shape (H, W)
    metadata: dict         # model name, version, crs, transform
```

### Replaceability

Any model producing a `RoadMask` can substitute SAM-Road++. The interface requires only a binary mask + metadata. Downstream modules (Graph Engine) never see the model directly.

### Fallback Path

If SAM-Road++ checkpoint unavailable or GPU insufficient: use D-LinkNet or a lightweight U-Net. The mask contract is identical.

---

## M3 — Graph Engine

| Field | Value |
|---|---|
| Purpose | Convert road segmentation masks into validated, clean, topology-correct road graphs |
| Layer | L3 Graph |
| Owner | Backend |
| Priority | P1 |
| Implementation Phase | M2 Graph Pipeline |

### Responsibilities

- Mask-to-graph conversion (skeletonization → node/edge extraction)
- Graph construction (NetworkX MultiDiGraph with geospatial node positions)
- Topology validation (connectivity checks, dangling nodes, isolated components)
- Graph cleaning (remove artifacts, merge close nodes, snap endpoints)
- Graph simplification (reduce node count while preserving topology)
- Coordinate annotation (attach lat/lon to nodes using raster transform)

### Inputs

- Binary road mask (from M2)
- Raster geospatial metadata (transform, CRS — from M1)
- Graph construction config (simplification tolerance, merge distance)

### Outputs

- Validated road graph (`networkx.MultiDiGraph`)
  - Nodes: `id`, `x`, `y`, `lat`, `lon`, `degree`
  - Edges: `u`, `v`, `length`, `geometry` (LineString)
- Graph metadata (node count, edge count, CRS, bounds)

### Dependencies

- **Libraries**: NetworkX, sknw (skeleton-to-graph), Shapely, SciPy (skeletonize), GeoPandas
- **Reusable repos**: sknw (direct use), CRESI (reference for mask→graph pipeline), Sat2Graph (reference for graph construction patterns)
- **Modules**: M1 Data, M2 Vision

### Interface Contract

```python
class RoadGraphBuilder(Protocol):
    def build(self, mask: RoadMask, config: GraphConfig) -> RoadGraph: ...

class RoadGraph:
    graph: nx.MultiDiGraph
    metadata: dict   # node_count, edge_count, crs, bounds
```

### Replaceability

NetworkX can be swapped for cuGraph (GPU graphs) by changing the internal graph representation. The `RoadGraph` wrapper exposes only the required accessors; downstream modules use the wrapper, not the raw NetworkX object directly where feasible.

---

## M4 — Analytics Engine

| Field | Value |
|---|---|
| Purpose | Compute graph-theoretic criticality metrics to identify critical roads and intersections |
| Layer | L4 Analytics |
| Owner | Backend |
| Priority | P2 |
| Implementation Phase | M4 Criticality |

### Responsibilities

- Centrality computation (betweenness, closeness, degree centrality)
- Structural vulnerability (articulation points, bridges)
- Resilience metrics (network robustness scores, component analysis)
- Criticality ranking (identify top-N critical nodes/edges)
- Per-element metrics annotation (attach scores as graph attributes)

### Inputs

- Validated road graph (from M3)
- Analytics config (which metrics to compute, top-N threshold)

### Outputs

- Annotated graph (input graph + criticality attributes on nodes/edges)
- Criticality report (JSON/CSV with top-N critical elements)
- Summary statistics (network-wide metrics)

### Dependencies

- **Libraries**: NetworkX (algorithms), NumPy, Pandas (report generation)
- **Reusable repos**: OSMnx (reference for centrality on street networks), CRESI (reference for criticality pipeline)
- **Modules**: M3 Graph Engine

### Interface Contract

```python
class CriticalityAnalyzer(Protocol):
    def analyze(self, road_graph: RoadGraph, config: AnalyticsConfig) -> AnalyticsResult: ...

class AnalyticsResult:
    annotated_graph: RoadGraph       # graph with criticality attributes
    report: dict                     # top-N critical nodes/edges + metrics
    summary: dict                    # network-wide statistics
```

---

## M5 — Simulation Engine

| Field | Value |
|---|---|
| Purpose | Simulate disaster scenarios by modifying graph topology and edge weights deterministically |
| Layer | L5 Simulation |
| Owner | Backend |
| Priority | P2 |
| Implementation Phase | M5 Simulation |

### Responsibilities

- Disaster scenario loading (from YAML configs)
- Edge removal (flooded roads, collapsed bridges, blocked segments)
- Edge weight modification (congestion, partial damage, speed reduction)
- Node removal (junction failures, isolated areas)
- Impact estimation (affected area, disconnected population, reroute demand)
- Scenario comparison support (before/after graph pairs)

### Inputs

- Annotated road graph (from M3 or M4)
- Disaster scenario config (YAML: type, affected regions, severity)

### Outputs

- Modified graph (edges/nodes removed or reweighted)
- Impact report (affected nodes, edges, disconnected components, summary)
- Scenario metadata (scenario ID, type, parameters)

### Dependencies

- **Libraries**: NetworkX, Shapely (spatial filtering), GeoPandas
- **Reusable repos**: None needed (pure graph manipulation)
- **Modules**: M3 Graph Engine, M4 Analytics Engine (for pre-annotated graphs)

### Interface Contract

```python
class DisasterSimulator(Protocol):
    def simulate(self, road_graph: RoadGraph, scenario: ScenarioConfig) -> SimulationResult: ...

class SimulationResult:
    modified_graph: RoadGraph
    impact_report: dict
    scenario_metadata: dict
```

### Critical Constraint

Simulation must NEVER invoke the Vision module or any AI model. It is pure graph manipulation driven by scenario configs. This ensures the simulation layer remains deterministic, testable, and AI-independent.

---

## M6 — Routing Engine

| Field | Value |
|---|---|
| Purpose | Compute optimal and alternative routes on the (possibly modified) road graph |
| Layer | L6 Routing |
| Owner | Backend |
| Priority | P3 |
| Implementation Phase | M6 Routing |

### Responsibilities

- Shortest path computation (single source → single target)
- Emergency routing (multiple targets: hospitals, shelters, exits)
- Alternative route computation (K-shortest paths, route diversity)
- Accessibility analysis (which destinations are reachable, unreachable)
- Route comparison (baseline vs. post-disruption routes)
- Reroute recommendation (best alternative when primary route affected)

### Inputs

- Road graph (original or simulation-modified — from M3 or M5)
- Routing query (origin, destination(s), algorithm choice, constraints)

### Outputs

- Route(s) (GeoJSON LineStrings with metadata: length, travel time, nodes traversed)
- Accessibility report (reachable/unreachable destinations)
- Comparison report (if baseline + modified graphs provided)

### Dependencies

- **Libraries**: NetworkX (path algorithms), OSMnx (reference for routing), Shapely, GeoPandas
- **Reusable repos**: OSMnx (routing patterns)
- **Modules**: M3 Graph Engine, M5 Simulation Engine (for modified graphs)

### Interface Contract

```python
class Router(Protocol):
    def find_route(self, road_graph: RoadGraph, query: RouteQuery) -> RouteResult: ...
    def accessibility(self, road_graph: RoadGraph, query: AccessibilityQuery) -> AccessibilityResult: ...
```

### Critical Constraint

Routing operates on the graph — never on segmentation masks or model outputs directly. If the graph does not exist, routing cannot run.

---

## M7 — Dashboard Engine

| Field | Value |
|---|---|
| Purpose | Present analysis, simulation, and routing results in an interactive decision-support UI |
| Layer | L7 Presentation |
| Owner | Frontend |
| Priority | P3 |
| Implementation Phase | M7 Dashboard |

### Responsibilities

- Interactive map display (PyDeck/Leaflet with road network overlay)
- Criticality visualization (heatmap, highlighted critical nodes/edges)
- Simulation scenario controls (select/trigger disaster scenarios)
- Route display (baseline vs. alternative routes, color-coded)
- Accessibility indicators (reachable/unreachable area highlighting)
- Scenario comparison view (side-by-side or before/after)
- Export results (download reports, GeoJSON routes)

### Inputs

- Road graph (from M3)
- Criticality results (from M4)
- Simulation results (from M5)
- Routing results (from M6)
- Dashboard config (UI options, layer toggles)

### Outputs

- Interactive web UI (Streamlit app)
- Exported reports (user-triggered)

### Dependencies

- **Libraries**: Streamlit, PyDeck (or Folium/Leaflet), Pandas, GeoPandas
- **Reusable repos**: None needed (UI layer)
- **Modules**: M3 Graph, M4 Analytics, M5 Simulation, M6 Routing (consumes their outputs)

### Interface Contract

The dashboard does not define a Python protocol (it is the UI terminus). Instead, it consumes standardized result objects from M4, M5, M6. If a FastAPI backend is added for React migration, the API serves these same objects as JSON.

### Critical Constraint

The dashboard must NOT own business logic. All computation (criticality, simulation, routing) happens upstream. The dashboard renders results. If a computation is needed, add it to the appropriate upstream module — never to the dashboard.

---

## M8 — Core Infrastructure

| Field | Value |
|---|---|
| Purpose | Provide shared interfaces, type definitions, config loading, logging, and cross-cutting utilities |
| Layer | Cross-cutting |
| Owner | Shared |
| Priority | P0 |
| Implementation Phase | M0 Foundation |

### Responsibilities

- Define shared protocols/ABCs (`RoadExtractor`, `RoadGraphBuilder`, `CriticalityAnalyzer`, `DisasterSimulator`, `Router`)
- Define shared data types (`RasterImage`, `RoadMask`, `RoadGraph`, `AnalyticsResult`, `SimulationResult`, `RouteResult`)
- Centralized config loading (Hydra/OmegaConf or Pydantic)
- Logging setup (structured, configurable per-module)
- Common constants (CRS defaults, file format defaults)

### Inputs

- Config files (YAML in `configs/`)

### Outputs

- Python package `argus.core` imported by all modules

### Dependencies

- **Libraries**: Pydantic or OmegaConf (config), structlog or loguru (logging), typing_extensions
- **Modules**: None (foundation)

### Interface Contract

Importable by all modules:
```python
from argus.core.types import RasterImage, RoadMask, RoadGraph, ...
from argus.core.protocols import RoadExtractor, RoadGraphBuilder, ...
from argus.core.config import load_config
```

---

## Cross-Reference

| For | See |
|---|---|
| How modules communicate | `docs/integration_points.md` |
| Data lifecycle through modules | `docs/data_flow.md` |
| Implementation order | `docs/implementation_order.md` |
| Technology choices per module | `docs/technology_mapping.md` |
| Folder structure | `docs/repository_map.md` |
| System-level architecture | `docs/system_design.md` |
