# Knowledge Repository

Index of domain knowledge, references, and external data sources for ARGUS.
# KNOWLEDGE

# ARGUS Knowledge Base

> This document serves as the centralized knowledge repository for the ARGUS project.
>
> It is **NOT** an implementation document.
>
> It exists to consolidate everything the project knows before implementation begins.

---

# Purpose

The purpose of this document is to ensure that future engineering decisions are based on accumulated knowledge rather than assumptions.

This document should continuously evolve throughout the project's lifecycle.

Whenever new research is completed, this document should be updated before implementation decisions are made.

---

# Knowledge Philosophy

ARGUS follows one simple principle:

> **Never reinvent something that already exists.**

Whenever a mature, well-maintained, open-source solution exists, it should be evaluated before designing a new one.

Research always precedes implementation.

---

# Knowledge Sources

The project prioritizes knowledge in the following order.

## Level 1 — Official Sources

Highest priority.

Examples:

- Official ISRO documentation
- Official dataset documentation
- Official APIs
- Official library documentation

---

## Level 2 — Peer Reviewed Research

Examples:

- IEEE
- CVPR
- ICCV
- ECCV
- NeurIPS
- Remote Sensing
- ISPRS
- TGRS

---

## Level 3 — Mature Open Source

Repositories that are

- actively maintained
- widely used
- production quality
- well documented

---

## Level 4 — Industry Best Practices

Examples

- Google
- NVIDIA
- Meta
- Microsoft
- Uber
- ESRI

---

## Level 5 — Internal Engineering Decisions

Project-specific implementations developed by the ARGUS team.

---

# Project Knowledge Domains

The project spans multiple engineering disciplines.

Knowledge should be organized around these domains.

## Computer Vision

Topics include

- Road extraction
- Semantic segmentation
- Occlusion handling
- Vision Transformers
- Foundation Models

---

## Remote Sensing

Topics include

- Satellite imagery
- Geospatial imagery
- Image preprocessing
- Coordinate systems
- Sensor characteristics

---

## Graph Theory

Topics include

- Graph construction
- Network topology
- Connectivity
- Centrality
- Graph traversal
- Bridges
- Articulation Points

---

## Geographic Information Systems

Topics include

- GIS
- Vector data
- Raster data
- Spatial joins
- Coordinate Reference Systems
- Geospatial visualization

---

## Disaster Simulation

Topics include

- Flood simulation
- Road closures
- Infrastructure failures
- Edge weighting
- Network resilience

---

## Routing

Topics include

- Dijkstra
- A*
- K-shortest paths
- Emergency routing
- Dynamic routing

---

## Visualization

Topics include

- Interactive dashboards
- GIS visualization
- Heatmaps
- Layer management
- Decision support interfaces

---

# Research Status

The following research has already been completed.

## Official Documentation

Status

Completed

---

## Existing Products

Status

Completed

---

## Open Source Survey

Status

Completed

---

## Research Papers

Status

Completed

---

## Datasets

Status

Completed

---

## Models

Status

Completed

---

## Libraries

Status

Completed

---

# Reference Repositories

The following repositories have been identified during research.

These repositories are **reference implementations**.

They should NOT automatically become project dependencies.

Every repository should be evaluated before reuse.

## High Priority

- OSMnx
- SAM-Road++
- CRESI
- Sat2Graph
- RoadTracer
- DeH4R
- sknw

---

## Workflow References

- Work-Review
- Ponytail
- Codebase-Memory-MCP
- GSD-Core

---

# Expected Reuse Strategy

The project should maximize reuse.

Potential reusable components include

- Road extraction pipelines
- Graph construction
- Graph simplification
- GIS utilities
- Routing algorithms
- Dashboard patterns
- Dataset preprocessing
- Evaluation metrics

The project should avoid rewriting mature components unless absolutely necessary.

---

# Major Datasets

Current known datasets include

- SpaceNet
- DeepGlobe
- Massachusetts Roads
- CityScale
- Sentinel-2 India
- Global Scale Dataset

Future datasets may be added as research evolves.

---

# Major Models

Current known models include

- D-LinkNet
- SAM-Road
- SAM-Road++
- Sat2Graph
- DeH4R
- RoadTracer
- CoANet
- SPIN RoadMapper

These represent the current research landscape and may evolve over time.

---

# Major Libraries

Expected ecosystem includes

## Computer Vision

- PyTorch
- OpenCV

---

## GIS

- GeoPandas
- Rasterio
- Shapely

---

## Graph

- OSMnx
- NetworkX
- sknw

---

## Dashboard

- Streamlit
- PyDeck
- Leaflet

---

## Backend

- Python
- FastAPI

---

# Engineering Decisions

Current decisions

## Product

Decision

Build a complete decision-support platform.

Not just an AI model.

---

## AI

Decision

Prefer existing pretrained models before training new ones.

---

## Research

Decision

Research first.

Implementation later.

---

## Documentation

Decision

Documentation is considered part of the codebase.

---

## Architecture

Decision

Maintain modular boundaries between

- AI
- Graph
- Simulation
- Routing
- Dashboard

---

# Open Questions

This section tracks unresolved engineering decisions.

Examples

- Final AI model
- Final dashboard framework
- Deployment strategy
- Database choice
- Graph storage
- Disaster simulation methodology

These should remain unresolved until sufficient evidence exists.

---

# Living Document

This document is intentionally designed as a living knowledge base.

It should continuously grow as

- new papers are published
- new repositories emerge
- new datasets become available
- engineering decisions change

Nothing inside this document should be considered permanently fixed.

Knowledge evolves.

ARGUS evolves with it.

---

# Related Documents

- PROJECT.md
- ARCHITECTURE.md
- ENGINEERING.md
- research/repositories.md
- research/models.md
- research/papers.md
- research/datasets.md

These documents expand the knowledge summarized here.

---

**This document is the canonical knowledge foundation of ARGUS.**

Every future AI agent should treat this file as the primary high-level research context before making technical recommendations.
