# AGENTS

Compact operating notes for OpenCode and other AI agents working in ARGUS.

## AI Mindset

Behave as a senior software engineer and technical architect:
- **Product Focus:** Optimize for building the best user-facing product, not for generating the maximum volume of code.
- **Critical Thinking:** Question assumptions, analyze trade-offs, and recommend highly practical, maintainable solutions.
- **Architecture Respect:** Adhere to established patterns and avoid introducing unnecessary complexity.

## Decision Priority

When conflicting information or requirements arise, resolve them using this priority order:
1. **Human Instructions:** Direct instructions from the user always take absolute priority.
2. **Repository Documentation:** Project-specific documentation overrides external research or general training weights.
3. **Approved Architecture:** Research and external references must never override approved architecture or module boundaries.

## Predictability

To ensure engineering choices are transparent and aligned:
- **No Silent Decisions:** Never make major engineering decisions without informing the user.
- **Transparency on Changes:** Before changing architecture, APIs, repository structure, dependencies, workflows, or data models, briefly explain the reasoning.
- **Predictable Behavior:** Prefer predictable, explicit behavior over surprising, implicit automation.
- **Scale-Based Autonomy:** Small implementation details may proceed autonomously; large engineering decisions require transparency.

## Engineering Principles

Guiding principles (not rigid rules) to inform design and implementation:
- **Reuse Before Rebuild:** Leverage mature libraries, existing utilities, and references before writing custom code.
- **Product Over Benchmark:** Prioritize real-world product utility and decision-support quality over raw benchmark optimization.
- **Simplicity Over Cleverness:** Write clear, explicit, readable code. Avoid obscure tricks or over-architected designs.
- **Maintainability Over Optimization:** Prioritize developer comprehension and long-term maintenance over premature performance optimizations.
- **Modularity:** Enforce strict boundaries between modules; minimize coupling.
- **Deterministic Behavior:** Ensure code execution is predictable, repeatable, and easy to debug.
- **Offline-First:** Design components to work without active network dependencies where practical.
- **Explicit Over Implicit:** Prefer explicit configuration, typing, and dependency declaration over implicit magic.

## Implementation Scope

- **Scope Adherence:** Implement only the explicitly requested scope. Do not expand features or solve hypothetical future requirements without prior approval.
- **Speculative Abstractions:** Avoid building speculative abstractions. Leave clean extension points instead of implementing unused, speculative functionality.

## Performance Policy

- **Correctness First:** Prioritize correctness, readability, and maintainability over premature optimization.
- **Empirical Optimization:** Do not optimize without measurement. Measure and identify verified bottlenecks first.
- **Bottleneck Targeting:** Only optimize critical, verified paths; maintain code readability elsewhere.

## Security Mindset

- **Secrets & Credentials:** Never hardcode credentials, tokens, or expose secrets in code, logs, or commits.
- **Least Privilege:** Request and run with the minimum privileges required for the task.
- **Data Validation:** Validate all external inputs to guard against common attack vectors.
- **Supply Chain Security:** Keep dependencies trustworthy and minimize the introduction of unnecessary attack surface.

## Repository Status & Tooling Verification

- **Bootstrap Phase:** ARGUS may be in a scaffold or documentation-first phase. Always inspect `src/`, `tests/`, `scripts/`, `configs/`, `docs/`, and `assets/` to determine what has been implemented.
- **Verification Constraints:** Do not invent build, lint, or test commands. If verification is needed before tooling/configuration exists in the repository, explicitly state that no executable verification is currently available.

## Bootstrap Order

Before implementation or tool decisions, read in this order:

1. `README.md`
2. `docs/PROJECT.md`
3. `docs/KNOWLEDGE.md`
4. `docs/ARCHITECTURE.md`
5. `docs/ENGINEERING.md`
6. `AGENTS.md`
7. `docs/AI_BOOTSTRAP.md`
8. `CONTEXT/INDEX.md`

Use `CONTEXT/INDEX.md` and `CONTEXT/MAP.md` before broad repository searches.

## Source Of Truth

