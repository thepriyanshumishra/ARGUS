# Technology Mapping

Technology choices for every ARGUS subsystem. Each choice documents alternatives considered, justification, reusable components, and expected complexity.

> This document resolves the technology direction noted in README.md and PROJECT.md into concrete, implementation-ready choices. All choices are hackathon-tuned and replaceability-preserving.

---

## Technology Selection Principles

1. **Reuse before reinvent.** Use mature libraries before writing custom code.
2. **Offline-first.** All chosen tech works locally without network dependencies.
3. **Replaceability.** Every choice documents the swap path to a future alternative.
4. **Hackathon-fit.** Prioritize ease of setup, fast iteration, and demo quality over enterprise scalability.
5. **Minimal dependencies.** No library added unless it provides clear value.

---

## Subsystem Technology Map

### M8 — Core Infrastructure

| Field | Value |
|---|---|
| Language | Python 3.11+ |
| Config | OmegaConf (or Pydantic-Settings) |
| Logging | loguru (simpler than stdlib; structured optional) |
| Types | dataclasses + typing_extensions (Protocols) |

**Chosen**: Python 3.11+ with modern type hints.

**Alternatives Considered**:

| Option | Pros | Cons | Decision |
|---|---|---|---|
| Python 3.11+ | Standard ML/GIS ecosystem, team familiarity, type hints | Slower runtime than compiled | **Chosen** — ecosystem dominance trumps runtime perf for hackathon |
| Python 3.10 | Similar | Fewer typing features, fewer perf improvements | Rejected — 3.11 is widely available |
| Python 3.12+ | Latest | Less ecosystem validation, newer dependency compatibility issues | Wait — not needed for hackathon |

**Reusable Components**: None (foundation layer defines its own primitives).

**Expected Complexity**: Low. Define types, protocols, config schema. ~200 lines of Python.

---

### M1 — Data Layer

| Field | Value |
|---|---|
| Raster I/O | Rasterio |
| Vector I/O | GeoPandas |
| CRS | pyproj (via GeoPandas/Rasterio) |
| Arrays | NumPy |

**Chosen**: Rasterio + GeoPandas.

**Alternatives Considered**:

| Option | Pros | Cons | Decision |
|---|---|---|---|
| Rasterio | Industry standard, GeoTIFF support, transform handling | C-dependencyGDAL (install friction) | **Chosen** — no viable alternative for serious raster I/O |
| PIL/Pillow | Easy install, PNG/JPEG | No CRS/transform, no GeoTIFF | Rejected — cannot handle geospatial metadata |
| OpenCV | Easy | No geospatial awareness | Rejected — good for image ops, not for geospatial loads |

**Reusable Components**:
- `rasterio.open()`, `rasterio.features` for I/O
- `geopandas.read_file()` for vector I/O
- `pyproj.CRS` for CRS validation

**Expected Complexity**: Low-Medium. Tiling for large images adds complexity (~300 LOC).

---

### M2 — Vision Module

| Field | Value |
|---|---|
| Model | SAM-Road++ (primary), D-LinkNet (fallback) |
| Inference | PyTorch |
| Image ops | OpenCV |
| Tiling | Custom (or torch slice) |

**Chosen**: SAM-Road++ as primary road extraction model.

**Alternatives Considered**:

| Option | Pros | Cons | Decision |
|---|---|---|---|
| SAM-Road++ | Occlusion-robust, graph-aware, pretrained | Large checkpoint, GPU preferred | **Chosen** — directly addresses problem statement (occlusion-robust extraction) |
| D-LinkNet | Mature, SpaceNet winner, well-documented | Less occlusion handling | **Fallback** — if SAM-Road++ unavailable or too heavy |
| Sat2Graph | Graph-direct output (skips mask step) | Less mature, harder to integrate, non-standard interface | Rejected — adds coupling between Vision and Graph |
| RoadTracer | Iterative graph construction | Non-standard pipeline, harder to integrate | Rejected — violates mask→graph boundary design |
| U-Net baseline | Simple, well-understood | Lower accuracy, no occlusion handling | Dropout option if both above unavailable |

**Reuse Reference Repos**:
- **SAM-Road++**: Study inference wrapper, checkpoint loader, tiling logic. Adapt the inference code (do not depend on their repo structure).
- **D-LinkNet**: SpaceNet reference; adapt model class definition and inference loop.
- Study: CRESI, Sat2Graph, RoadTracer for pipeline patterns but do not adopt their architectures.

