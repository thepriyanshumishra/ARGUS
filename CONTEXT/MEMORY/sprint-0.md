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

---

## Sprint 0: Foundation & Repository Setup (2026-07-12)

### Decision
Initialized production ARGUS repository per ARCHITECTURE.md and docs/ blueprints. Created complete project skeleton with tooling, configs, tests, and CI pipeline.

### Deliverables
- **pyproject.toml**: Ruff lint/format, Pyright basic, pytest, coverage, build
- **src/argus/**: 7 module packages + core + CLI (src-layout, editable)
- **configs/**: 10 YAML files (7 module configs + 3 scenario configs)
- **tests/**: 34 smoke tests mirroring src/ structure
- **CI**: GitHub Actions (lint → test → build → docker)
- **Pre-commit**: Ruff + Pyright hooks
- **CLI**: Typer app with 8 commands (info, ingest, extract, build-graph, analyze, simulate, route, run, dashboard)

### Engineering Decisions
1. **torch 2.2.0 pinned** — only version with macOS x86_64 wheels; avoids build-from-source
2. **numpy<2.0** — torch 2.2.0 incompatibility with numpy 2.x
3. **skimage.morphology.skeletonize** — scipy.ndimage.morphology deprecated in SciPy 2.0
4. **Protocol interfaces** — all module boundaries use typing.Protocol for replaceability
5. **OmegaConf YAML configs** — one per module + scenarios, loaded via argus.core.config
6. **loguru logging** — structured console + optional file output

### Verification Results
- ✅ Ruff: 0 errors, 13 files reformatted
- ✅ Pyright: 0 errors on src/
- ✅ pytest: 34/34 tests pass
- ✅ Build: sdist + wheel created successfully
- ✅ CLI: all commands show help, `argus info` works
- ✅ Package structure: matches docs/repository_map.md

### Sprint 1 Readiness
Repository is implementation-ready. Data Layer (M1) can begin immediately using:
- `src/argus/data/imagery.py` (RasterImageLoader)
- `src/argus/data/cache.py` (ArtifactCache)
- `configs/data.yaml`
- `tests/argus/data/test_data.py`

### Artifacts
- `CONTEXT/CACHE/sprint-0_summary.md`

Generated: 2026-07-12
