"""Unit tests for Stage 2 improvements."""

import os
import pytest
import torch
import torch.nn as nn
from pathlib import Path

from argus.vision.extractor import (
    VisionConfig,
    SAMRoadExtractor,
    DLinkNetExtractor,
    resolve_device,
    download_checkpoint,
)


def test_resolve_device():
    """Test device resolution mapping for CUDA, MPS, and CPU."""
    # Test explicit CPU
    assert resolve_device("cpu") == "cpu"

    # Test auto resolution
    resolved_auto = resolve_device("auto")
    assert resolved_auto in ["cuda", "mps", "cpu"]

    # Test CUDA requested but unavailable fallback
    if not torch.cuda.is_available():
        assert resolve_device("cuda") == "cpu"
    else:
        assert resolve_device("cuda") == "cuda"

    # Test MPS requested but unavailable fallback
    if not torch.backends.mps.is_available():
        assert resolve_device("mps") == "cpu"
    else:
        assert resolve_device("mps") == "mps"


def test_auto_download_fail_raises_error():
    """Verify that loading an extractor with a missing checkpoint raises FileNotFoundError."""
    # Using allow_random_weights=False (default) should trigger download which fails on invalid path
    config = VisionConfig(
        model_path="nonexistent_checkpoint.pth",
        model_type="sam_road",
        allow_random_weights=False,
    )
    
    with pytest.raises(FileNotFoundError):
        SAMRoadExtractor(config)


def test_device_placement_fallback_to_cpu(monkeypatch):
    """Verify that if VRAM/GPU allocation fails, model falls back to CPU."""
    config = VisionConfig(
        model_path="dummy.pth",
        device="cpu",  # start with cpu then mock fail when setting to GPU
        allow_random_weights=True,
    )
    
    extractor = SAMRoadExtractor(config)
    assert extractor.model is not None
    
    # Mock a runtime error when trying to move the model to an invalid GPU
    def mock_to(self_model, device):
        if device == "cuda" or device == "mps":
            raise RuntimeError("Out of memory or device error")
        return self_model
    
    monkeypatch.setattr(nn.Module, "to", mock_to)
    
    # Manually change device in config and trigger model loading logic
    extractor.config.device = "cuda"
    extractor._load_model()
    
    # Device should have fallen back to 'cpu' due to our mocked RuntimeError
    assert extractor.config.device == "cpu"