**Reusable Components**:
- `torch.load()` for checkpoint loading
- `torchvision.transforms` for preprocessing
- `cv2.morphologyEx()` for mask post-processing
- `cv2.threshold()` for binarization

**Expected Complexity**: High. Model integration, tiling, CPU/GPU paths. ~600-800 LOC. This is the most complex module.

---

### M3 — Graph Engine

| Field | Value |
|---|---|
| Skeletonization | scipy.ndimage.skeletonize |
| Mask→Graph | sknw |
| Graph library | NetworkX |
| Geometry | Shapely |
| Export | NetworkX native (GraphML), custom GeoJSON |

**Chosen**: sknw + NetworkX.

**Alternatives Considered**:

| Option | Pros | Cons | Decision |
|---|---|---|---|
| sknw | Purpose-built for mask-to-graph, simple API, mature | Small library, limited docs | **Chosen** — exactly maps to our use case |
| OSMnx | Street network expert | OSM-centered, not mask-based | Use for reference (OSM-based graphs only) |
| Custom tracing | Full control | Reinventing solved problem | Rejected — violates reuse-first |
| CRESI graph module | Pipeline proven | Tightly coupled to CRESI approach | Reference only — adapt ideas, not code |

**Reuse Reference Repos**:
- **sknw**: Direct use. Read source (~500 LOC) to understand its output schema.
- **CRESI**: Study their mask→graph pipeline for cleaning and simplification ideas.
- **Sat2Graph**: Reference for graph simplification patterns.

**Reusable Components**:
- `sknw.graph_skeleton(mask)` for skeletonization path
- `scipy.ndimage.skeletonize` for preprocessing
- `networkx` for all graph operations
- `shapely.geometry.LineString` for edge geometry

**Expected Complexity**: Medium. Skeleton logic, cleaning heuristics, simplification tuning are iterative. ~400-500 LOC.

---

### M4 — Analytics Engine

| Field | Value |
|---|---|
| Algorithms | NetworkX built-in |
| Reports | Pandas + custom JSON |

**Chosen**: NetworkX (algorithm provider).

**Alternatives Considered**:

| Option | Pros | Cons | Decision |
|---|---|---|---|
| NetworkX centrality | Built-in, mature, well-tested | Slower on huge graphs | **Chosen** — sufficient for hackathon graph sizes |
| igraph | Faster C implementation | Different API, less Python idiomatic | Future option if performance bottleneck |
| Custom centrality | Full control | Reinventing audit-tested algorithms | Rejected — NetworkX is audited |

**Reusable Components**:
- `networkx.betweenness_centrality()` (nodes and edges)
- `networkx.closeness_centrality()`
- `networkx.articulation_points()` (convert to undirected)
- `networkx.bridges()` (undirected)
- `networkx.connected_components()`
- `networkx.average_shortest_path_length()`

**Expected Complexity**: Low-Medium. Algorithm orchestration, report formatting. ~300 LOC.

---

### M5 — Simulation Engine

| Field | Value |
|---|---|
| Graph manipulation | NetworkX |
| Spatial containment | Shapely |
| Scenario config | PyYAML + OmegaConf |
| No external ML | Pure graph logic |

**Chosen**: Custom scenario-based graph injection (no model required).

**Alternatives Considered**:

| Option | Pros | Cons | Decision |
|---|---|---|---|
| Scenario injection (YAML) | Deterministic, testable, AI-independent, simple | No probabilistic realism | **Chosen** — engineering-quality demo over simulation realism |
| Physical flood modeling | Realistic water flow | Complex, slow, needs terrain data, heavy deps | Rejected — overkill for hackathon |
| Probabilistic failure | Stochastic realism | Non-deterministic → harder to demo, harder to verify | Rejected — violates determinism principle |
| Agent-based simulation | Rich dynamics | Massive complexity | Rejected — scope mismatch |

**Future Upgrade**: Add probabilistic scenarios (Monte Carlo edge failure) as an optional mode. The deterministic scenario YAML format naturally extends to stochastic parameters.

**Reusable Components**:
- `shapely.geometry.Polygon`, `shapely.geometry.box` for affected regions
- `shapely.contains()` for spatial containment checks
- `networkx.remove_edge()`, `networkx.remove_node()`

**Expected Complexity**: Low. Pure graph manipulation. ~250 LOC.

---

