# Data Flow

End-to-end data lifecycle from satellite imagery to decision support. Each stage defines its input, output, transformations, and responsible module.

> This document traces a single data artifact through the entire ARGUS pipeline.

---

## Pipeline Overview

```
Satellite Image
       │
       ▼
  1. Ingest & Preprocess  ──▶ Normalized Raster
       │                         (numpy array + geo metadata)
       ▼
  2. Road Extraction      ──▶ Binary Road Mask
       │                         (H × W numpy array)
       ▼
  3. Graph Generation     ──▶ Raw Road Graph
       │                         (NetworkX MultiDiGraph)
       ▼
  4. Graph Cleaning        ──▶ Validated Road Graph
       │                         (cleaned, simplified graph)
       ▼
  5. Criticality Analysis  ──▶ Annotated Graph + Report
       │                         (graph + criticality attributes)
       ▼
  6. Disaster Simulation  ──▶ Modified Graph + Impact Report
       │                         (edges removed/weighted + impact)
       ▼
  7. Route Computation    ──▶ Routes + Accessibility
       │                         (GeoJSON paths + reachability)
       ▼
  8. Visualization        ──▶ Interactive Dashboard
       │                         (Streamlit UI with layers)
       ▼
  9. Decision Support     ──▶ User Insight
                                 (critical infra, reroutes, impact)
```

---

## Stage 1 — Ingest & Preprocess

| Field | Value |
|---|---|
| Module | M1 Data Layer |
| Input | Satellite imagery file (GeoTIFF, PNG, JPEG) |
| Output | `RasterImage`: normalized numpy array + geospatial metadata (CRS, transform, bounds) |
| Transformations | File load, CRS validation/conversion, band selection (RGB or grayscale), normalization (0-1 or 0-255), optional tiling for large images |
| Dependencies | Rasterio, GeoPandas |
| Interface | `DataInput.load_imagery(source, config) -> RasterImage` |

### Data Contract

```python
@dataclass
class RasterImage:
    array: np.ndarray      # shape (H, W, C) or (H, W)
    crs: str               # e.g. "EPSG:4326"
    transform: Affine     # rasterio transform
    bounds: tuple          # (west, south, east, north)
    metadata: dict         # source file, resolution, etc.
```

### Verification

- Array is non-empty and normalized
- CRS is defined and valid
- Transform maps pixel coords to geographic coords
- Bounds are finite and non-degenerate

---

## Stage 2 — Road Extraction

| Field | Value |
|---|---|
| Module | M2 Vision Module |
| Input | `RasterImage` |
| Output | `RoadMask`: binary numpy array same spatial dimensions as input |
| Transformations | Model preprocessing (resize/normalize for model input), model inference (segmentation), post-processing (threshold, morphology, gap filling, noise removal) |
| Dependencies | PyTorch, OpenCV, SAM-Road++ checkpoint |
| Interface | `RoadExtractor.extract(image, config) -> RoadMask` |

### Data Contract

```python
@dataclass
class RoadMask:
    mask: np.ndarray       # binary, shape (H, W), dtype uint8 (0 or 1)
    metadata: dict         # model_name, model_version, crs, transform, confidence
```

### Verification

- Mask shape matches image array spatial dimensions
- Mask is binary (0 and 1 only)
- Metadata includes model name and CRS
- No silent failure: low-confidence masks produce a warning, not a crash

### Occlusion Handling

The model (SAM-Road++) is selected for its occlusion robustness. If cloud/shadow occludes roads, the model fills gaps. Post-processing further connects broken segments via morphological closing.

---

## Stage 3 — Graph Generation

| Field | Value |
|---|---|
| Module | M3 Graph Engine |
| Input | `RoadMask` |
| Output | `RoadGraph`: raw NetworkX MultiDiGraph with geospatial node positions |
| Transformations | Skeletonization (reduce mask to 1-pixel-wide lines), node detection (intersection/endpoints), edge tracing (connect nodes via sknw), coordinate annotation (pixel → lat/lon via transform) |
| Dependencies | SciPy (skeletonize), sknw, NetworkX, Shapely |
| Interface | `RoadGraphBuilder.build(mask, config) -> RoadGraph` |

