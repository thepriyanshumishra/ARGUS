# ENGINEERING

# ARGUS Engineering Standards

> This document defines the engineering standards, development philosophy, coding conventions, repository workflow and quality expectations for the ARGUS project.
>
> It is the primary engineering handbook for both human developers and AI coding agents.

---

# Purpose

The objective of this document is to ensure that every contribution made to ARGUS follows a consistent engineering philosophy regardless of whether it is written by a human or an AI coding agent.

Consistency is more valuable than individual coding style.

---

# Engineering Philosophy

ARGUS follows several core engineering principles.

- Documentation before implementation
- Architecture before code
- Simplicity before cleverness
- Reuse before reinvention
- Composition over duplication
- Modular development
- AI-assisted engineering
- Continuous documentation

Every engineering decision should improve maintainability.

---

# Development Workflow

Every feature should follow this lifecycle.

```text
Research

↓

Architecture

↓

Planning

↓

Implementation

↓

Testing

↓

Review

↓

Documentation Update

↓

Merge
```

Implementation should never skip earlier phases.

---

# Repository Organization

Each directory has a single responsibility.

```
src/
```

Contains production source code.

---

```
tests/
```

Contains automated tests.

---

```
configs/
```

Contains configuration files.

---

```
scripts/
```

Contains utility and automation scripts.

---

```
assets/
```

Contains static assets.

---

```
docs/
```

Contains generated technical documentation.

---

```
research/
```

Contains curated research references.

---

```
CONTEXT/
```

Contains AI navigation metadata.

---

# Coding Principles

Every implementation should satisfy the following goals.

## Readability

Code should be understandable without excessive comments.

---

## Maintainability

Future developers should understand the implementation quickly.

---

## Replaceability

Individual modules should be replaceable without affecting unrelated systems.

---

## Predictability

Behavior should be explicit.

Avoid hidden side effects.

---

## Testability

Every important module should be independently testable.

---

# Modularity Rules

Every module should have one primary responsibility.

Avoid creating "God classes" or "utility dumping grounds."

Prefer multiple focused modules over one massive implementation.

---

# Naming Conventions

Names should describe intent rather than implementation.

Prefer

```
RoadGraphBuilder
```

instead of

```
Manager
```

Prefer

```
CriticalityAnalyzer
```

instead of

```
Processor
```

Avoid ambiguous names.

---

# Folder Philosophy

A folder should exist only if it has a clear responsibility.

Avoid deeply nested structures without purpose.

Prefer logical grouping over excessive hierarchy.

---

# Dependency Philosophy

Dependencies should be introduced carefully.

Before adding any dependency ask:

- Does the standard library already solve this?
- Does an existing dependency already solve this?
- Is the dependency actively maintained?
- Is it well documented?
- Does it simplify the project?

Avoid dependency bloat.

---

# Error Handling

Failures should be explicit.

Avoid silent failures.

Every important exception should provide meaningful context.

Never ignore exceptions without justification.

---

# Logging

Logging should help debugging.

Logs should answer:

- What happened?
- Why did it happen?
- Which module produced it?
- What should happen next?

Avoid noisy logs.

---

# Configuration

Configuration should never be hardcoded.

Configuration belongs inside the configuration layer.

Environment-specific behavior should remain configurable.

---

# Documentation Rules

Documentation is considered part of the implementation.

Whenever architecture changes,

documentation should be updated before merge.

The repository should never contain outdated documentation.

---

# Git Workflow

Preferred workflow

```
Feature

↓

Development

↓

Testing

↓

Review

↓

Merge
```

Every commit should represent one logical change.

Avoid large unrelated commits.

---

# Testing Philosophy

Testing should validate behavior,

not implementation details.

Priority order

1. Unit Tests
2. Integration Tests
3. End-to-End Tests

Testing should evolve alongside implementation.

---

# Performance Philosophy

Optimization should be evidence-driven.

Never optimize code without identifying a real bottleneck.

Premature optimization increases complexity.

---

# Security Philosophy

Assume all external inputs are untrusted.

Validate inputs whenever possible.

Avoid exposing internal implementation details.

Protect sensitive configuration.

---

# AI Development Rules

AI coding agents should:

- Read documentation before coding.
- Follow existing architectural decisions.
- Reuse existing utilities whenever possible.
- Avoid introducing duplicate functionality.
- Keep implementations modular.
- Explain significant engineering decisions.
- Update documentation whenever behavior changes.

AI should never rewrite working modules without explicit justification.

---

# Definition of Done

A task is complete only when:

- Implementation is finished.
- Tests pass.
- Documentation is updated.
- Architecture remains consistent.
- No duplicate functionality exists.
- Naming follows conventions.
- The feature integrates cleanly with the existing system.

---

# Quality Checklist

Before merging any feature, verify:

- Architecture respected.
- Documentation updated.
- Code is readable.
- No unnecessary complexity introduced.
- No duplicate logic created.
- Dependencies justified.
- Tests completed.
- Repository remains consistent.

---

# Engineering Decision Hierarchy

When conflicts occur, follow this priority:

1. PROJECT.md
2. ARCHITECTURE.md
3. ENGINEERING.md
4. ../AGENTS.md
5. AI_BOOTSTRAP.md

Engineering decisions must never violate higher-level project goals.

---

# Living Document

This document will evolve throughout the project.

New engineering standards should be added only after careful discussion.

Consistency across the project is more important than individual preference.

---

# Related Documents

- PROJECT.md
- KNOWLEDGE.md
- ARCHITECTURE.md
- ../AGENTS.md
- AI_BOOTSTRAP.md

---

This document defines how ARGUS is engineered.

Every contributor—human or AI—is expected to follow these standards throughout the project's lifecycle.