### M6 — Routing Engine

| Field | Value |
|---|---|
| Algorithms | NetworkX built-in |
| GeoJSON export | Custom (via Shapely) |

**Chosen**: NetworkX path algorithms.

**Alternatives Considered**:

| Option | Pros | Cons | Decision |
|---|---|---|---|
| NetworkX shortest_path | Built-in, tested, simple | Dijkstra O(V²) on dense | **Chosen** — graph sizes small enough |
| A* with heuristic | Faster | Requires heuristic (straight-line for lat/lon) | Implement as enhancement in M6 |
| Contraction hierarchies | Very fast | Preprocessing complexity, heavy dep | Future — for larger city-scale |
| OSMnx routing | Patterns | OSM-specific convenience | Use as reference, not dependency |

**Reusable Components**:
- `networkx.shortest_path()`, `networkx.shortest_path_length()`
- `networkx.astar_path()`
- `networkx.shortest_simple_paths()` for K-shortest
- `networkx.single_source_dijkstra_path_length()` for accessibility

**Expected Complexity**: Low-Medium. Orchestration + GeoJSON conversion. ~300 LOC.

---

### M7 — Dashboard Engine

| Field | Value |
|---|---|
| Framework | Streamlit |
| Map rendering | PyDeck (primary), Folium (fallback) |
| Data prep | Pandas, GeoPandas |

**Chosen**: Streamlit + PyDeck.

**Alternatives Considered**:

| Option | Pros | Cons | Decision |
|---|---|---|---|
| Streamlit | Python-native, fast prototyping, built-in widgets, low learning curve | Not production-grade, limited custom UI | **Chosen** — ideal for hackathon demo |
| Dash (Plotly) | More control, more production-ready | Steeper learning curve, more code | Future — if demo becomes production |
| React + FastAPI | Full control, scalable | Frontend work, build tooling, time cost | Future — only if team has React skills and time |
| Flask + Leaflet | Minimal | Manual everything (UI, state, routing) | Rejected — too much custom work |
| Gradio | Simplest ML demos | Less flexibility for GIS | Rejected — poor fit for multi-layer maps |

**Reuse Reference Repos**:
- **OSMnx**: Reference for map layer patterns, graph-to-GeoJSON conversion
- Streamlit + PyDeck examples for map visualization patterns

**Reusable Components**:
- `streamlit.components.v1` for UI layout
- `pydeck.Deck`, `pydeck.Layer` for 3D map rendering
- `folium.Map`, `folium.GeoJson` (PyDeck fallback)
- `geopandas.GeoDataFrame.to_json()` for GeoJSON layer data

**Expected Complexity**: Medium-High. UI design, interactivity, layer management. ~500-700 LOC. Most iteration happens here.

---

## Supporting Tooling

### M0 Toolchain

| Tool | Type | Choice | Alternatives |
|---|---|---|---|
| Dependency management | Package manager | `uv` (fast) or `pip` (standard) | `poetry`, `conda` |
| Linter | Code quality | Ruff | flake8, pylint |
| Formatter | Code style | Ruff (format mode) | black, isort |
| Type checker | Static type checks | Pyright | mypy |
| Test runner | Test execution | pytest | unittest |
| Pre-commit | Commit hygiene | pre-commit + Ruff + Pyright | Manual hygiene only |
| CI | Automation | GitHub Actions | GitLab CI, CircleCI |

**Justification for Ruff**: Replaces flake8 + black + isort in one fast tool. Modern Rust implementation. Minimal config.

**Justification for Pyright**: Faster than mypy. Same type checking semantics. Good VSCode integration.

---

## Complete Dependency List

### Runtime Dependencies

```toml
[project]
dependencies = [
    # Core
    "python>=3.11",
    "numpy>=1.24",
    "scipy>=1.10",
    "pandas>=2.0",

    # GIS
    "rasterio>=1.3",
    "geopandas>=0.13",
    "shapely>=2.0",
    "pyproj>=3.6",

    # Graph
    "networkx>=3.1",
    "scikit-image>=0.21",   # for skeletonize
    "scikit-learn>=1.3",    # transitive via analytics

    # ML / Vision
    "torch>=2.0",
    "torchvision>=0.15",
    "opencv-python>=4.8",

    # Config
    "omegaconf>=2.3",
    "pyyaml>=6.0",

    # Logging
    "loguru>=0.7",

    # Dashboard
    "streamlit>=1.28",
    "pydeck>=0.8",
    "folium>=0.15",        # fallback

    # CLI
    "typer>=0.9",
]
```

