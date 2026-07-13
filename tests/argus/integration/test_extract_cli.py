"""Integration tests for CLI commands."""

import os
os.environ["ARGUS_TESTING"] = "1"

import subprocess

import numpy as np
import pytest
import rasterio
from rasterio.crs import CRS
from rasterio.transform import from_bounds


class TestCLIExtract:
    """Integration tests for argus extract CLI command."""

    @pytest.fixture
    def synthetic_geotiff(self, tmp_path):
        """Create a synthetic GeoTIFF for testing."""
        path = tmp_path / "test.tif"
        height, width = 256, 256
        data = np.random.randint(0, 255, (3, height, width), dtype=np.uint8)
        transform = from_bounds(0, 0, 1, 1, width, height)
        with rasterio.open(
            path,
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
        return path

    def test_extract_command_runs(self, synthetic_geotiff, tmp_path):
        """Test that argus extract runs without error."""
        output = tmp_path / "mask.png"
        result = subprocess.run(
            [
                "uv",
                "run",
                "argus",
                "extract",
                str(synthetic_geotiff),
                "--output",
                str(output),
                "--device",
                "cpu",
                "--tile-size",
                "256",
            ],
            capture_output=True,
            text=True,
            cwd="/Users/thedarkpcm/Desktop/Priyanshu/ARGUS",
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        assert output.exists(), "Output mask not created"
        assert output.stat().st_size > 0, "Output mask is empty"

    def test_extract_outputs_metadata(self, synthetic_geotiff, tmp_path):
        """Test that extract command outputs expected metadata."""
        output = tmp_path / "mask.png"
        result = subprocess.run(
            [
                "uv",
                "run",
                "argus",
                "extract",
                str(synthetic_geotiff),
                "--output",
                str(output),
                "--device",
                "cpu",
                "--tile-size",
                "256",
            ],
            capture_output=True,
            text=True,
            cwd="/Users/thedarkpcm/Desktop/Priyanshu/ARGUS",
        )

        assert result.returncode == 0
        # Check that metadata table is printed
        assert "RoadMask" in result.stdout
        assert "Shape" in result.stdout
        assert "CRS" in result.stdout
        assert "Bounds" in result.stdout
        assert "Model" in result.stdout

    def test_extract_with_dlinknet_model(self, synthetic_geotiff, tmp_path):
        """Test extract command with dlinknet model."""
        output = tmp_path / "mask_dlinknet.png"
        result = subprocess.run(
            [
                "uv",
                "run",
                "argus",
                "extract",
                str(synthetic_geotiff),
                "--output",
                str(output),
                "--device",
                "cpu",
                "--model",
                "dlinknet",
                "--tile-size",
                "256",
            ],
            capture_output=True,
            text=True,
            cwd="/Users/thedarkpcm/Desktop/Priyanshu/ARGUS",
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        assert output.exists(), "Output mask not created"

    def test_extract_custom_threshold(self, synthetic_geotiff, tmp_path):
        """Test extract command with custom threshold."""
        output = tmp_path / "mask_thresh.png"
        result = subprocess.run(
            [
                "uv",
                "run",
                "argus",
                "extract",
                str(synthetic_geotiff),
                "--output",
                str(output),
                "--device",
                "cpu",
                "--threshold",
                "0.3",
                "--tile-size",
                "256",
            ],
            capture_output=True,
            text=True,
            cwd="/Users/thedarkpcm/Desktop/Priyanshu/ARGUS",
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        assert "0.3" in result.stdout  # Threshold should appear in metadata


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
