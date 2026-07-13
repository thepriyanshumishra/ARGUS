# Context Index

Index of context states and dynamic memory for the ARGUS platform.
# CONTEXT INDEX

# ARGUS Context Navigation System

> This document is the **entry point of the ARGUS Context System**.
>
> It is **NOT** project documentation.
>
> It is a navigation layer whose sole purpose is to help AI agents quickly locate information without unnecessarily scanning the repository.
>
> The Context System exists to reduce token usage, improve navigation, maintain consistency, and minimize hallucinations.

---

# Purpose

ARGUS is expected to become a large AI-first engineering project.

As the repository grows, AI agents should never perform repository-wide searches unless absolutely necessary.

Instead, they should use this Context System as the project's navigation layer.

This document answers questions such as:

- Where is this information stored?
- Which document should I read?
- Which module owns this functionality?
- Which files are authoritative?
- Which document should I update?

---

# Context Philosophy

Documentation stores knowledge.

Context stores navigation.

Implementation stores behavior.

Research stores references.

Every file has exactly one responsibility.

---

# Repository Navigation Priority

Every AI session should navigate the repository using the following order.

```
AI_BOOTSTRAP

↓

CONTEXT INDEX

↓

Relevant Documentation

↓

Relevant Context

↓

Relevant Module

↓

Implementation

↓

Repository Search (Last Resort)
```

Repository-wide searches should be avoided whenever possible.

---

# Repository Map

## README.md

Purpose

Repository landing page.

Contains

- Project introduction
- Vision
- High-level overview
- Repository summary

Read when

Understanding the project for the first time.

---

## docs/PROJECT.md

Purpose

Canonical project definition.

Contains

- Vision
- Goals
- Scope
- Success criteria
- Product philosophy
- Core modules

Read when

Understanding why ARGUS exists.

---

## docs/KNOWLEDGE.md

Purpose

Project knowledge base.

Contains

- Research summary
- Models
- Papers
- Datasets
- Libraries
- Existing products
- Engineering decisions

Read when

Making technical decisions.

---

## docs/ARCHITECTURE.md

Purpose

System blueprint.

Contains

- Layers
- Modules
- Data flow
- Integration
- Interfaces
- Architectural principles

Read when

Designing or modifying architecture.

---

## docs/ENGINEERING.md

Purpose

Engineering handbook.

Contains

- Coding standards
- Workflow
- Testing
- Naming
- Documentation rules
- Repository standards

Read when

Writing or reviewing implementation.

---

## AGENTS.md

Purpose

AI operating rules.

Contains

- Agent responsibilities
- Repository workflow
- Decision hierarchy
- Review process

Read when

Initializing AI behavior.

---

## docs/AI_BOOTSTRAP.md

Purpose

AI startup protocol.

Contains

- Session initialization (Awareness → Context → State → Health → Readiness → Plan → Implement → Validate)
- State detection (repo maturity assessment)
- Project health check
- Execution readiness gate
- Planning and implementation workflow
- Validation and documentation sync

Read before every AI session.

---

## docs/ system design (NEW)

Purpose

Implementation-ready engineering blueprint.

Contains

- System design, module map, data flow, implementation order
- Integration points, repository map, technology mapping

Read after AI_BOOTSTRAP when preparing to implement — these bridge research to code.

---

# CONTEXT Directory

The Context directory contains repository navigation data.

It should never duplicate project documentation.

Instead, it should point to where information already exists.

---

## INDEX.md

Current document.

Repository navigation.

---

## MAP.md

Purpose

Repository topology.

Should contain

- folder ownership
- module ownership
- dependency map
- implementation locations

---

## GRAPH/

Purpose

Machine-readable relationship graph.

Expected future contents

- dependency graphs
- architecture graphs
- module relationships
- documentation graph

May contain

JSON

YAML

GraphML

Mermaid

or other graph representations.

---

## MEMORY/

Purpose

Persistent engineering memory.

Should contain

- important engineering decisions
- architectural history
- recurring patterns
- project evolution

Acts as long-term project memory.

---

## CACHE/

Purpose

Generated summaries.

Should contain

- AI-generated summaries
- indexed documentation
- compressed context
- reusable reasoning artifacts

Used to reduce token consumption.

---

## SEARCH/

Purpose

Search indexes.

May contain

- keyword indexes
- semantic indexes
- vector indexes
- repository metadata