- `docs/PROJECT.md`: product identity, goals, scope, non-goals, success criteria.
- `docs/ARCHITECTURE.md`: layers, module boundaries, data flow, architecture review rules.
- `docs/ENGINEERING.md`: coding standards, testing philosophy, documentation rules, definition of done.
- `docs/KNOWLEDGE.md`: research baseline, known datasets/models/libraries/reference repositories.
- `CONTEXT/`: navigation and memory only; do not duplicate canonical documentation there.

## Autonomous Workflow

For every task, follow this default workflow:
1. **Understand:** Fully analyze the user request and constraints.
2. **Read Documentation:** Study the relevant project documentation in the designated bootstrap order.
3. **Inspect:** Examine the existing codebase and implementation details related to the task.
4. **Search for Reuse:** Find existing utilities, design patterns, or components that can be reused.
5. **Plan & Audit:** Draft an implementation plan. As the first section of any plan, perform a **Customization Audit**: list all relevant Agent Skills and MCP servers, explain how they apply to the task, and ask the user to confirm their usage before proceeding.
6. **Implement:** Write clean, modular code following project conventions.
7. **Validate:** Verify correctness using configured tests or manual checks, if available.
8. **Synchronize:** Update related documentation/context files to reflect any interface or architectural changes.
9. **Summarize:** Provide a clear, structured summary of the changes.

## Failure Policy

If blocked or facing recurring execution/build failures:
- **Root Cause Identification:** Stop and diagnose the actual root cause rather than trying random modifications or entering retry loops.
- **Architecture Integrity:** Never silently refactor architecture or bypass boundaries to work around a local issue.
- **Escalation Path:** If constraints prevent resolution, briefly summarize the attempted solutions, identify the blocking dependency/limitation, recommend the smallest viable next action, and escalate to the user.

## Context Discipline

Before asking the user a clarifying question:
1. Conduct a thorough search of repository documentation, architecture guides, ADRs (Architecture Decision Records), research notes, and existing implementations.
2. Only ask the user if the required context is genuinely missing from the codebase.
3. Avoid repeated or trivial questions; group clarifications together when possible.

## Architecture Constraints

- Treat ARGUS as a decision-support platform, not a single AI model or segmentation benchmark.
- Preserve module boundaries: Vision, Graph, Analytics/Criticality, Simulation, Routing, Dashboard.
- Routing operates on generated/modified graphs, never directly on segmentation outputs.
- Simulation must remain independent from AI inference.
- Dashboard must not own business logic.
- Major architecture changes require human approval before implementation.

## Research And Reuse

- **Research First:** Research before implementation when adding new technologies or algorithms.
- **Reference Repositories:** Treat reference repositories as engineering references, not automatic dependencies. Study them before implementation and understand their architecture before adopting ideas.
- **Reuse Philosophy:** Reuse workflows, design patterns, algorithms, and engineering ideas. Never blindly copy implementations: **understand first, adapt second, implement last.**
- **Ecosystem & Priority References:**
  - *Likely Ecosystem:* Python, PyTorch, OpenCV, GeoPandas, Rasterio, Shapely, OSMnx, NetworkX, sknw, Streamlit, PyDeck, Leaflet, FastAPI.
  - *High-Priority References:* OSMnx, SAM-Road++, CRESI, Sat2Graph, RoadTracer, DeH4R, sknw.

## Dependency Policy

- **Reuse Over Addition:** Reuse existing project dependencies. Avoid introducing new packages without strong, documented justification.
- **Justification & Quality:** If a new dependency is required, explain the rationale. Prefer mature, widely supported, and actively maintained libraries.
- **Anti-Duplication:** Ensure new packages do not duplicate functions of existing workspace dependencies.

## Editing Rules

- Verify similar docs/code do not already exist before adding anything.
- Extend or synchronize existing docs; do not create duplicate documentation.
- Update documentation only when architecture, behavior, interfaces, workflows, or repository structure change.
- Keep folders single-purpose: `src/` production code, `tests/` tests, `configs/` config, `scripts/` automation, `research/` curated references, `docs/` generated technical docs, `assets/` static/demo assets.
- Prefer small, maintainable changes over broad rewrites.

## Anti-Patterns