### Development Dependencies

```toml
[project.optional-dependencies]
dev = [
    "ruff>=0.1",
    "pyright>=1.1",
    "pytest>=7.4",
    "pytest-cov>=4.1",
    "pre-commit>=3.5",
    "ipykernel>=6.0",        # for notebook experiments
    "matplotlib>=3.7",        # for graph visualizations
]
```

### Special Notes

- **sknw**: Not on PyPI mainstream — may need `pip install git+https://github.com/Image-Python/sknw.git`. Document in `scripts/download_models.py` or in M0 setup script.
- **SAM-Road++**: Checkpoint download script in `scripts/download_models.py`. Checkpoint committed to `assets/checkpoints/` (git-ignored via LFS or downloaded).
- **GDAL**: Rasterio depends on GDAL. On macOS use `brew install gdal`; on Ubuntu `apt install gdal-bin libgdal-dev`. Document in README's setup section.

---

## Expected Complexity Summary

| Module | LOC (est.) | Complexity | Risk |
|---|---|---|---|
| M8 Core | ~200 | Low | Low |
| M1 Data | ~300 | Low-Medium | Low |
| M2 Vision | ~700 | **High** | **Medium** (model integration) |
| M3 Graph | ~450 | Medium | Low-Medium (sknw output quality) |
| M4 Analytics | ~300 | Low-Medium | Low |
| M5 Simulation | ~250 | Low | Low |
| M6 Routing | ~300 | Low-Medium | Low |
| M7 Dashboard | ~600 | Medium-High | Medium (UI polish) |
| CLI | ~300 | Low | Low |
| **Total** | **~3,400 LOC** | — | — |

---

## Decision Traceability

For each technology choice above, it traces to existing approved decisions:

| Choice | Traceable To |
|---|---|
| Python ecosystem | KNOWLEDGE.md "Major libraries" |
| PyTorch | KNOWLEDGE.md "Major libraries" |
| Rasterio / GeoPandas / Shapely | KNOWLEDGE.md "Major libraries", ARCHITECTURE.md L1 |
| NetworkX / sknw / OSMnx (ref) | ARCHITECTURE.md L3, AGENTS.md "Ecosystem" |
| SAM-Road++ | ARCHITECTURE.md L2 (replaceable Vision model), OPEN question "Final AI model" resolved here |
| Streamlit + PyDeck / Leaflet | ARCHITECTURE.md L7, KNOWLEDGE.md "Major libraries", OPEN question "Final dashboard framework" resolved here |
| File-based storage (no DB) | OPEN questions "Database choice" + "Graph storage" resolved pragmatically for hackathon |
| Scenario-based simulation (no model) | OPEN question "Disaster simulation methodology" resolved; ARCHITECTURE.md "Simulation independent from AI inference" |
| Local deployment | OPEN question "Deployment strategy" resolved; AGENTS.md "Offline-first" |
| OmegaConf / Typer / Ruff / Pyright | Engineering toolchain choices (no conflicting canonical decisions) |

---

## Replaceability Register

| Component | Current | Future | Migration Effort | Interface |
|---|---|---|---|---|
| Vision model | SAM-Road++ | Any model producing a road mask | Low — implement `RoadExtractor` protocol | `argus.core.protocols.RoadExtractor` |
| Graph library | NetworkX | cuGraph | Medium — change `RoadGraph` internal; accessor stays | `argus.core.types.RoadGraph` |
| Dashboard framework | Streamlit | React + FastAPI | High — build API layer + frontend | FastAPI serves JSON; rendering layer is replaceable |
| Storage backend | File-based | PostGIS or Neo4j | Medium — add storage interface implementations | `argus.data.cache.GraphStore` (to be defined in M8) |
| Routing algorithm | Dijkstra/A* | Contraction hierarchies | Low — swap backend; `Router` protocol narrows | `argus.core.protocols.Router` |
| Config format | YAML | Any | Low — OmegaConf handles multiple formats | Config loader |

---

## Cross-Reference

| For | See |
|---|---|
| Module specs | `module_map.md` |
| Data flow | `data_flow.md` |
| Implementation order | `implementation_order.md` |
| Interface contracts | `integration_points.md` |
| System architecture | `system_design.md` |
| Repository structure | `repository_map.md` |
