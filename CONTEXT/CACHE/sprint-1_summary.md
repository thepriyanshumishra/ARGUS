# Sprint -1 Summary: Technology Validation

## Objective
Verify architectural feasibility of ARGUS's core technologies before Sprint 0 repository initialization.

## Experiments

| ID | Experiment | Verdict | Key Finding |
|---|---|---|---|
| V1 | Vision Feasibility | **works** | SAM-Road++ loads; checkpoint valid; CPU inference works |
| V2 | Graph Pipeline | **works_with_issues** | Mask→skeleton→Graph concept valid; sknw blocked by numba build |
| V3 | Dashboard Feasibility | **works** | Streamlit+PyDeck render road graph via GeoJSON |
| V4 | Technology Compatibility | **works_with_issues** | 20/20 deps import; Pickle/GeoJSON OK; GraphML fails on MultiDiGraph |

## Overall Verdict
**works_with_issues** — No fundamental architectural blockers. Two issues to resolve in Sprint 0:
1. sknw/numba build (alternative skeleton-to-graph tooling needed)
2. GraphML serialization with MultiDiGraph (use Pickle, convert to Graph for GraphML)

## Environment
- Python 3.11.15, macOS, Homebrew Python
- uv virtualenv at `validation/.venv/`
- All runtime deps installed (numpy, torch, geopandas, streamlit, etc.)

## Reports
- `validation/reports/sprint-1_report.json` — full aggregated report
- `validation/vision/report.json`
- `validation/graph/report.json`
- `validation/dashboard/report.json`
- `validation/compatibility/report.json`

## Next Steps
1. Resolve sknw/numba build or find alternatives (skeleton2graph, custom impl)
2. Pin numpy<2 for torch compatibility
3. Start Sprint 0: initialize `src/`, `tests/`, `configs/` per ARCHITECTURE.md

Generated: 2026-07-12
