# Integration Points

How every module communicates. Defines the interface contract at each boundary — the data format, ownership, and guarantees each side provides.

> Modules communicate through documented interfaces only. No module directly accesses another module's internals. Violation is an architecture issue.

---

## Integration Overview

```
M1 Data    M2 Vision    M3 Graph    M4 Analytics   M5 Simulation
  │            │            │            │               │
  ▼            ▼            ▼            ▼               ▼
RasterImage ▶ RoadMask ▶ RoadGraph ▶ AnalyticsResult ▶ SimulationResult
                                   │                       │
                                   │                       ▼
                              M6 Routing        M7 Dashboard
                                   │                       │
                                   ▼                       ▼
                             RouteResult ▶ Interactive UI
```

Each arrow is an integration point with a defined contract below.

---

## IP-1: Data → Vision

| Field | Value |
|---|---|
| From | M1 Data Layer |
| To | M2 Vision Module |
| Data | `RasterImage` |
| Direction | Synchronous call |

### Contract

```python
@dataclass
class RasterImage:
    array: np.ndarray      # (H, W, C) or (H, W), normalized
    crs: str                # e.g. "EPSG:4326"
    transform: Affine       # pixel → geographic coords
    bounds: tuple           # (west, south, east, north)
    metadata: dict          # source, resolution, etc.
```

### Guarantees (Producer: M1)

- Array is non-empty, normalized (0–1 or 0–255)
- CRS is a valid EPSG string
- Transform maps every pixel to geographic coordinates
- Bounds are finite and non-degenerate

### Assumptions (Consumer: M2)

- Image is ready for model preprocessing (M2 handles its own resize/normalize)
- CRS/transform are authoritative for mask-to-geo mapping

### Failure Modes

| Failure | Behavior |
|---|---|
| Unsupported format | M1 raises `UnsupportedFormatError` with format detail |
| CRS missing | M1 raises `MissingCRSError`; M2 does not proceed |
| Array empty | M1 raises `EmptyRasterError` |

---

## IP-2: Vision → Graph

| Field | Value |
|---|---|
| From | M2 Vision Module |
| To | M3 Graph Engine |
| Data | `RoadMask` |
| Direction | Synchronous call |

### Contract

```python
@dataclass
class RoadMask:
    mask: np.ndarray       # binary (0 or 1), shape (H, W), uint8
    metadata: dict         # model_name, model_version, crs, transform, confidence
```

### Guarantees (Producer: M2)

- Mask is binary (values 0 and 1 only)
- Mask spatial dimensions match the input `RasterImage` array
- Metadata includes `crs` and `transform` (inherited from input image)
- Metadata includes `model_name` and `model_version`

### Assumptions (Consumer: M3)

- Mask aligns geographically with stated CRS/transform
- 1 = road, 0 = background
- Mask may have noise; M3 handles cleaning

### Failure Modes

| Failure | Behavior |
|---|---|
| Mask not binary | M3 raises `InvalidMaskError` |
| Mask spatial dims mismatch | M3 raises `DimensionMismatchError` |
| Metadata missing CRS | M3 cannot annotate node lat/lon → raises `MissingGeoMetadataError` |

---

## IP-3: Graph → Analytics

| Field | Value |
|---|---|
| From | M3 Graph Engine |
| To | M4 Analytics Engine |
| Data | `RoadGraph` |
| Direction | Synchronous call |

### Contract

```python
@dataclass
class RoadGraph:
    graph: nx.MultiDiGraph
    metadata: dict     # node_count, edge_count, crs, bounds
```

### Graph Schema

**Node attributes** (required):
- `id`: int
- `x`: float (pixel x)
- `y`: float (pixel y)
- `lat`: float (geographic latitude)
- `lon`: float (geographic longitude)
- `degree`: int

**Edge attributes** (required):
- `u`: int (source node)
- `v`: int (target node)
- `length`: float (meters)
- `geometry`: LineString (pixel coords)

### Guarantees (Producer: M3)

- Graph has been cleaned (no self-loops, no duplicate edges, small components removed)
- All nodes have valid `lat`/`lon`
- All edges have `length` and `geometry`
- `metadata` includes `crs` and `bounds`

### Assumptions (Consumer: M4)