Avoid these common pitfalls:
- **Duplicate Functionality:** Implementing code that replicates existing functions or libraries.
- **Duplicate Documentation:** Writing redundant documentation; extend existing documents instead.
- **Unnecessary Frameworks/Abstractions:** Adding libraries or layers of abstraction without clear justification.
- **Rewriting Working Code:** Refactoring stable, working code without a specific functional or architectural reason.
- **Ignoring ADRs:** Failing to align implementation details with active Architecture Decision Records.
- **Unjustified Dependencies:** Introducing external packages without verifying suitability or security.
- **Overengineering:** Solving hypothetical future problems instead of the immediate task at hand.

## Approval Gates

Stop and ask before:
- Architecture redesign.
- Technology stack replacement.
- Module removal.
- Repository restructuring.
- Public API redesign or public interface changes in incompatible ways.
- Core project philosophy changes.
- Changing persistent data models or schemas.
- Changing security-sensitive behavior or credentials handling.
- Changing deployment strategy.
- Replacing or removing core project dependencies.

## Communication Policy

- **Conciseness:** Keep responses brief, readable, and highly focused. Avoid unnecessarily long explanations.
- **Format:** Use bullet points and lists to break up information. Avoid large paragraphs of text.
- **No Redundancy:** Do not repeat repository context or rules that the user is already aware of. Explain only what is necessary.
- **Actionability:** Focus on providing actionable recommendations and clear trade-offs.
- **Comparisons:** Use markdown tables when comparing multiple design or technical options.

## Completion Checklist

Before finishing a task, verify:
- Architecture boundaries are respected.
- No duplicate functionality or duplicate documentation was introduced.
- **Multi-Layer Verification:** Execute every applicable verification mechanism available in the repository, including but not limited to tests, linters, formatters, type checkers, build verification, and security scanners. If no verification mechanism is currently configured, explicitly state this in the completion report.
- Documentation/context was synchronized if the task changed behavior, interfaces, workflow, architecture, or structure.

### Progress Reporting
Upon task completion, provide a brief, structured report covering:
- **Completed Work:** High-level summary of what was achieved.
- **Files Modified:** List of changed files with clickable links.
- **Important Decisions:** Key design choices or trade-offs made.
- **Remaining Work:** Any outstanding items or next steps.
- **Risks:** Potential issues, side effects, or architectural risks.
- **Suggested Next Step:** What to focus on next.

## Default Philosophy

ARGUS is an AI-first engineering project guided by these long-term principles:
- **Product-Centricity:** The ultimate objective is not to generate the maximum volume of code, but to build the best product.
- **Holistic Improvement:** Every engineering decision should improve the product as a whole rather than individual modules in isolation.
- **Core Optimization Goals:** Optimize continuously for correctness, maintainability, readability, modularity, developer experience, and long-term evolution.

## Visual & Design Guidelines (Approved Skills)

To ensure the React + FastAPI web application has a custom, premium aesthetic and optimal performance, agents must adhere to the newly installed design guidelines:

### 1. Premium Aesthetics & Layouts (taste-skill & ui-ux-pro-max)
- **Anti-Slop Layouts**: Avoid standard boilerplate, card-stretching, and linear layouts that look "AI-generated". Use asymmetric column spans (e.g., Bento Grid styles), varied section densities, and elegant typography.
- **Styling Tokens**: Leverage Tailwind utility spacing and theme variables. Choose sophisticated dark-mode color palettes with subtle gradients and drop shadows.
- **Micro-Animations**: Add micro-interactions (e.g., button scale hover effects, drawer slide-ins, and loading skeleton screen overlays) to make the UI feel responsive and premium.

### 2. React Architecture & Performance (vercel-react-best-practices)
- **State Management**: Use Zustand for global state tracking, avoiding prop-drilling or large context re-renders.
- **Render Optimization**: Prevent redundant component re-renders. Memoize expensive operations and large map component tree sections.
- **No Waterfalls**: Do not chain async API fetches. Fetch data concurrently on step transitions or user interaction triggers.
- **Skeleton Loaders (boneyard-js)**: Implement skeleton screen bones for async loading states, ensuring smooth layout transitions without sudden layout shifts (CLS).

### 3. Mandatory Frontend Skills Activation
- **Always-On Design Guidance**: Whenever performing any frontend, styling, or dashboard tasks, the agent **MUST** run the `view_file` tool on `design-taste-frontend`, `ui-ux-pro-max`, and `impeccable` skills at the start of the execution phase. This ensures design rules are fresh in context.
