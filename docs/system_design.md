# System Design

ARGUS implementation-ready system architecture. Synthesized from PROJECT.md, ARCHITECTURE.md, KNOWLEDGE.md, and ENGINEERING.md.

> This document is the engineering blueprint. Every implementation task follows this design. It does not redefine architecture — it makes approved architecture implementation-ready.

---

## 1. System Overview

ARGUS is a decision-support platform that transforms satellite imagery into actionable urban mobility intelligence. It is not a segmentation model, a routing engine, or a GIS viewer — it is an integrated platform that chains these capabilities into a single workflow ending in human decision-support.

### Core Identity

| Aspect | Value |
|---|---|
| Identity | Decision-support platform (not a single AI model) |
| Domain | Urban mobility resilience under disaster scenarios |
| Input | Satellite imagery (+ optional GIS overlays) |
| Output | Interactive dashboard showing criticality, simulation impact, and alternative routing |
| Context | Bharatiya Antariksh Hackathon 2026, Problem Statement 4 |
| Scale | Undergraduate team, limited GPU, local development, demo-quality |

### Implementation Philosophy

1. **Product over benchmark** — Engineering quality and demo-ability matter more than SOTA accuracy.
2. **Reuse before reinvent** — Use mature libraries (OSMnx, NetworkX, sknw) before writing custom code.
3. **Modularity** — Strict module boundaries; communicate via interfaces, never internal access.
4. **Replaceability** — Vision model, graph library, and dashboard framework are swappable without downstream changes.
5. **Offline-first** — All core operations work without network dependencies.
6. **Deterministic behavior** — Same input produces same output; no hidden side effects.
7. **Explainability** — Every result (criticality, route change, disruption) is traceable to its cause.

---

## 2. Layered Architecture

Seven layers define the system. Each layer has a single responsibility and a defined interface to adjacent layers.

```
┌─────────────────────────────────────────────────────────┐
│  L7  Presentation Layer   │  Dashboard, GIS visualization│
├─────────────────────────────────────────────────────────┤
│  L6  Routing Layer        │  Shortest path, emergency    │
├─────────────────────────────────────────────────────────┤
│  L5  Simulation Layer     │  Disaster scenarios, edges  │
├─────────────────────────────────────────────────────────┤
│  L4  Analytics Layer      │  Criticality, centrality    │
├─────────────────────────────────────────────────────────┤
│  L3  Graph Layer          │  Road graph construction    │
├─────────────────────────────────────────────────────────┤
│  L2  Vision Layer         │  Road extraction, mask      │
├─────────────────────────────────────────────────────────┤
│  L1  Data Layer           │  Imagery, GIS, metadata I/O │
└─────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

| Layer | Responsibility | Not Responsible For |
|---|---|---|
| L1 Data | Input loading, format normalization, CRS handling, caching | Interpretation, transformation beyond I/O |
| L2 Vision | Preprocessing, road extraction, occlusion recovery, mask generation | Graph construction, routing, visualization |
| L3 Graph | Mask-to-graph conversion, topology construction, cleaning, simplification | Segmentation, analytics, routing |
| L4 Analytics | Centrality, bridges, articulation points, resilience metrics | Graph construction, simulation, routing |
| L5 Simulation | Disaster scenario injection, edge weight modification, impact estimation | AI inference, routing computation, visualization |
| L6 Routing | Shortest paths, alternative routes, emergency routing, accessibility | Simulation logic, graph construction, dashboard |
| L7 Presentation | Interactive map, scenario comparison, decision support UI | Business logic, computation, data processing |

---

## 3. Core Modules

Six modules map to layers L2–L7. Data (L1) is shared infrastructure, not a standalone module.

### Module Interaction Chain

```
Satellite Image
      │
      ▼
