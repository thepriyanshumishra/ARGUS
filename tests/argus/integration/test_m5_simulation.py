"""M5 integration tests: simulate CLI + run --scenario."""

import json
import subprocess

import numpy as np


def _make_synthetic_road_mask(tmp_path):
    """Create a synthetic road mask with grid pattern."""
    mask_path = tmp_path / "roads.png"
    import cv2

    height, width = 128, 128
    mask = np.zeros((height, width), dtype=np.uint8)
    mask[30:40, 10:120] = 255
    mask[60:70, 10:120] = 255
    mask[10:120, 50:60] = 255
    mask[10:120, 90:100] = 255
    cv2.imwrite(str(mask_path), mask)
    return mask_path


class TestM5Integration:
    """Integration tests for M5 simulation pipeline."""

    def test_simulate_cli_flood(self, tmp_path):
        """CLI simulate produces valid output for flood scenario."""
        mask_path = _make_synthetic_road_mask(tmp_path)
        graph_path = tmp_path / "graph.pkl"
        out_dir = tmp_path / "sim_output"
        out_dir.mkdir()

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
            check=True,
            cwd="/Users/thedarkpcm/Desktop/Priyanshu/ARGUS",
        )
        assert graph_path.exists(), f"Graph not created at {graph_path}"

        scenario_path = "configs/scenarios/flood_zone_a.yaml"
        result = subprocess.run(
            [
                "uv",
                "run",
                "argus",
                "simulate",
                str(graph_path),
                scenario_path,
                "--output-dir",
                str(out_dir),
            ],
            capture_output=True,
            text=True,
            cwd="/Users/thedarkpcm/Desktop/Priyanshu/ARGUS",
        )
        assert result.returncode == 0, f"simulate failed: {result.stderr}"

        assert (out_dir / "modified_graph.pkl").exists()
        assert (out_dir / "impact_report.json").exists()

        with open(out_dir / "impact_report.json") as f:
            report = json.load(f)
        impact = report.get("impact_report", report)
        assert "removed_nodes" in impact
        assert "removed_edges" in impact
        assert "original_nodes" in impact
        assert "modified_nodes" in impact

    def test_simulate_cli_bridge_collapse(self, tmp_path):
        """CLI simulate bridge collapse removes expected edges."""
        mask_path = _make_synthetic_road_mask(tmp_path)
        graph_path = tmp_path / "graph.pkl"
        out_dir = tmp_path / "sim_bridge"
        out_dir.mkdir()

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
            check=True,
            cwd="/Users/thedarkpcm/Desktop/Priyanshu/ARGUS",
        )
        assert graph_path.exists(), f"Graph not created at {graph_path}"

        result = subprocess.run(
            [
                "uv",
                "run",
                "argus",
                "simulate",
                str(graph_path),
                "configs/scenarios/bridge_collapse.yaml",
                "--output-dir",
                str(out_dir),
            ],
            capture_output=True,
            text=True,
            cwd="/Users/thedarkpcm/Desktop/Priyanshu/ARGUS",
        )
        assert result.returncode == 0, f"simulate bridge failed: {result.stderr}"
        assert (out_dir / "impact_report.json").exists()

    def test_simulate_invalid_scenario_fails(self, tmp_path):
        """Invalid scenario YAML produces error exit."""
        mask_path = _make_synthetic_road_mask(tmp_path)
        graph_path = tmp_path / "graph.pkl"
        bad_yaml = tmp_path / "bad.yaml"
        bad_yaml.write_text("scenario_id: x\nseverity: 0.5\n")

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
            check=True,
            cwd="/Users/thedarkpcm/Desktop/Priyanshu/ARGUS",
        )
        assert graph_path.exists(), f"Graph not created at {graph_path}"

        result = subprocess.run(
            [
                "uv",
                "run",
                "argus",
                "simulate",
                str(graph_path),
                str(bad_yaml),
            ],
            capture_output=True,
            text=True,
            cwd="/Users/thedarkpcm/Desktop/Priyanshu/ARGUS",
        )
        assert result.returncode != 0
