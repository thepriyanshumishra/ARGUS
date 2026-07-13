"""Report generation utilities for M4 Criticality Analytics."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from argus.core.logging import get_logger

log = get_logger(__name__)


def generate_report(
    analytics_result: Any,
    output_dir: Path,
    format: str = "both",
) -> dict[str, Path]:
    """Save criticality reports to *output_dir*.

    Parameters
    ----------
    analytics_result:
        An ``AnalyticsResult`` instance (has ``.report`` and ``.summary``).
    output_dir:
        Directory to write reports into.
    format:
        ``"json"``, ``"csv"``, or ``"both"`` (default).

    Returns
    -------
    dict[str, Path]
        Maps ``"json"`` or ``"csv"`` to the written file path(s).
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output: dict[str, Any] = {}

    if format in ("json", "both"):
        full = {
            "report": analytics_result.report,
            "summary": analytics_result.summary,
        }
        json_path = output_dir / "criticality_report.json"
        with open(json_path, "w") as f:
            json.dump(full, f, indent=2, default=serialise_value)
        log.info(f"Saved JSON report → {json_path}")
        output["json"] = json_path

    if format in ("csv", "both"):
        _write_csv_sections(analytics_result.report, output_dir)
        _write_csv_sections(
            _flatten_summary(analytics_result.summary), output_dir, prefix="summary_"
        )
        log.info(f"Saved CSV reports to {output_dir}")
        output["csv"] = output_dir

    return output


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------


def serialise_value(value: Any) -> Any:
    """Convert non-serialisable values (numpy types, sets) for JSON."""
    if isinstance(value, (int, float, str, bool, type(None))):
        return value
    if isinstance(value, (list, tuple)):
        return [serialise_value(v) for v in value]
    if isinstance(value, dict):
        return {str(k): serialise_value(v) for k, v in value.items()}
    try:
        import numpy as np

        if isinstance(value, np.integer):
            return int(value)
        if isinstance(value, np.floating):
            return float(value)
        if isinstance(value, np.ndarray):
            return value.tolist()
    except ImportError:
        pass
    return str(value)


def _write_csv_sections(data: dict[str, Any], output_dir: Path, prefix: str = "") -> None:
    """Write CSV files for each list-valued key in *data*."""
    for key, value in data.items():
        if not isinstance(value, list):
            continue
        if not value:
            continue
        if isinstance(value[0], dict):
            csv_path = output_dir / f"{prefix}{key}.csv"
            df = pd.DataFrame(value)
            df.to_csv(csv_path, index=False)
        elif isinstance(value[0], tuple) and len(value[0]) == 2:
            csv_path = output_dir / f"{prefix}{key}.csv"
            df = pd.DataFrame(value, columns=["id", "score"])
            df.to_csv(csv_path, index=False)
        elif isinstance(value[0], (int, float)):
            csv_path = output_dir / f"{prefix}{key}.csv"
            df = pd.DataFrame({"value": value})
            df.to_csv(csv_path, index=False)


def _flatten_summary(summary: dict[str, Any]) -> dict[str, Any]:
    """Flatten nested summary dict into top-level list-valued keys for CSV."""
    flat: dict[str, Any] = {}
    for section_key, section_val in summary.items():
        if isinstance(section_val, dict):
            for k, v in section_val.items():
                if isinstance(v, (list, int, float, str)) and not isinstance(v, dict):
                    flat[f"{section_key}_{k}"] = v if isinstance(v, list) else [v]
                elif isinstance(v, dict):
                    flat[k] = v
        elif isinstance(section_val, list):
            flat[section_key] = section_val
    return flat