Used only when required.

---

# Research Directory

## research/repositories.md

Contains

Reference repositories.

Use before searching GitHub.

---

## research/papers.md

Contains

Research papers.

Use before literature review.

---

## research/models.md

Contains

Known AI models.

Use before selecting or changing models.

---

## research/datasets.md

Contains

Available datasets.

Use before collecting new data.

---

## research/references.md

Contains

External resources.

Use when additional evidence is required.

---

# Source Code Navigation

The following directories contain implementation.

## src/

Production source code.

### src/argus/ — Main Python Package (Sprint 0 Complete)

| Module | Path | Purpose | Tests |
|--------|------|---------|-------|
| Core Infrastructure | `src/argus/core/` | Types, protocols, config, logging | `tests/argus/core/` |
| Data Layer (M1) | `src/argus/data/` | Imagery, vector, cache, preprocessing | `tests/argus/data/` |
| Vision Module (M2) | `src/argus/vision/` | Road extraction, postprocess, tiling | `tests/argus/vision/` |
| Graph Engine (M3) | `src/argus/graph/` | Mask→graph, cleaning, export | `tests/argus/graph/` |
| Analytics Engine (M4) | `src/argus/analytics/` | Criticality metrics, reports | `tests/argus/analytics/` |
| Simulation Engine (M5) | `src/argus/simulation/` | Disaster scenarios, impact | `tests/argus/simulation/` |
| Routing Engine (M6) | `src/argus/routing/` | Pathfinding, accessibility | `tests/argus/routing/` |
| Dashboard Engine (M7) | `src/argus/dashboard/` | Streamlit + Folium UI, 6 tabs, config-driven | `tests/argus/dashboard/` |
| CLI Orchestration | `src/argus/cli/` | Typer commands for all stages | `tests/argus/cli/` |

All modules follow strict import rules: import from `argus.core` only, never cross-module.

---

## tests/

Testing.

---

## scripts/

Automation.

---

## configs/

Configuration.

---

## docs/

Design documentation — implementation-ready engineering blueprint.

Contains these files:

| File | Purpose |
|---|---|
| `system_design.md` | Complete high-level architecture (7-layer, 6 modules, interfaces) |
| `module_map.md` | Per-module specifications (purpose, I/O, dependencies, owner, priority) |
| `data_flow.md` | End-to-end data lifecycle (ingest → decision support) |
| `implementation_order.md` | Milestone roadmap (M0–M7) with acceptance criteria and risk register |
| `integration_points.md` | Inter-module interface contracts (7 integration points documented) |
| `repository_map.md` | Folder-to-architecture mapping with directory ownership and import rules |
| `technology_mapping.md` | Table of what modules depend on, justifications, alternatives, replaceability |

Read when preparing for implementation — these documents bridge research to code.

---

## assets/

Static assets.

---

# Decision Lookup

If the task involves...

## Project goals

Read

docs/PROJECT.md

---

## Technical research

Read

docs/KNOWLEDGE.md

---

## System design

Read

docs/ARCHITECTURE.md

---

## Coding standards

Read

docs/ENGINEERING.md

---

## AI behavior

Read

AGENTS.md

---

## Session startup

Read

docs/AI_BOOTSTRAP.md

---

## Repository navigation

Read

CONTEXT/

---

# Context Maintenance Rules

Whenever a new major document is created

Update this file.

Whenever repository structure changes

Update this file.

Whenever a module changes ownership

Update this file.

Whenever new documentation becomes canonical

Register it here.

This file should always reflect the current repository structure.

---

# AI Navigation Rules

Before searching the repository, ask:

1. Does INDEX.md already tell me where this information is?

2. Is there already a canonical document?

3. Is there already a summary?

4. Is repository-wide search actually necessary?

Repository search should always be the final option.

---

# Long-Term Vision

As ARGUS grows, the Context System should evolve into a lightweight knowledge graph capable of directing AI agents to relevant information with minimal token usage.

The Context System should become the central navigation layer connecting documentation, architecture, implementation, research, and engineering memory.

---

# Canonical Rule

Documentation explains.

Context navigates.

Memory remembers.

Architecture organizes.

Implementation executes.

Never mix these responsibilities.

---

This document is the navigation backbone of the ARGUS Operating System.

Every AI coding agent should consult this file before exploring the repository.
