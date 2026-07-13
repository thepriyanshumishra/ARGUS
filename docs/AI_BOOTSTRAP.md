# AI BOOTSTRAP

ARGUS AI Bootstrap Protocol — mandatory startup sequence for every AI session.

> Initialize yourself before contributing. Understand first. Engineer second.

## Golden Rule

**Never start coding immediately.** Every session must first understand the repository. Understanding always precedes implementation.

## Bootstrap Sequence

Every AI agent must execute this initialization sequence in order. Do not skip phases.

### Phase 1 — Repository Awareness

Read these documents in order. Each builds on the previous.

1. `../README.md`
2. `PROJECT.md`
3. `KNOWLEDGE.md`
4. `ARCHITECTURE.md`
5. `ENGINEERING.md`
6. `../AGENTS.md`
7. `AI_BOOTSTRAP.md`
8. `../CONTEXT/INDEX.md`

Use `../CONTEXT/INDEX.md` and `../CONTEXT/MAP.md` before performing repository-wide searches.

### Phase 2 — Context Initialization

Load repository context. Understand:
- Project goals, current architecture, implementation status
- Active modules, completed work, pending work, engineering decisions
- Everything that is already known before adding anything new

Prefer the Context system over repository-wide searches.

### Phase 3 — State Detection

Inspect the repository to determine its actual maturity. Check:

- **Implementation**: Does `src/` contain code files or only placeholders?
- **Tests**: Does `tests/` contain test files or only placeholders?
- **Manifests**: Does `pyproject.toml`, `package.json`, or equivalent exist?
- **Tooling**: Are lint, typecheck, formatter, codegen configs present?
- **CI**: Do `.github/workflows/` contain workflow files?
- **ADRs**: Do `docs/adr/` or `CONTEXT/MEMORY/` exist with records?
- **Research**: Are `research/` files populated or still stubs?
- **Phase**: What phase does `PROJECT.md` report (Architecture & Research, Foundation, etc.)?

This phase determines whether you are in a scaffold-only repo, a partially implemented repo, or a mature repo with full tooling.

### Phase 4 — Project Health Check

Evaluate completeness without attempting to fix. Purpose: awareness only.

| Check | What to examine |
|---|---|
| Documentation | Do all referenced docs exist? Are any stubs? |
| Architecture | Do module boundaries in ARCHITECTURE.md match actual src/ layout? |
| Implementation | Which modules have code? Which are empty? Are entrypoints defined? |
| Tooling | Are Ruff/Pyright/pytest/pre-commit configured? |
| Dependencies | Are manifests/lockfiles present? Is the ecosystem clear? |
| ADRs | Do architecture decisions have records, or are they still implicit? |

Record findings internally. Do not modify anything based on health check alone.

### Phase 5 — Working Context

Identify current project state regardless of whether a specific task exists:

- **Milestone**: What phase is PROJECT.md reporting?
- **Active area**: Which module(s) is the project currently focused on?
- **Pending decisions**: Check KNOWLEDGE.md Open Questions section
- **Known constraints**: Architecture boundaries, technology choices, approved toolchain
- **Documentation debt**: Any docs that reference "TODO" or describe unimplemented features

If a task was provided, also identify affected modules, docs, architecture, and tests.

### Phase 6 — Existing Work Discovery

Before writing anything, verify whether similar work already exists:

- Does this module already exist?
- Does a utility already solve this?
- Does documentation already describe this?
- Can an existing implementation be extended?

Never duplicate functionality.

### Phase 7 — Research Validation

If the task requires new technology, consult available research in this priority:

1. Official ISRO documentation
2. PROJECT.md
3. ARCHITECTURE.md
4. ENGINEERING.md
5. Existing repository code
6. Research papers (peer-reviewed)
7. Reference repositories (mature open-source)

Do not invent solutions that already exist.

### Phase 8 — Execution Readiness

Before proceeding to planning, confirm:

- Sufficient context exists (all relevant docs are read)
- Additional research is not required (or is complete)
- Approval is not required (not an architecture change, stack swap, module removal, or restructuring)
- No blockers detected (missing deps, missing config, unclear scope)
- Safe to proceed with implementation

If any condition is not met, resolve it before moving forward.

### Phase 9 — Planning

Prepare an internal execution plan identifying:
- Affected files
- Implementation order
- Dependencies
- Risks
- Documentation updates required
- Testing requirements

Large tasks should be broken into smaller logical steps.

### Phase 10 — Implementation

Implementation begins only after all preceding phases are complete: repository understanding, context loading, state detection, health check, working context, research validation, execution readiness, and planning.

Follow all engineering standards defined in ENGINEERING.md.

### Phase 11 — Validation

After implementation, verify:
- Architecture respected
- Documentation updated
- Consistency maintained
- Modularity preserved
- No duplicate functionality
- Naming conventions followed
- Tests pass (if tooling exists)

Do not consider a task complete until validation succeeds.

### Phase 12 — Documentation Synchronization

If implementation changed architecture, APIs, workflows, behavior, or repository structure, update documentation. Documentation is always synchronized with implementation. Never leave outdated documentation.

---

## Context Usage Strategy

The Context system minimizes token usage. Always follow this order:

1. `../CONTEXT/`
2. Documentation
3. Implementation
4. Repository Search (last resort)

## Memory Strategy

- Documentation = long-term memory
- `CONTEXT/` = working memory
- Current conversation = short-term memory

Persist important engineering decisions into the repository. Future sessions should inherit previous knowledge.

## Repository Navigation Strategy

Never explore randomly. Priority: README → PROJECT → ARCHITECTURE → Relevant Context → Relevant Module → Implementation. Avoid opening unrelated files.

## Decision Strategy

1. Official ISRO Documentation
2. PROJECT.md
3. ARCHITECTURE.md
4. ENGINEERING.md
5. Existing Repository
6. Research Papers
7. Reference Repositories

Never violate higher-priority decisions.

## Repository Improvement Rule

Leave the repository better than you found it. Improve documentation, naming, modularity, and architecture. Reduce duplication and ambiguity.

## Autonomous Responsibilities

Create missing documentation, improve quality, refactor duplication, improve naming, simplify architecture — all without explicit instructions. Major architectural changes still require human approval.

## Human Approval Required

Stop and ask before:
- Architecture redesign
- Technology stack replacement
- Module removal
- Repository restructuring
- Public API redesign
- Core project philosophy changes

## AI Coding Principles

Every implementation should be: Modular, Readable, Maintainable, Explainable, Testable, Replaceable, Scalable.

Avoid: overengineering, unnecessary abstractions, duplicated logic, tightly coupled modules.

## Research Repository Policy

Reference repositories exist for learning. Never blindly copy code. Understand → Evaluate → Adapt → Integrate. Repositories may inspire but should never dictate architecture.

## Session Completion Checklist

- ✓ Implementation complete
- ✓ Documentation synchronized
- ✓ No duplicated functionality
- ✓ Architecture respected
- ✓ Naming conventions followed
- ✓ Tests updated (if applicable)
- ✓ Context remains valid

## Relationship To Other Documents

- `../README.md` — Introduces the project
- `PROJECT.md` — Defines why the project exists
- `KNOWLEDGE.md` — Defines what the project knows
- `ARCHITECTURE.md` — Defines how the system is organized
- `ENGINEERING.md` — Defines how the system is built
- `../AGENTS.md` — Defines how AI agents behave
- `AI_BOOTSTRAP.md` — Defines how every AI session begins
- `../CONTEXT/` — Provides efficient navigation and repository memory

## Final Instruction

If you are reading this document, you are expected to fully initialize yourself before making any contribution to ARGUS. Never prioritize speed over understanding. Bootstrap first. Engineer second.
