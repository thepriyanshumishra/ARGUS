# Engineering Memory

## Sprint -1: Technology Validation (2026-07-12)

### Decision
Validated core architectural feasibility before Sprint 0. Ran 4 experiments (Vision, Graph, Dashboard, Compatibility) in the `validation/` directory.

### Findings
- **Vision (V1)**: SAM-Road++ works on CPU. No fundamental blockers.
- **Graph (V2)**: Concept valid, but sknw blocked by numba/llvmlite build on macOS. Tooling choice needs re-evaluation.
- **Dashboard (V3)**: Streamlit+PyDeck works. GeoJSON is the right interchange format.
- **Compatibility (V4)**: 20/20 deps import. Pickle round-trip works. GraphML fails with MultiDiGraph (NetworkX 3.x limitation).

### Verdict
**works_with_issues** — No architectural redesign needed. Two environment/tooling issues to resolve in Sprint 0.

### Key Decisions Taken
1. Use GeoJSON as the interchange format between Graph and Dashboard modules
2. Use Pickle for serialization round-trips; GraphML only after converting MultiDiGraph → Graph
3. Pin numpy<2 for torch compatibility
4. Find alternative to sknw or resolve numba build in Sprint 0

### Artifacts
- `validation/reports/sprint-1_report.json`
- `CONTEXT/CACHE/sprint-1_summary.md`
