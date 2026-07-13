# Repository Map

Mapping of repository folders to architecture. Every directory has a clear responsibility and owner. No ambiguous ownership.

> This document defines what lives where and why. Implementation follows this structure exactly.

---

## Repository Structure

```
ARGUS/
├── docs/                           # Design documentation (NEW)
│   ├── system_design.md
│   ├── module_map.md
│   ├── data_flow.md
│   ├── implementation_order.md
│   ├── integration_points.md
│   ├── repository_map.md
│   └── technology_mapping.md
├── src/
│   └── argus/                      # Main Python package
│       ├── __init__.py
│       ├── core/                   # M8 — Shared infrastructure
│       │   ├── __init__.py
│       │   ├── types.py            #   Shared data types (RasterImage, RoadMask, ...)
│       │   ├── protocols.py         #   Interface protocols (RoadExtractor, ...)
│       │   ├── config.py            #   Config loading (OmegaConf)
│       │   └── logging.py           #   Logging setup
│       ├── data/                   # M1 — Data Layer
│       │   ├── __init__.py
│       │   ├── imagery.py           #   Raster loading (Rasterio)
│       │   ├── vector.py            #   Vector loading (GeoPandas)
│       │   ├── cache.py              #   Artifact caching
│       │   └── preprocessing.py     #   CRS conversion, normalization
│       ├── vision/                 # M2 — Vision Module
│       │   ├── __init__.py
│       │   ├── extractor.py         #   RoadExtractor implementation
│       │   ├── sam_road.py           #   SAM-Road++ adapter
│       │   ├── dlinknet.py           #   D-LinkNet fallback adapter
│       │   ├── postprocess.py        #   Mask cleaning, morphology
│       │   └── tiling.py             #   Large image tiling
│       ├── graph/                  # M3 — Graph Engine
│       │   ├── __init__.py
│       │   ├── builder.py            #   RoadGraphBuilder implementation
│       │   ├── sknw_adapter.py       #   Mask → graph conversion
│       │   ├── cleaning.py           #   Graph cleaning, dedup, snap
│       │   ├── simplification.py     #   Degree-2 chain reduction
│       │   └── export.py             #   GraphML, GeoJSON export
│       ├── analytics/              # M4 — Analytics Engine
│       │   ├── __init__.py
│       │   ├── analyzer.py           #   CriticalityAnalyzer implementation
│       │   ├── centrality.py         #   Betweenness, closeness, degree
│       │   ├── vulnerability.py      #   Articulation points, bridges
│       │   └── report.py             #   Report generation (JSON/CSV)
│       ├── simulation/             # M5 — Simulation Engine
│       │   ├── __init__.py
│       │   ├── simulator.py          #   DisasterSimulator implementation
│       │   ├── scenario.py           #   YAML scenario parser
│       │   ├── flood.py              #   Flood scenario logic
│       │   ├── blockage.py            #   Road blockage logic
│       │   └── impact.py             #   Impact estimation
│       ├── routing/                # M6 — Routing Engine
│       │   ├── __init__.py
│       │   ├── router.py             #   Router implementation
│       │   ├── shortest_path.py      #   Dijkstra, A*
│       │   ├── k_shortest.py         #   K-shortest paths
│       │   ├── accessibility.py     #   Multi-target reachability
│       │   └── comparison.py         #   Baseline vs. alternative
│       ├── dashboard/              # M7 — Dashboard Engine
│       │   ├── __init__.py
│       │   ├── app.py                #   Streamlit app entry
│       │   ├── layers.py             #   Map layer management
│       │   ├── controls.py           #   UI controls (scenario, route query)
│       │   ├── visualization.py      #   Criticality heatmap, route rendering
│       │   └── export.py             #   User-triggered exports
│       └── cli/                    # CLI orchestration
│           ├── __init__.py
│           ├── main.py               #   Typer/Click entry point
│           ├── ingest.py             #   `argus ingest`
│           ├── extract.py            #   `argus extract`
│           ├── build_graph.py        #   `argus build-graph`
│           ├── analyze.py            #   `argus analyze`
│           ├── simulate.py           #   `argus simulate`
│           ├── route.py              #   `argus route`
│           ├── dashboard_cmd.py      #   `argus dashboard`
│           └── run.py                #   `argus run` (full pipeline)
├── tests/
│   └── argus/                      # Tests mirror src/argus structure
│       ├── core/
│       ├── data/
│       ├── vision/
│       ├── graph/
│       ├── analytics/
│       ├── simulation/
│       ├── routing/
│       ├── dashboard/
│       └── integration/             # Cross-module integration tests
├── configs/                        # Configuration
│   ├── data.yaml
│   ├── vision.yaml
│   ├── graph.yaml
│   ├── analytics.yaml
│   ├── routing.yaml
│   └── scenarios/                  # Simulation scenario configs
│       ├── flood_zone_a.yaml
│       ├── bridge_collapse.yaml
│       └── road_blockage.yaml
├── scripts/                       # Automation
│   ├── download_models.py           #   Download pretrained checkpoints
│   ├── prepare_samples.py          #   Prepare sample datasets
│   ├── run_demo.sh                  #   Full demo script
│   └── benchmark.py                 #   Performance benchmarking
├── assets/                        # Static/demo assets
│   ├── samples/                    #   Sample satellite images
│   ├── results/                    #   Demo output examples
│   └── checkpoints/                #   Model checkpoints (git-ignored)
├── docs/                           # Documentation
│   ├── PROJECT.md                  #   Vision, goals, scope
│   ├── KNOWLEDGE.md                #   Research knowledge base
│   ├── ARCHITECTURE.md             #   System architecture blueprint
│   ├── ENGINEERING.md              #   Coding & quality standards
│   ├── AI_BOOTSTRAP.md             #   AI session startup protocol
│   ├── system_design.md
│   ├── module_map.md
│   ├── data_flow.md
│   ├── implementation_order.md
│   ├── integration_points.md
│   ├── repository_map.md
│   └── technology_mapping.md
├── research/                       # Curated research references
├── CONTEXT/                        # AI navigation layer
├── README.md
├── AGENTS.md
└── pyproject.toml                  # Package definition (M0)
```

