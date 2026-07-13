"""Smoke tests for vision module."""

import numpy as np
from argus.vision.extractor import DLinkNetExtractor, SAMRoadExtractor, VisionConfig
from argus.vision.postprocess import fill_gaps, postprocess_mask, skeletonize
from argus.vision.tiling import generate_tiles, stitch_predictions


class TestExtractors:
    """Test road extractors."""

    def test_vision_config_creation(self):
        config = VisionConfig(
            model_path="dummy.pth",
            device="cpu",
            tile_size=256,
            overlap=32,
            threshold=0.5,
            model_type="sam_road",
        )
        assert config.tile_size == 256
        assert config.device == "cpu"

    def test_sam_extractor_creation(self):
        config = VisionConfig(model_path="dummy.pth", device="cpu", allow_random_weights=True)
        # Just test instantiation - model loading is not implemented yet
        extractor = SAMRoadExtractor(config)
        assert extractor is not None
        assert extractor.config == config

    def test_dlinknet_extractor_creation(self):
        config = VisionConfig(model_path="dummy.pth", device="cpu", allow_random_weights=True)
        extractor = DLinkNetExtractor(config)
        assert extractor is not None


class TestPostprocess:
    """Test mask post-processing."""

    def test_postprocess_mask(self):
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[40:60, 40:60] = 1
        mask[10:15, 10:15] = 1  # noise - smaller than min_area

        processed = postprocess_mask(mask, min_area=50, close_kernel=3, open_kernel=3)
        # Noise should be removed (area = 25 < 50)
        assert processed[10:15, 10:15].sum() == 0
        # Main blob should remain (area = 400 > 50)
        assert processed[40:60, 40:60].sum() > 0

    def test_skeletonize(self):
        mask = np.zeros((50, 50), dtype=np.uint8)
        mask[25, 10:40] = 1  # horizontal line
        mask[10:40, 25] = 1  # vertical line

        skeleton = skeletonize(mask)
        assert skeleton.sum() > 0
        assert skeleton.max() <= 1

    def test_fill_gaps(self):
        mask = np.zeros((50, 50), dtype=np.uint8)
        mask[25, 10:20] = 1
        mask[25, 30:40] = 1  # gap in middle

        filled = fill_gaps(mask, max_gap=15)
        assert filled[25, 20:30].sum() > 0  # gap filled


class TestTiling:
    """Test image tiling."""

    def test_generate_tiles(self):
        image = np.random.rand(512, 512, 3)
        tiles = list(generate_tiles(image, tile_size=256, overlap=32))
        assert len(tiles) > 0
        for tile, (_y, _x), (_y_end, _x_end) in tiles:
            assert tile.shape[0] <= 256
            assert tile.shape[1] <= 256

    def test_stitch_predictions(self):
        image = np.random.rand(512, 512)
        tiles = list(generate_tiles(image, tile_size=256, overlap=32))

        # Create dummy predictions
        predictions = []
        for tile, (_y, _x), (_y_end, _x_end) in tiles:
            pred = np.ones((tile.shape[0], tile.shape[1]), dtype=np.float32) * 0.5
            predictions.append((pred, (_y, _x)))

        stitched = stitch_predictions(predictions, (512, 512), tile_size=256, overlap=32)
        assert stitched.shape == (512, 512)
        assert (stitched > 0).any()