- Graph is ready for algorithmic computation
- Edge `length` is in meters (M4 uses this for weighted centrality)
- Multi-edges allowed (parallel roads)

### Failure Modes

| Failure | Behavior |
|---|---|
| Graph empty (no nodes) | M4 raises `EmptyGraphError` |
| Missing lat/lon on nodes | M4 raises `MissingCoordinateError` |
| Missing edge length | M4 raises `MissingEdgeLengthError`; cannot compute weighted metrics |

---

## IP-4: Analytics → Simulation

| Field | Value |
|---|---|
| From | M4 Analytics Engine |
| To | M5 Simulation Engine |
| Data | `AnalyticsResult` (annotated graph) or `RoadGraph` directly |
| Direction | Synchronous call |

### Contract

```python
@dataclass
class AnalyticsResult:
    annotated_graph: RoadGraph       # graph with criticality attributes
    report: dict
    summary: dict
```

### Data on Annotated Graph

**Additional node attributes** (from M4):
- `betweenness`: float
- `closeness`: float
- `degree_centrality`: float
- `is_articulation_point`: bool

**Additional edge attributes** (from M4):
- `betweenness`: float
- `is_bridge`: bool

### Guarantees (Producer: M4)

- Criticality attributes are numeric and finite
- `is_articulation_point` and `is_bridge` are boolean
- Annotated graph preserves original topology (same nodes/edges, only attributes added)

### Assumptions (Consumer: M5)

- M5 can use criticality attributes to prioritize which edges/nodes to report as "most affected"
- M5 can also operate on a bare `RoadGraph` (from M3) without analytics annotations — annotations are optional enrichment

### Failure Modes

| Failure | Behavior |
|---|---|
| Graph not annotatable (no edges) | M4 returns empty report with warning |
| Simulation receives non-annotated graph | M5 proceeds; criticality attributes accessed via `.get()` with defaults |

---

## IP-5: Simulation → Routing

| Field | Value |
|---|---|
| From | M5 Simulation Engine |
| To | M6 Routing Engine |
| Data | `SimulationResult` (modified graph) or `RoadGraph` directly |
| Direction | Synchronous call |

### Contract

```python
@dataclass
class SimulationResult:
    modified_graph: RoadGraph
    impact_report: dict
    scenario_metadata: dict
```

### `impact_report` Schema

```python
{
    "removed_edges": [{"u": int, "v": int, "reason": str}],
    "removed_nodes": [{"id": int, "reason": str}],
    "reweighted_edges": [{"u": int, "v": int, "old_weight": float, "new_weight": float}],
    "affected_area_m2": float,
    "disconnected_components": [{"node_count": int, "centroid": [lat, lon]}],
    "reroute_demand": int     # estimated count of trips needing reroute
}
```

### Guarantees (Producer: M5)

- `modified_graph` is a valid `RoadGraph` (same schema as M3 output)
- Removed edges/nodes are absent from the modified graph (not merely flagged)
- Reweighted edges have updated `length` or a `weight` attribute
- Impact report accurately reflects what was changed

### Assumptions (Consumer: M6)

- Modified graph is a valid routing substrate
- Routing on modified graph avoids removed/affected edges naturally
- M6 may also route on the original graph (from M3) for baseline comparison

### Critical Constraint

M5 must NOT invoke M2 Vision or any AI. Simulation is pure graph manipulation.

### Failure Modes

| Failure | Behavior |
|---|---|
| Scenario config invalid | M5 raises `InvalidScenarioError` with field detail |
| Affected region outside graph bounds | M5 returns empty impact report with warning |
| Modified graph disconnected | M5 proceeds; M6 handles disconnection via accessibility analysis |

---

## IP-6: Routing → Dashboard

| Field | Value |
|---|---|
| From | M6 Routing Engine |
| To | M7 Dashboard Engine |
| Data | `RouteResult` |
| Direction | Synchronous call (dashboard fetches) |

### Contract

```python
@dataclass
class RouteResult:
    routes: list[Route]
    accessibility: dict     # {"reachable": [...], "unreachable": [...]}
    metadata: dict           # algorithm, computation_time

@dataclass
class Route:
    geometry: LineString     # lat/lon coords
    nodes: list[int]         # graph node IDs
    length: float            # meters
    travel_time: float       # seconds
```

### Guarantees (Producer: M6)