### Data Contract

```python
@dataclass
class RoadGraph:
    graph: nx.MultiDiGraph
    metadata: dict     # node_count, edge_count, crs, bounds
```

### Graph Schema

**Nodes**:
- `id`: int (pixel coordinate hash or sequential)
- `x`: float (pixel x)
- `y`: float (pixel y)
- `lat`: float (geographic latitude)
- `lon`: float (geographic longitude)
- `degree`: int (number of connected edges)

**Edges**:
- `u`: int (source node)
- `v`: int (target node)
- `length`: float (geometric length in meters)
- `geometry`: LineString (pixel coords)
- `geometry_geo`: LineString (lat/lon coords)

---

## Stage 4 — Graph Cleaning

| Field | Value |
|---|---|
| Module | M3 Graph Engine |
| Input | Raw `RoadGraph` |
| Output | Validated `RoadGraph` (cleaned, simplified) |
| Transformations | Remove isolated small components, merge near-duplicate nodes (< merge_distance threshold), snap close endpoints, remove self-loops, simplify degree-2 chains (reduce intermediate nodes preserving geometry), validate connectivity |
| Dependencies | NetworkX, Shapely |
| Interface | `RoadGraphBuilder.clean(graph, config) -> RoadGraph` (or part of `build`) |

### Verification

- No self-loops
- No duplicate edges between same (u, v) pair unless geometry differs meaningfully
- All nodes have `lat`/`lon` populated
- Large connected component(s) identified; tiny isolated components flagged
- Node count reduced from raw; topology preserved

---

## Stage 5 — Criticality Analysis

| Field | Value |
|---|---|
| Module | M4 Analytics Engine |
| Input | Validated `RoadGraph` |
| Output | `AnalyticsResult`: annotated graph + criticality report + summary |
| Transformations | Compute betweenness centrality (per-node, per-edge), find articulation points, find bridges, compute closeness centrality, rank top-N critical elements, attach metrics as graph attributes |
| Dependencies | NetworkX, NumPy, Pandas |
| Interface | `CriticalityAnalyzer.analyze(road_graph, config) -> AnalyticsResult` |

### Data Contract

```python
@dataclass
class AnalyticsResult:
    annotated_graph: RoadGraph
    report: dict       # {top_nodes: [...], top_edges: [...], per_node_metrics: {...}}
    summary: dict      # {total_nodes, total_edges, articulation_points, bridges, avg_centrality}
```

### Metrics Computed

| Metric | Scope | Purpose |
|---|---|---|
| Betweenness centrality | Node, Edge | Which intersections/roads are most traversed in shortest paths |
| Closeness centrality | Node | Which nodes have shortest average distance to all others |
| Degree centrality | Node | Which nodes have most connections (major junctions) |
| Articulation points | Node | Nodes whose removal disconnects the graph |
| Bridges | Edge | Edges whose removal disconnects the graph |
| Connected components | Graph | Identify isolated sub-networks |
| Average path length | Graph | Network-wide accessibility |

---

## Stage 6 — Disaster Simulation

| Field | Value |
|---|---|
| Module | M5 Simulation Engine |
| Input | `RoadGraph` (annotated from M4 or clean from M3) + scenario config |
| Output | `SimulationResult`: modified graph + impact report + metadata |
| Transformations | Parse scenario config → identify affected region (geometry or bounding box) → remove edges in affected region or modify their weights → recompute connectivity → generate impact report |
| Dependencies | NetworkX, Shapely (spatial containment) |
| Interface | `DisasterSimulator.simulate(road_graph, scenario) -> SimulationResult` |

### Data Contract

```python
@dataclass
class SimulationResult:
    modified_graph: RoadGraph
    impact_report: dict    # {removed_edges: [...], removed_nodes: [...], affected_area, disconnected_components, reroute_demand}
    scenario_metadata: dict
```

### Scenario Config Schema (YAML)

```yaml
scenario_id: "flood_zone_a"
type: "flood"
affected_region:
  type: "polygon"
  coordinates: [[lon, lat], [lon, lat], ...]
  # OR
  type: "bbox"
  bounds: [west, south, east, north]
action:
  edges: "remove"      # or "weight"
  nodes: "remove"      # or "keep"
  weight_multiplier: 0.0   # only if action.edges == "weight"
severity: 1.0
```

