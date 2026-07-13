# ARCHITECTURE

# ARGUS Architecture

> This document defines the architectural blueprint of ARGUS.
>
> It explains **how the system is organized**, **why each component exists**, and **how information flows throughout the platform**.
>
> This document is intentionally implementation-agnostic.
> It defines architecture, not code.

---

# Purpose

The objective of this document is to establish a stable architectural foundation before implementation begins.

Every implementation decision should originate from this document.

Architecture must remain significantly more stable than code.

---

# Architecture Philosophy

ARGUS follows several core architectural principles.

- Product-first architecture
- AI-first engineering
- Modular design
- Replaceable components
- Loose coupling
- High cohesion
- Explainable systems
- Documentation-driven development

---

# High-Level System Overview

ARGUS transforms satellite imagery into actionable transportation intelligence.

The complete workflow is:

```text
Satellite Imagery

↓

Road Extraction

↓

Road Graph Generation

↓

Graph Refinement

↓

Graph Analytics

↓

Criticality Analysis

↓

Disaster Simulation

↓

Alternative Routing

↓

Interactive Dashboard
```

---

# System Layers

The platform is divided into independent layers.

## Layer 1

### Data Layer

Responsible for

- Satellite imagery
- GIS layers
- Metadata
- Administrative boundaries
- Disaster overlays

Output

Standardized geospatial inputs.

---

## Layer 2

### Vision Layer

Responsible for

- Image preprocessing
- Road extraction
- Occlusion recovery
- Feature generation

Possible future models

- SAM-Road++
- DeH4R
- Sat2Graph
- D-LinkNet
- Other future models

The architecture should never depend on one specific model.

---

## Layer 3

### Graph Layer

Responsible for

- Graph construction
- Topology generation
- Node creation
- Edge creation
- Connectivity validation
- Graph cleaning
- Graph simplification

Expected libraries

- OSMnx
- NetworkX
- sknw

This layer represents the core of ARGUS.

---

## Layer 4

### Analytics Layer

Responsible for

- Centrality
- Connectivity
- Bridges
- Articulation Points
- Graph metrics
- Network resilience

Outputs

Actionable transportation intelligence.

---

## Layer 5

### Simulation Layer

Responsible for

- Flood simulation
- Bridge failures
- Road blockages
- Disaster scenarios
- Edge weight modification
- Dynamic graph updates

Simulation must remain independent from AI inference.

---

## Layer 6

### Routing Layer

Responsible for

- Shortest paths
- Alternative routing
- Emergency routing
- Route comparison
- Accessibility analysis

Routing always operates on the generated graph.

Never directly on segmentation outputs.

---

## Layer 7

### Presentation Layer

Responsible for

- Dashboard
- GIS visualization
- Decision support
- User interaction
- Reports
- Scenario comparison

This is the primary user-facing layer.

---

# Core Modules

ARGUS consists of independent modules.

## Vision Module

Input

Satellite imagery

Output

Road graph candidates

Responsibilities

- preprocessing
- inference
- occlusion handling

---

## Graph Engine

Input

Road candidates

Output

Validated road graph

Responsibilities

- graph construction
- topology refinement
- graph validation

---

## Criticality Engine

Input

Road graph

Output

Critical infrastructure metrics

Responsibilities

- betweenness
- closeness
- bridges
- articulation points
- resilience metrics

---

## Simulation Engine

Input

Road graph

Disaster scenario

Output

Modified graph

Responsibilities

- disaster modeling
- edge modifications
- scenario generation

---

## Routing Engine

Input

Modified graph

Output

Optimal routes

Responsibilities

- routing
- rerouting
- accessibility
- evacuation

---

## Dashboard Engine

Input

Results from every module

Output

Interactive visualization

Responsibilities

- visualization
- user interaction
- reports
- GIS overlays

---

# Module Independence

Every module must communicate through interfaces.

Modules should never directly manipulate another module's internal implementation.

Example

Vision

↓

Graph API

↓

Analytics

↓

Simulation

↓

Routing

↓

Dashboard

This allows future replacement of individual components.

---

# Data Flow

```text
Satellite Image

↓

Vision

↓

Road Graph

↓

Graph Validation

↓

Analytics

↓

Simulation

↓

Routing

↓

Visualization
```

Each stage consumes the output of the previous stage.

---

# Architectural Boundaries

The following responsibilities must remain isolated.

Vision

≠

Graph

Graph

≠

Simulation

Simulation

≠

Routing

Routing

≠

Dashboard

No module should perform another module's responsibilities.

---

# Replaceability

Every major subsystem should be replaceable.

Examples

Road Extraction

Today

SAM-Road++

Tomorrow

Future Vision Model

No downstream module should require modification.

---

Graph Library

Today

NetworkX

Tomorrow

cuGraph

Downstream modules should remain unchanged.

---

Dashboard

Today

Streamlit

Tomorrow

React

Business logic should remain unchanged.

---

# Integration Strategy

The project should integrate existing technologies whenever possible.

Priority

1. Reuse
2. Adapt
3. Extend
4. Build

Never invert this order.

---

# Repository Architecture

```
Documentation

↓

Architecture

↓

Implementation

↓

Testing

↓

Deployment
```

Implementation should never precede architecture.

---

# AI Architecture

Future AI coding agents should interact with the repository using the following order.

1.

PROJECT.md

↓

2.

KNOWLEDGE.md

↓

3.

ARCHITECTURE.md

↓

4.

ENGINEERING.md

↓

5.

../AGENTS.md

↓

6.

AI_BOOTSTRAP.md

↓

7.

../CONTEXT/

Only after understanding these documents should implementation begin.

---

# Architectural Decisions

Current accepted decisions

Product

Decision-support platform

Not an AI model.

---

Architecture

Modular.

---

Development

AI-first.

---

Research

Evidence-driven.

---

Implementation

Repository-driven.

---

Reuse

Preferred over rebuilding.

---

# Future Expansion

The architecture should support future integration of

- New AI models
- New disaster scenarios
- Additional graph algorithms
- Traffic prediction
- Real-time sensor data
- Weather feeds
- Digital twin capabilities
- Cloud deployment
- Multi-city analysis

No architectural redesign should be required.

---

# Architecture Review Rule

Any implementation that violates the architectural boundaries described in this document should be treated as an architectural issue before becoming a coding task.

Architecture changes require explicit review.

Implementation changes do not.

---

# Relationship to Other Documents

PROJECT.md

Defines

Why ARGUS exists.

---

KNOWLEDGE.md

Defines

What ARGUS knows.

---

ARCHITECTURE.md

Defines

How ARGUS is organized.

---

ENGINEERING.md

Defines

How ARGUS is built.

---

../AGENTS.md

Defines

Who performs the work.

---

AI_BOOTSTRAP.md

Defines

How AI agents should initialize themselves.

---

This document is the canonical architectural reference for ARGUS.

Every future implementation must remain consistent with the architectural principles established here.