# Implementation Order

Recommended implementation roadmap. Each milestone produces a working, demonstrable system. Ordering maximizes incremental progress while minimizing integration risk.

> This document is the build plan. Every milestone must end with a working slice of the system, not just incomplete components.

---

## Design Principles

1. **Every milestone produces a demo.** No milestone ends with "we built components but nothing runs."
2. **Build the spine first, then add intelligence.** Data flows through all stages before any stage is optimized.
3. **Front-load shared infrastructure.** Config, logging, interfaces, and types must exist before any module ships.
4. **Integrate continuously.** Each milestone wires new output into the dashboard, even if only basic.
5. **Lowest risk first.** Criticality (analytical) before Simulation (stateful) before Routing (query-driven) before Dashboard (UI polish).

---

## Milestone Timeline

```
M0 ──▶ M1 ──▶ M2 ──▶ M3 ──▶ M4 ──▶ M5 ──▶ M6 ──▶ M7
Found.  Data   Vision  Graph  Crit.  Simul.  Route   Dash
                │       │               (end-to-end demo from M3 onward)
```

| Milestone | Name | Duration (est.) | Working Output |
|---|---|---|---|
| M0 | Foundation & Repo Setup | 2–3 days | Project skeleton, configs, CI, one-pass CLI |
| M1 | Data Layer | 1–2 days | CLI loads any GeoTIFF/PNG, prints metadata |
| M2 | Vision Pipeline | 3–4 days | CLI outputs road mask from satellite image |
| M3 | Graph Pipeline | 2–3 days | CLI outputs road graph (GraphML) + basic map preview |
| M4 | Criticality Analytics | 2–3 days | Dashboard shows road network + critical nodes highlighted |
| M5 | Simulation Engine | 2–3 days | Dashboard shows disaster impact on network |
| M6 | Routing Engine | 2–3 days | Dashboard shows baseline vs. alternative routes |
| M7 | Dashboard Polish & Demo | 3–4 days | Full end-to-end demo: image → criticality → sim → reroute |

**Total estimated effort**: 17–25 days for a small undergraduate team.

---

## M0 — Foundation & Repo Setup

| Field | Value |
|---|---|
| Goal | Establish project skeleton, tooling, CI, and shared core package |
| Modules | M8 Core Infrastructure, skeleton for M1–M7 |
| Input | None (greenfield) |
| Output | Runnable Python package with importable `argus`, configured linter/formatter/typechecker, passing CI |
| Demo | `argus --info` prints module versions and config path |

### Tasks

- [ ] Create `pyproject.toml` (Python 3.11+, dependencies, dev deps)
- [ ] Configure Ruff (lint + format), Pyright (typecheck), pytest
- [ ] Configure pre-commit hooks
- [ ] Create `src/argus/` package with `__init__.py`
- [ ] Create subpackages: `argus.core`, `argus.data`, `argus.vision`, `argus.graph`, `argus.analytics`, `argus.simulation`, `argus.routing`, `argus.dashboard`
- [ ] Define core types (`RasterImage`, `RoadMask`, `RoadGraph`, `RoadGraphBuilder`, `AnalyticsResult`, `SimulationResult`, `RouteResult`) in `argus.core.types`
- [ ] Define protocols (`RoadExtractor`, `RoadGraphBuilder`, `CriticalityAnalyzer`, `DisasterSimulator`, `Router`) in `argus.core.protocols`
- [ ] Configure logging (structlog or loguru) in `argus.core.logging`
- [ ] Create `argus.core.config` with config loading (OmegaConf or Pydantic)
- [ ] Create `configs/` with default YAMLs per module
- [ ] Create CLI skeleton (`argus.cli`) with Click/Typer
- [ ] Set up `.github/workflows/` CI (ruff, pyright, pytest on push/PR)
- [ ] Create `tests/` mirroring `src/argus/` with smoke test (import succeeds)
- [ ] Update `docs/repository_map.md` if folder structure evolves

### Acceptance Criteria

- `pip install -e .` succeeds
- `ruff check src/` passes
- `pyright src/` passes
- `pytest tests/` passes (smoke test)
- `argus --info` prints project info
- CI runs on push

### Blocked By

Nothing (starting point).

### Blocks

All subsequent milestones.

---

## M1 — Data Layer

