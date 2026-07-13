# CONTEXT MAP

# ARGUS Repository Map

> This document describes the logical structure of the ARGUS repository.
>
> Unlike `INDEX.md`, which explains **where information lives**, this document explains **how everything is connected**.
>
> It is the architectural map of the repository.
>
> AI agents should use this document to understand ownership, dependencies, module boundaries and future expansion.

---

# Purpose

As ARGUS grows, hundreds of files and dozens of modules may eventually exist.

The objective of this document is to provide a high-level map of the repository without requiring repository-wide scanning.

This document should evolve alongside the project.

---

# Repository Overview

```
ARGUS

│

├── Documentation Layer

├── Context Layer

├── Research Layer

├── Engineering Layer

├── Source Layer

├── Testing Layer

├── Configuration Layer

└── Assets Layer
```

Each layer has a clearly defined responsibility.

No layer should duplicate another.

---

# Layer Ownership

## Documentation Layer

Purpose

Defines
- project identity
- architecture
- engineering standards
- AI workflows
- **implementation blueprint (docs/)**

Contains

```
[Canonical]
README.md
docs/PROJECT.md
docs/KNOWLEDGE.md
docs/ARCHITECTURE.md
docs/ENGINEERING.md
AGENTS.md
docs/AI_BOOTSTRAP.md

[Design Blueprints]
docs/system_design.md
docs/module_map.md
docs/data_flow.md
docs/implementation_order.md
docs/integration_points.md
docs/repository_map.md
docs/technology_mapping.md
```

Authority

Highest.
Implementation should always follow documentation.
Canonical docs define architecture and standards.
Design docs (docs/) make architecture implementation-ready.

---

## Context Layer

Purpose

Repository navigation.

Contains

```
CONTEXT/
```

Responsibilities

- navigation
- indexing
- memory
- relationship mapping
- search optimization

Authority

Navigation only.

Never stores implementation.

---

## Research Layer

Purpose

Collect external knowledge.

Contains

```
research/
```

Responsibilities

- repositories
- papers
- datasets
- models
- references

Authority

External evidence.

Never implementation.

---

## Source Layer

Purpose

Production code.

Contains

```
src/
```

Responsibilities

Business logic.

---

## Testing Layer

Purpose

Quality assurance.

Contains

```
tests/
```

Responsibilities

Validation.

Regression.

Testing.

---

## Configuration Layer

Purpose

Project configuration.

Contains

```
configs/
```

Responsibilities

Environment configuration.

Application configuration.

Tool configuration.

---

## Script Layer

Purpose

Automation.

Contains

```
scripts/
```

Responsibilities

Utilities.

Automation.

Build support.

Migration support.

---

## Asset Layer

Purpose

Static resources.

Contains

```
assets/
```

Responsibilities

Images.

Icons.

Demo assets.

GIS assets.

Static files.

---

# Documentation Relationships

```
README

↓

PROJECT

↓

KNOWLEDGE

↓

ARCHITECTURE

↓

ENGINEERING

↓

AGENTS

↓

AI_BOOTSTRAP

↓

CONTEXT
```

Every AI session should follow this flow.

---

# Engineering Flow

```
Research

↓

Planning

↓

Architecture

↓

Implementation

↓

Testing

↓

Documentation

↓

Review
```

Implementation should never bypass architecture.

---

# Product Flow

```
Vision

↓

Requirements

↓

Architecture

↓

Engineering

↓

Implementation

↓

Validation

↓

Demonstration
```

---

# System Flow

```
Satellite Imagery

↓

Vision

↓

Road Graph

↓

Analytics

↓

Simulation

↓

Routing

↓

Dashboard
```

This represents the functional architecture.

---

# Repository Dependency Graph

```
PROJECT

↓

KNOWLEDGE

↓

ARCHITECTURE

↓

ENGINEERING

↓

Implementation
```

Engineering decisions should flow downward.

Never upward.

---

# AI Navigation Graph

```
AI_BOOTSTRAP

↓

INDEX

↓

Relevant Documentation

↓

Relevant Context

↓

Relevant Module

↓

Implementation
```

Repository-wide search is the final option.

---

# Module Ownership

Future implementation is expected to contain independent modules.

Examples include

```
Vision

Graph

Analytics

Simulation

Routing

Dashboard

Infrastructure
```

Each module should own

- its implementation
- tests
- documentation

No module should directly own another.

---

# Context Ownership

INDEX.md

Repository navigation.

---

MAP.md

Repository relationships.

---

GRAPH/

Machine-readable dependency graphs.

---

MEMORY/

Persistent project memory.

---

CACHE/

Generated summaries.

---

SEARCH/

Repository indexes.

---

# Expected Future Growth

The following additions are expected over time.

Documentation (Completed: docs/ design blueprint — system_design, module_map, data_flow, implementation_order, integration_points, repository_map, technology_mapping)

- ADRs
- API documentation
- Developer guides

Context

- dependency graphs
- semantic maps
- vector indexes

Research

- benchmark results
- experiment logs
- implementation comparisons

Source

- backend
- frontend
- graph engine
- simulation engine
- dashboard

Testing

- unit
- integration
- end-to-end
- benchmarking

---

# Repository Evolution Rule

As the project grows,

this document should always remain a high-level map.

It should never become implementation-specific.

If implementation details appear here,

they belong elsewhere.

---

# Maintenance Rules

Update this document whenever

- major folders are added
- module ownership changes
- repository structure changes
- new architectural layers are introduced

This document should always reflect the logical organization of ARGUS.

---

# Final Principle

Think of the repository as a city.

Documentation defines the laws.

Architecture designs the city.

Engineering builds the roads.

Implementation builds the buildings.

Context provides the map.

Research provides the knowledge.

Every layer has a single responsibility.

Together they form the ARGUS Operating System.

---

This document is the canonical structural map of the ARGUS repository.
