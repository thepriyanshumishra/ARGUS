"""M4 integration tests: build graph → analyze → verify reports."""

import os

os.environ["ARGUS_TESTING"] = "1"

import json
import subprocess

import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.transform import from_bounds


def _make_synthetic_road_mask(tmp_path):
    """Create a synthetic road mask with a simple grid pattern."""
    mask_path = tmp_path / "roads.png"
    height, width = 128, 128
    mask = np.zeros((height, width), dtype=np.uint8)
    mask[30:40, 10:120] = 255  # horizontal road
    mask[60:70, 10:120] = 255  # horizontal road
    mask[10:120, 50:60] = 255  # vertical road
    mask[10:120, 90:100] = 255  # vertical road

    transform = from_bounds(0, 0, 1, 1, width, height)
    with rasterio.open(
        mask_path,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=1,
        dtype=np.uint8,
        crs=CRS.from_epsg(4326),
        transform=transform,
    ) as dst:
        dst.write(mask, 1)
    return mask_path


class TestM4Integration:
    """Integration tests for M4 pipeline: build → analyze → report."""

    def test_build_and_analyze_pipeline(self, tmp_path):
        """Full pipeline: build graph from mask → analyze → generate reports."""
        mask_path = _make_synthetic_road_mask(tmp_path)
        graph_path = tmp_path / "graph.pkl"
        report_dir = tmp_path / "reports"
        report_dir.mkdir()

        result = subprocess.run(
            [
                "uv",
                "run",
                "argus",
                "build-graph",
                str(mask_path),
                "--output",
                str(graph_path),
                "--format",
                "pickle",
            ],
            capture_output=True,
            text=True,
            cwd="/Users/thedarkpcm/Desktop/Priyanshu/ARGUS",
        )
        assert result.returncode == 0, f"build-graph failed: {result.stderr}"
        assert graph_path.exists(), "Graph pickle not created"

        result = subprocess.run(
            [
                "uv",
                "run",
                "argus",
                "analyze",
                str(graph_path),
                "--output",
                str(report_dir),
                "--format",
                "both",
            ],
            capture_output=True,
            text=True,
            cwd="/Users/thedarkpcm/Desktop/Priyanshu/ARGUS",
        )
        assert result.returncode == 0, f"analyze failed: {result.stderr}"

        json_path = report_dir / "criticality_report.json"
        assert json_path.exists(), "JSON report not created"

        csv_files = list(report_dir.glob("*.csv"))
        assert len(csv_files) > 0, "No CSV report files created"

        with open(json_path) as f:
            report = json.load(f)
        assert "report" in report, "Report missing data section"
        assert "summary" in report, "Report missing summary section"
        assert "metrics_computed" in report["summary"], "Summary missing metrics_computed"

    def test_analyze_metrics_subset(self, tmp_path):
        """Test analyze command with a subset of metrics."""
        mask_path = _make_synthetic_road_mask(tmp_path)
        graph_path = tmp_path / "graph.pkl"
        report_dir = tmp_path / "reports"
        report_dir.mkdir()

        subprocess.run(
            [
                "uv",
                "run",
                "argus",
                "build-graph",
                str(mask_path),
                "--output",
                str(graph_path),
                "--format",
                "pickle",
            ],
            capture_output=True,
            text=True,
            cwd="/Users/thedarkpcm/Desktop/Priyanshu/ARGUS",
        )

        result = subprocess.run(
            [
                "uv",
                "run",
                "argus",
                "analyze",
                str(graph_path),
                "--output",
                str(report_dir),
                "--metrics",
                "betweenness,bridges",
                "--format",
                "json",
            ],
            capture_output=True,
            text=True,
            cwd="/Users/thedarkpcm/Desktop/Priyanshu/ARGUS",
        )
        assert result.returncode == 0, f"analyze with metrics subset failed: {result.stderr}"

        # Verify only requested metrics appear in summary table
        assert "Betweenness" in result.stdout or "betweenness" in result.stdout
        assert "Bridges" in result.stdout or "bridges" in result.stdout

    def test_analyze_empty_graph_handling(self, tmp_path):
        """Test that analyze command handles empty graphs gracefully."""
        import pickle

        import networkx as nx
        from argus.core.types import RoadGraph

        empty_graph_path = tmp_path / "empty.pkl"
        rg = RoadGraph(
            graph=nx.MultiDiGraph(),
            crs="EPSG:4326",
            bounds=(0.0, 0.0, 1.0, 1.0),
            metadata={"file_path": "test.png"},
        )
        with open(empty_graph_path, "wb") as f:
            pickle.dump(rg, f)

        report_dir = tmp_path / "reports"
        report_dir.mkdir()

        result = subprocess.run(
            [
                "uv",
                "run",
                "argus",
                "analyze",
                str(empty_graph_path),
                "--output",
                str(report_dir),
            ],
            capture_output=True,
            text=True,
            cwd="/Users/thedarkpcm/Desktop/Priyanshu/ARGUS",
        )
        assert result.returncode != 0, "Should fail on empty graph"

    def test_full_run_command(self, tmp_path):
        """Test the run command for M1→M4 pipeline (handles empty graphs gracefully)."""
        image_path = tmp_path / "test_rgb.tif"
        height, width = 128, 128
        data = np.random.randint(0, 255, (3, height, width), dtype=np.uint8)
        transform = from_bounds(0, 0, 1, 1, width, height)
        with rasterio.open(
            image_path,
            "w",
            driver="GTiff",
            height=height,
            width=width,
            count=3,
            dtype=np.uint8,
            crs=CRS.from_epsg(4326),
            transform=transform,
        ) as dst:
            dst.write(data)

        output_dir = tmp_path / "outputs"
        output_dir.mkdir()

        result = subprocess.run(
            [
                "uv",
                "run",
                "argus",
                "run",
                str(image_path),
                "--output-dir",
                str(output_dir),
            ],
            capture_output=True,
            text=True,
            timeout=300,
            cwd="/Users/thedarkpcm/Desktop/Priyanshu/ARGUS",
        )
        assert result.returncode == 0, f"run command failed: {result.stderr}"

        assert (output_dir / "mask.png").exists(), "mask.png not created"
        assert (output_dir / "graph.pkl").exists(), "graph.pkl not created"
        assert "Pipeline complete" in result.stdout