| Field | Value |
|---|---|
| Goal | Load satellite imagery and GIS overlays into normalized internal types |
| Module | M1 Data Layer |
| Input | File paths (GeoTIFF, PNG, JPEG, GeoJSON, Shapefile) |
| Output | `RasterImage` and GeoDataFrame ready for Vision module |
| Demo | `argus ingest --source <path> --output <preview>` prints metadata and saves a thumbnail |

### Tasks

- [ ] Implement `RasterImage` builder (load via Rasterio, normalize, attach CRS/transform/bounds)
- [ ] Implement vector loader (GeoJSON/Shapefile via GeoPandas)
- [ ] Implement CRS validation and conversion (standardize to EPSG:4326 for output)
- [ ] Implement image preview/thumbnail generation (for CLI demo)
- [ ] Implement artifact caching (save/load intermediate results to `configs/cache_dir`)
- [ ] Create `configs/data.yaml` (default CRS, cache settings, supported formats)
- [ ] Write unit tests: load GeoTIFF, load PNG, CRS conversion, caching round-trip
- [ ] Wire CLI `ingest` command

### Acceptance Criteria

- Any GeoTIFF in `assets/` loads and round-trips (load → cache → reload → equal)
- CRS conversion works for common input CRSs
- Unit tests pass
- CLI demo works

### Blocked By

M0

### Blocks

M2

---

## M2 — Vision Pipeline

| Field | Value |
|---|---|
| Goal | Extract binary road segmentation mask from satellite imagery |
| Module | M2 Vision Module |
| Input | `RasterImage` |
| Output | `RoadMask` (saved as GeoTIFF or PNG) |
| Demo | `argus extract --source <image> --output <mask.png>` produces a visible road mask |

### Tasks

- [ ] Download SAM-Road++ pretrained checkpoint (script in `scripts/`)
- [ ] Implement `RoadExtractor` for SAM-Road++ (preprocessing, inference, postprocessing)
- [ ] Implement CPU fallback path (if no GPU, use smaller model or CPU inference)
- [ ] Implement mask post-processing: threshold, morphological closing, noise removal
- [ ] Implement tiling for large images (split → infer → stitch)
- [ ] Implement confidence map generation (if model supports)
- [ ] Create `configs/vision.yaml` (model path, device, tile size, overlap, threshold)
- [ ] Write unit tests: small synthetic image → mask shape correct, binary, metadata correct
- [ ] Write integration test: known image → known mask (or visual comparison)
- [ ] Wire CLI `extract` command

### Acceptance Criteria

- Road mask is binary, same spatial dims as input
- Mask visually corresponds to roads (sanity check on sample image)
- CPU path works (slower but functional)
- Large image tiling produces correct stitched mask
- Unit + integration tests pass

### Blocked By

M1

### Blocks

M3

---

## M3 — Graph Pipeline

| Field | Value |
|---|---|
| Goal | Convert road mask into validated, cleaned, simplified road graph |
| Module | M3 Graph Engine |
| Input | `RoadMask` |
| Output | `RoadGraph` (exported as GraphML + GeoJSON) |
| Demo | `argus build-graph --source <mask> --output <graph.graphml>` then `argus preview --graph <graph.graphml>` renders a basic map |

### Tasks

- [ ] Implement skeletonization (scipy.ndimage.skeletonize)
- [ ] Implement mask-to-graph conversion (sknw)
- [ ] Implement node annotation (pixel → lat/lon via raster transform)
- [ ] Implement graph cleaning (remove small components, merge near nodes, snap endpoints, remove self-loops)
- [ ] Implement graph simplification (reduce degree-2 chains)
- [ ] Implement graph validation (connectivity check, dangling node detection)
- [ ] Implement GraphML + GeoJSON export
- [ ] Implement basic graph statistics (node count, edge count, connected components)
- [ ] Create `configs/graph.yaml` (simplification tolerance, merge distance, min component size)
- [ ] Write unit tests: synthetic mask → known graph topology
- [ ] Write integration test: real mask → graph validity checks
- [ ] Wire CLI `build-graph` and `preview` commands

### Acceptance Criteria

- Graph has nodes with lat/lon attributes
- No self-loops or duplicate edges
- Large connected component dominates; isolated components flagged
- GraphML export is valid and reloadable
- Basic map preview renders (Folium or matplotlib)
- Tests pass

### Blocked By

M2

### Blocks

M4, M5, M6

---

## M4 — Criticality Analytics