┌──────────┐    ┌──────────┐    ┌────────────┐    ┌────────────┐    ┌──────────┐    ┌───────────┐
│  Vision  │───▶│  Graph   │───▶│ Analytics  │───▶│ Simulation │───▶│ Routing  │───▶│ Dashboard │
│  Module  │    │  Engine  │    │  Engine    │    │   Engine   │    │  Engine  │    │  Engine   │
└──────────┘    └──────────┘    └────────────┘    └────────────┘    └──────────┘    └───────────┘
```

Each arrow is an interface contract defined in `docs/integration_points.md`.

### Module I/O Summary

| Module | Input | Output | Swappable? |
|---|---|---|---|
| Vision | Satellite image (raster) | Road segmentation mask | Yes (SAM-Road++ → future models) |
| Graph Engine | Road mask | Validated road graph (NetworkX) | Yes (NetworkX → cuGraph) |
| Analytics Engine | Road graph | Criticality metrics (per-node, per-edge) | Yes (algorithm set extensible) |
| Simulation Engine | Road graph + scenario | Modified graph (edges removed/weighted) | Yes (scenario types extensible) |
| Routing Engine | Modified graph + query | Route(s) + accessibility report | Yes (algorithm set extensible) |
| Dashboard Engine | Results from all modules | Interactive web UI | Yes (Streamlit → React) |

---

## 4. Architectural Boundaries (Non-Negotiable)

These constraints are approved in ARCHITECTURE.md and AGENTS.md. Violation is an architecture issue, not a coding issue.

1. **Routing operates on the generated/modified graph, never directly on segmentation outputs.** Routing requires a validated NetworkX graph. It must never consume raw masks or model logits.
2. **Simulation must remain independent from AI inference.** Simulation modifies graph topology/weights deterministically. It must never invoke the Vision module or any AI model.
3. **Dashboard must not own business logic.** The dashboard renders results computed by other modules. Computation does not happen in the dashboard layer.
4. **No module directly manipulates another module's internals.** Communication is via documented interfaces only.
5. **Architecture must never depend on one specific AI model.** The Vision module interface must accept any model producing a road segmentation mask.

---

## 5. External Interfaces

### User-Facing

| Interface | Technology | Purpose |
|---|---|---|
| Web Dashboard | Streamlit + PyDeck/Leaflet | Interactive map, scenario controls, route display, criticality heatmap |
| CLI | Python (Click/Typer) | Run pipeline, trigger simulations, export results |

### Data Interfaces

| Interface | Format | Direction |
|---|---|---|
| Satellite imagery input | GeoTIFF, PNG, JPEG | Ingest |
| GIS overlays (optional) | GeoJSON, Shapefile | Ingest |
| Road graph export | GraphML, GeoJSON, Pickle | Export |
| Criticality report | JSON, CSV | Export |
| Simulation scenario | YAML config | Ingest |
| Routing result | GeoJSON, JSON | Export |

### Internal Interfaces (between modules)

Defined in detail in `docs/integration_points.md`. Summary:

| From → To | Data Contract |
|---|---|
| Vision → Graph | Binary segmentation mask (numpy array, same CRS as input) |
| Graph → Analytics | NetworkX MultiDiGraph with node/edge attributes |
| Analytics → Simulation | Graph + attached criticality attributes |
| Simulation → Routing | Modified graph (edges removed/weighted) + impact report |
| Routing → Dashboard | GeoJSON routes + accessibility metrics + metadata |
| All → Dashboard | Module results packaged as standardized result objects |

---

## 6. Design Decisions Resolved

The following open questions from KNOWLEDGE.md are resolved pragmatically for hackathon scale. Each resolution documents alternatives and upgrade paths to preserve replaceability.

| Open Question | Resolution | Rationale | Upgrade Path |
|---|---|---|---|
| Final AI model | **SAM-Road++** (pretrained, primary); D-LinkNet (fallback) | Occlusion-robust, graph-aware, pretrained → no training needed for demo | Swap model class in Vision module; interface unchanged |
| Dashboard framework | **Streamlit + PyDeck** | Python-native, fast prototyping, built-in GIS support, low learning curve | Migrate to React/FastAPI; business logic stays in backend modules |
| Deployment strategy | **Local-first** (Docker Compose optional) | Works offline, no cloud dependency, demo-portable | Containerize for cloud; orchestration layer added without arch changes |
| Database choice | **None** — file-based (GeoJSON, Parquet, Pickle) | Hackathon scale needs no DB; file I/O is simpler and transparent | Add PostGIS for multi-city scale; data access interface abstracts storage |
| Graph storage | **NetworkX serialized to GraphML/Pickle** | Native to NetworkX, human-readable (GraphML), fast round-trip (Pickle) | Migrate to Neo4j or PostGIS pgRouting; serialization interface abstracts backend |
| Simulation methodology | **Scenario-based graph injection** | Deterministic, AI-independent, configurable via YAML; supports floods, blockages, bridge failures | Extend scenario types; add probabilistic models if不确定性 data available |

---

## 7. Replaceability Strategy

Every swappable component is isolated behind an interface. Replacing a component requires implementing the interface — no downstream module changes needed.

| Component | Current | Future | Interface |
|---|---|---|---|
| Road extraction model | SAM-Road++ | Any model producing a road mask | `RoadExtractor` protocol |
| Graph library | NetworkX | cuGraph (GPU acceleration) | Internal to Graph Engine; graph accessor interface |
| Dashboard framework | Streamlit | React | Backend exposes JSON via FastAPI; frontend is replaceable |
| Storage backend | File-based | PostGIS, Neo4j | `GraphStore` protocol |
| Routing algorithm | Dijkstra/A* | Contraction hierarchies | `Router` protocol |

---

## 8. Non-Functional Requirements

| Requirement | Target | Enforcement |
|---|---|---|
| Performance | End-to-end pipeline < 5 min on single image (demo scale) | Measure on representative input; optimize only bottlenecks |
| Reliability | No silent failures; all errors are explicit with context | ENGINEERING.md error handling rules |
| Reproducibility | Same input → same output | Deterministic algorithms; config-driven parameters |
| Testability | Unit tests for each module; integration tests for each interface boundary | tests/ mirrors src/ structure |
| Maintainability | Any new AI session can understand the system from docs alone | Documentation-first; this blueprint + canonical docs |
| Portability | Runs on macOS, Linux, Windows (Python 3.11+) | No platform-specific dependencies |
| GPU usage | Optional (model inference only); fallback to CPU | Vision module supports CPU inference path |

---

## 9. Relationship to Other Documents

| Document | Role |
|---|---|
| `PROJECT.md` | Why ARGUS exists (product vision) |
| `ARCHITECTURE.md` | How ARGUS is organized (architecture specification) |
| `system_design.md` | This document — implementation-ready system design |
| `module_map.md` | Per-module detailed specifications |
| `data_flow.md` | End-to-end data lifecycle |
| `implementation_order.md` | Milestone roadmap |
| `integration_points.md` | Inter-module interface contracts |
| `repository_map.md` | Folder-to-architecture mapping |
| `technology_mapping.md` | Per-subsystem technology choices |
| `ENGINEERING.md` | Coding standards and workflow |
| `KNOWLEDGE.md` | Research baseline and open questions |

---

## 10. Design Invariants

These invariants must hold throughout implementation. Any change requires architecture review.

1. The pipeline is a directed chain: Vision → Graph → Analytics → Simulation → Routing → Dashboard.
2. No module reads from another module's internals — only via documented interfaces.
3. Every module is independently testable with mock inputs.
4. Every module produces deterministic output for a given input + config.
5. The Vision model is the only component requiring GPU; all other modules run on CPU.
6. The dashboard renders results; it never computes them.
7. Simulation is pure graph manipulation; it never invokes AI.
8. Routing consumes a graph (original or simulation-modified); it never consumes masks or logits.