---

## Directory Ownership

| Directory | Owner Module | Responsibility | Contains Code? |
|---|---|---|---|
| `src/argus/core/` | M8 | Shared types, protocols, config, logging | Yes |
| `src/argus/data/` | M1 | Imagery/vector loading, caching, CRS | Yes |
| `src/argus/vision/` | M2 | Road extraction, mask postprocessing | Yes |
| `src/argus/graph/` | M3 | Mask→graph, cleaning, simplification, export | Yes |
| `src/argus/analytics/` | M4 | Criticality metrics, vulnerability, reports | Yes |
| `src/argus/simulation/` | M5 | Disaster scenarios, graph modification | Yes |
| `src/argus/routing/` | M6 | Pathfinding, accessibility, comparison | Yes |
| `src/argus/dashboard/` | M7 | Streamlit UI, map layers, controls | Yes |
| `src/argus/cli/` | CLI | Orchestration only (no business logic) | Yes |
| `tests/argus/` | QA | Unit + integration tests | Yes |
| `configs/` | Config | YAML configs per module + scenarios | No (YAML) |
| `scripts/` | DevOps | Model download, sample prep, demo runner | Yes |
| `assets/` | Assets | Sample images, demo outputs, checkpoints | No (binary) |
| `docs/` | Docs | Design documentation | No (markdown) |
| `research/` | Research | Curated references | No (markdown) |
| `CONTEXT/` | Navigation | AI session navigation + memory | No (markdown) |

---

## Module → Directory Mapping

| Module | Primary Directory | Test Directory |
|---|---|---|
| M8 Core | `src/argus/core/` | `tests/argus/core/` |
| M1 Data | `src/argus/data/` | `tests/argus/data/` |
| M2 Vision | `src/argus/vision/` | `tests/argus/vision/` |
| M3 Graph | `src/argus/graph/` | `tests/argus/graph/` |
| M4 Analytics | `src/argus/analytics/` | `tests/argus/analytics/` |
| M5 Simulation | `src/argus/simulation/` | `tests/argus/simulation/` |
| M6 Routing | `src/argus/routing/` | `tests/argus/routing/` |
| M7 Dashboard | `src/argus/dashboard/` | `tests/argus/dashboard/` |
| CLI | `src/argus/cli/` | `tests/argus/cli/` |
| Integration | N/A | `tests/argus/integration/` |

---

## Folder Rules

1. **One responsibility per folder.** No "utils" or "helpers" dumping grounds.
2. **No cross-module imports except via `core/`.** Modules import from `argus.core` (types, protocols, config) but never from each other's internals.
3. **Tests mirror `src/` structure.** Every source module has a corresponding test directory.
4. **Configs are external.** No hardcoded config in source code; all config in `configs/` YAML files.
5. **No business logic in `scripts/` or `cli/`.** These orchestrate; they do not compute.
6. **`assets/checkpoints/` is git-ignored.** Large model binaries are downloaded by `scripts/download_models.py`, not committed.
7. **No files in root except canonical docs and `pyproject.toml`.** All code lives under `src/argus/`.

---

## Import Rules

```python
# CORRECT — module imports from core only
from argus.core.types import RoadGraph, RoadMask
from argus.core.protocols import RoadExtractor
from argus.core.config import load_config

# CORRECT — module imports its own subpackage
from argus.vision.extractor import SAMRoadExtractor
from argus.graph.builder import RoadGraphBuilder

# WRONG — direct cross-module import (violates boundaries)
from argus.vision.sam_road import SAMRoad  # accessed from M3 — FORBIDDEN
from argus.routing.router import Router    # accessed from M7 directly — FORBIDDEN
```

The correct way for M7 (Dashboard) to use M6 (Routing) is to receive a `RouteResult` object — never to import M6's internal classes.

---

## Cross-Reference

| For | See |
|---|---|
| Module specs | `docs/module_map.md` |
| Interface contracts | `docs/integration_points.md` |
| Implementation order | `docs/implementation_order.md` |
| Technology choices | `docs/technology_mapping.md` |