### Critical Constraint

Simulation is pure graph manipulation. It does NOT invoke M2 Vision or any AI model. Scenarios are defined by config, not computed by ML.

---

## Stage 7 — Route Computation

| Field | Value |
|---|---|
| Module | M6 Routing Engine |
| Input | `RoadGraph` (original or `modified_graph` from M5) + routing query |
| Output | `RouteResult`: route(s) + accessibility report |
| Transformations | Shortest path (Dijkstra or A*), K-shortest paths (for alternatives), multi-target accessibility (which destinations reachable), route comparison if baseline+modified graphs provided |
| Dependencies | NetworkX, GeoPandas, Shapely |
| Interface | `Router.find_route(graph, query) -> RouteResult` |

### Data Contract

```python
@dataclass
class RouteResult:
    routes: list[Route]           # ordered by length/weight
    accessibility: dict           # {reachable: [...], unreachable: [...]}
    metadata: dict                # algorithm, computation_time

@dataclass
class Route:
    geometry: LineString          # lat/lon coords
    nodes: list[int]              # graph node IDs traversed
    length: float                # meters
    travel_time: float            # seconds (estimated)
```

### Routing Query Schema

```yaml
origin: [lat, lon]
destinations:
  - [lat, lon]
  - [lat, lon]
algorithm: "dijkstra"   # or "astar", "k_shortest"
k: 3                     # only for k_shortest
```

### Critical Constraint

Routing consumes a graph object — never a segmentation mask or model output. If no graph exists, routing cannot run.

---

## Stage 8 — Visualization

| Field | Value |
|---|---|
| Module | M7 Dashboard Engine |
| Input | `RoadGraph`, `AnalyticsResult`, `SimulationResult`, `RouteResult` |
| Output | Interactive Streamlit web UI |
| Transformations | Convert graph edges to GeoJSON for map overlay, generate criticality heatmap, overlay simulation-affected regions, draw routes as colored LineStrings, build interactive controls |
| Dependencies | Streamlit, PyDeck, GeoPandas, Pandas |
| Interface | Not a Python protocol — consumes result objects directly; renders UI |

### Layers Displayed

| Layer | Source | Visual |
|---|---|---|
| Road network | M3 RoadGraph | Thin grey lines |
| Critical nodes | M4 report | Red circles (size × criticality) |
| Critical edges | M4 report | Red/yellow lines (color × betweenness) |
| Affected region | M5 SimulationResult | Red shaded polygon |
| Removed edges | M5 SimulationResult | Dashed grey (hidden) |
| Baseline route | M6 RouteResult | Blue LineString |
| Alternative route | M6 RouteResult | Green LineString |
| Unreachable area | M6 accessibility | Hatched/red overlay |

### Critical Constraint

Dashboard does not compute. It renders results provided by upstream modules. All business logic lives in M1–M6.

---

## Stage 9 — Decision Support

| Field | Value |
|---|---|
| Module | M7 Dashboard Engine (presentation) + user |
| Input | All upstream results |
| Output | User understanding: critical infrastructure, disaster impact, reroute options |
| Transformations | None (this is the user interpreting the UI) |

This stage is the terminal goal: a decision-maker sees which roads are critical, what happens if a disaster strikes, and how to reroute. No computation occurs here.

---

## Data Flow Summary

```
GeoTIFF
  │
  ▼ RasterImage
  │
  ▼ RoadMask (binary H×W)
  │
  ▼ RoadGraph (NetworkX MultiDiGraph)
  │
  ▼ AnalyticsResult (graph + criticality attrs)
  │
  ▼ SimulationResult (modified graph + impact)
  │
  ▼ RouteResult (GeoJSON routes + accessibility)
  │
  ▼ Interactive Dashboard
  │
  ▼ Decision Support
```

---

## Cross-Reference

| For | See |
|---|---|
| Module specs | `docs/module_map.md` |
| Interface contracts between stages | `docs/integration_points.md` |
| Implementation order | `docs/implementation_order.md` |
| System architecture | `docs/system_design.md` |