| Field | Value |
|---|---|
| Goal | Compute criticality metrics and produce first end-to-end dashboard demo |
| Module | M4 Analytics Engine + initial M7 Dashboard |
| Input | `RoadGraph` |
| Output | `AnalyticsResult` (annotated graph + report) + interactive map showing critical nodes |
| Demo | `argus dashboard --graph <graph> --metrics <output>` opens a map with critical nodes highlighted |

### Tasks

- [ ] Implement betweenness centrality (nodes + edges)
- [ ] Implement closeness centrality
- [ ] Implement degree centrality
- [ ] Implement articulation points detection
- [ ] Implement bridges detection
- [ ] Implement connected components analysis
- [ ] Implement resilience summary (average path length, network robustness)
- [ ] Implement top-N critical element ranking
- [ ] Attach metrics as graph node/edge attributes
- [ ] Export criticality report (JSON + CSV)
- [ ] Create initial Streamlit dashboard: load graph, display road network, overlay critical nodes/edges
- [ ] Add dashboard controls: select centrality measure, top-N slider
- [ ] Create `configs/analytics.yaml` (metrics to compute, top-N default)
- [ ] Write unit tests: synthetic graph → known centrality values
- [ ] Write integration test: real graph → report structure valid
- [ ] Wire CLI `analyze` and `dashboard` commands

### Acceptance Criteria

- All centrality metrics compute correctly (validated against NetworkX reference)
- Report contains top-N nodes/edges with metric values
- Dashboard displays road network and highlights critical elements
- User can toggle centrality type
- End-to-end demo: image → graph → dashboard with criticality (this is the first full demo)
- Tests pass

### Blocked By

M3

### Blocks

M5, M6 (Dashboard foundation reused)

---

## M5 — Simulation Engine

| Field | Value |
|---|---|
| Goal | Simulate disaster scenarios and visualize impact on the dashboard |
| Module | M5 Simulation Engine |
| Input | `RoadGraph` (clean or annotated) + scenario YAML |
| Output | `SimulationResult` (modified graph + impact report) |
| Demo | Dashboard shows original network → user selects "flood" scenario → affected roads removed → impact displayed |

### Tasks

- [ ] Define scenario YAML schema (type, affected region, action)
- [ ] Implement scenario parser
- [ ] Implement edge removal by spatial containment (polygon or bbox)
- [ ] Implement node removal (junction failures)
- [ ] Implement edge weight modification (partial damage, congestion)
- [ ] Implement impact estimation (disconnected components, reroute demand, affected area)
- [ ] Implement before/after graph pair generation
- [ ] Add simulation controls to dashboard (scenario dropdown, trigger button, result display)
- [ ] Visualize affected region (shaded polygon) and removed edges (dashed/hidden)
- [ ] Create sample scenarios in `configs/scenarios/` (flood, bridge_collapse, road_blockage)
- [ ] Write unit tests: known graph + scenario → expected removed edges
- [ ] Write integration test: real graph + scenario → impact report valid
- [ ] Wire CLI `simulate` command

### Acceptance Criteria

- Scenarios load from YAML
- Edge removal by spatial containment works correctly
- Impact report identifies disconnected components
- Dashboard shows before/after visualization
- Simulation does NOT invoke Vision or any AI (constraint verified)
- Tests pass

### Blocked By

M3, M4 (dashboard foundation)

### Blocks

M6

---

## M6 — Routing Engine

| Field | Value |
|---|---|
| Goal | Compute baseline and alternative routes, display on dashboard |
| Module | M6 Routing Engine |
| Input | `RoadGraph` (original or modified from M5) + routing query |
| Output | `RouteResult` (GeoJSON routes + accessibility) |
| Demo | Dashboard: select origin/destination → see baseline route → trigger flood sim → see alternative route → unreachable areas highlighted |

### Tasks

- [ ] Implement shortest path (Dijkstra)
- [ ] Implement A* with heuristic
- [ ] Implement K-shortest paths (for alternatives)
- [ ] Implement multi-target accessibility (which destinations reachable)
- [ ] Implement route comparison (baseline vs. modified graph routes)
- [ ] Convert routes to GeoJSON with metadata (length, travel time, node list)
- [ ] Add routing controls to dashboard (origin/destination pickers, route display, comparison view)
- [ ] Visualize baseline route (blue) vs. alternative route (green)
- [ ] Visualize unreachable areas
- [ ] Create `configs/routing.yaml` (default algorithm, travel speed assumption)
- [ ] Write unit tests: known graph → known shortest path
- [ ] Write integration test: real graph → valid route geometry
- [ ] Wire CLI `route` command