- Each route has a valid LineString in lat/lon coordinates
- `length` is in meters
- `accessibility` lists are exhaustive (every queried destination classified)
- Route ordering: primary first, alternatives follow

### Assumptions (Consumer: M7)

- Route geometry is in lat/lon (EPSG:4326) suitable for map overlay
- Dashboard does not re-compute routes — it renders what M6 provides

### Failure Modes

| Failure | Behavior |
|---|---|
| No route found (unreachable) | M6 includes destination in `unreachable` list; routes list empty for that destination |
| Graph disconnected | M6 reports accessibility; does not raise |

---

## IP-7: All Modules → Dashboard

The dashboard consumes outputs from M3, M4, M5, and M6. These are bundled into a session state object.

### Dashboard Session State

```python
@dataclass
class DashboardSession:
    road_graph: RoadGraph              # from M3
    analytics_result: AnalyticsResult  # from M4 (optional until M4 built)
    simulation_result: SimulationResult # from M5 (optional until M5 run)
    route_result: RouteResult          # from M6 (optional until M6 run)
    config: dict                       # UI config, layer toggles
```

### Dashboard Responsibilities

- Render road network as map layer
- Overlay criticality (if analytics_result present)
- Overlay simulation impact (if simulation_result present)
- Overlay routes (if route_result present)
- Respond to user interactions (scenario selection, route query)
- Trigger upstream pipeline stages (or load pre-computed results)

### Critical Constraint

Dashboard does NOT compute. If computation is needed (e.g., running a new simulation), the dashboard invokes the relevant module's interface — it never implements the logic itself.

---

## IP-8: CLI → Modules

The CLI orchestrates module calls for command-line usage. It is a thin orchestrator, not a business logic layer.

### CLI Commands (Summary)

| Command | Modules Invoked | Output |
|---|---|---|
| `argus ingest --source` | M1 | `RasterImage` metadata + thumbnail |
| `argus extract --source` | M1, M2 | `RoadMask` PNG/GeoTIFF |
| `argus build-graph --source` | M1, M2, M3 | `RoadGraph` GraphML + GeoJSON |
| `argus analyze --graph` | M4 | `AnalyticsResult` JSON/CSV |
| `argus simulate --graph --scenario` | M5 | `SimulationResult` modified graph + impact |
| `argus route --graph --origin --dest` | M6 | `RouteResult` GeoJSON |
| `argus dashboard --graph` | M3 + present results | Streamlit web app |
| `argus run --source` | M1 → M2 → M3 → M4 | Full pipeline to analytics |
| `argus run --source --scenario --route` | All | Full end-to-end |

### Constraint

CLI is orchestration only. It instantiates modules, passes outputs, and writes results. No business logic in CLI.

---

## Ownership Matrix

| Interface | Producer (Owner) | Consumer (Owner) | Data Format |
|---|---|---|---|
| IP-1 | M1 Shared | M2 AI/Backend | `RasterImage` (Python object) |
| IP-2 | M2 AI/Backend | M3 Backend | `RoadMask` (Python object) |
| IP-3 | M3 Backend | M4 Backend | `RoadGraph` (NetworkX) |
| IP-4 | M4 Backend | M5 Backend | `AnalyticsResult` |
| IP-5 | M5 Backend | M6 Backend | `SimulationResult` |
| IP-6 | M6 Backend | M7 Frontend | `RouteResult` + GeoJSON |
| IP-7 | M3–M6 Backend | M7 Frontend | `DashboardSession` |
| IP-8 | CLI Shared | All modules | CLI args + file I/O |

---

## Interface Stability Rules

1. **Interface contracts are versioned.** Breaking changes require architecture review.
2. **Producers guarantee output schema.** Consumers may assume it.
3. **Producers fail explicitly.** Invalid inputs raise typed errors, never silent corruption.
4. **Consumers validate defensively.** If a required attribute is missing, raise — don't guess.
5. **No back-channels.** M6 cannot call M2 directly. Data flows forward only.
6. **Optional attributes use `.get()`.** Required attributes use direct access with validation.

---

## Cross-Reference

| For | See |
|---|---|
| Module specs | `docs/module_map.md` |
| Data flow lifecycle | `docs/data_flow.md` |
| Implementation order | `docs/implementation_order.md` |
| System architecture | `docs/system_design.md` |