### Acceptance Criteria

- Shortest path computes correctly (validated against NetworkX reference)
- K-shortest paths returns diverse alternatives
- Accessibility report identifies reachable/unreachable targets
- Dashboard shows baseline and alternative routes
- Routing consumes a graph object, never a mask (constraint verified)
- Tests pass

### Blocked By

M3, M5 (for modified graphs)

### Blocks

M7

---

## M7 — Dashboard Polish & End-to-End Demo

| Field | Value |
|---|---|
| Goal | Polish final dashboard and deliver full demo-ready experience |
| Module | M7 Dashboard Engine (final) |
| Input | All upstream modules integrated |
| Output | Production-quality demonstration: satellite image → interactive decision-support |
| Demo | Full workflow: load image → extract roads → identify critical infra → simulate flood → reroute → show unreachable areas |

### Tasks

- [x] Add image upload/selection UI (user uploads .pkl graph via sidebar) [M4-M6]
- [x] Add pipeline trigger button (sidebar analysis, simulation, routing buttons) [M4-M6]
- [x] Polish criticality visualization (heatmap, color scales, tooltips) [M7]
- [x] Add scenario library (select from predefined disasters in configs/scenarios/) [M5-M7]
- [x] Add route query builder (sidebar origin/destination text inputs) [M6]
- [x] Add comparison view (side-by-side before/after simulation and route maps) [M5-M6]
- [x] Add results export (download GeoJSON routes, JSON report, unified ZIP export) [M4-M7]
- [x] Add narration/storytelling panels (captions on each tab explaining visual meaning) [M7]
- [x] Performance pass: ensure dashboard responsive on demo hardware [M7]
- [x] Create demo script/click-through (documented demo flow) [M7]
- [x] Prepare sample dataset(s) in `assets/samples/` (pre-computed graph + criticality + simulation + route) [M7]
- [x] End-to-end integration test [M7]
- [x] Documentation: dashboard usage guide [M7]

### Acceptance Criteria

- Full workflow runs end-to-end without manual CLI steps
- Dashboard is responsive and clear
- Demo is presentable to hackathon judges
- All modules integrated and functional
- End-to-end test passes
- Good-bye: no silent failures, no broken interactions

### Blocked By

M4, M5, M6

### Blocks

Nothing (final milestone)

---

## Dependency Graph

```
M0 ──▶ M1 ──▶ M2 ──▶ M3 ──┬──▶ M4 ──▶ M5 ──▶ M6 ──▶ M7
                           │      └────────────┘
                           └──▶ M5
                           └──▶ M6
```

Critical path: M0 → M1 → M2 → M3 → M4 → M5 → M6 → M7.

M4 is the first milestone producing a full end-to-end demo (image → graph → dashboard).

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| SAM-Road++ checkpoint unavailable | Medium | High | M2 includes D-LinkNet/U-Net fallback path |
| GPU insufficient for inference | High (hackathon) | Medium | M2 includes CPU inference path; use small sample images |
| sknw produces noisy graphs | Medium | Medium | M3 includes cleaning + simplification; tunable via config |
| Dashboard too slow for demo | Low | Medium | M7 includes performance pass; keep sample images small |
| Team blocked on one person's task | Medium | High | Parallelize: M1 + M8 can run together; M4 + M5 partially parallel after M3 |
| Scope creep beyond demo | High | Medium | Each milestone has explicit acceptance criteria; do not add unrequested features |

---

## Parallelization Opportunities

For a team with multiple developers:

| Window | Parallel Tasks |
|---|---|
| During M0 | Core infrastructure + testing framework setup |
| During M1 | Data layer + initial sample data collection |
| During M2 | Vision pipeline + M3 graph scaffolding (interface-only) |
| During M3 | Graph pipeline + M4 analytics scaffolding (interface-only) |
| After M3 | M4 analytics + M5 simulation engine (M5 only needs graph + scenario config) |
| After M5 | M6 routing + M7 dashboard (M7 can start with M4's dashboard foundation) |

---

## Cross-Reference

| For | See |
|---|---|
| Module specs | `docs/module_map.md` |
| Data flow | `docs/data_flow.md` |
| Interface contracts | `docs/integration_points.md` |
| Technology choices | `docs/technology_mapping.md` |
| Repository structure | `docs/repository_map.md` |
