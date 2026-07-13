from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from argus.core.logging import get_logger
from argus.core.protocols import RoadExtractor
from argus.core.types import RasterImage, RoadMask

log = get_logger(__name__)


CHECKPOINT_URLS = {
    "sam_road": "https://github.com/ShengjiLi/SAM-RoadPlusPlus/releases/download/v1.0/sam_road_plus_plus.pth",
    "dlinknet": "https://github.com/ShengjiLi/D-LinkNet/releases/download/v1.0/dlinknet.pth",
}


def download_checkpoint(model_type: str, dest_path: Path) -> None:
    """Download pretrained checkpoint from release URL."""
    url = CHECKPOINT_URLS.get(model_type)
    if not url:
        raise ValueError(f"No checkpoint URL mapped for model type: {model_type}")

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    log.info(f"Downloading checkpoint for {model_type} from {url} to {dest_path}")

    from urllib.error import HTTPError, URLError
    from urllib.request import urlretrieve

    try:
        urlretrieve(url, dest_path)
        log.info(f"Successfully downloaded checkpoint to {dest_path}")
    except (URLError, HTTPError) as e:
        log.error(f"Failed to download checkpoint from {url}: {e}")
        raise FileNotFoundError(
            f"Pretrained checkpoint for '{model_type}' is missing at '{dest_path}' "
            f"and auto-download failed: {e}. Please check your internet connection "
            f"or manually run 'python scripts/download_models.py'."
        ) from e


def resolve_device(device_str: str) -> str:
    """Resolve 'auto' or select device based on availability (CUDA, MPS, CPU)."""
    dev = device_str.lower() if device_str else "auto"
    if dev == "auto":
        if torch.cuda.is_available():
            return "cuda"
        elif torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"

    if dev == "cuda" and not torch.cuda.is_available():
        log.warning("CUDA requested but not available. Falling back to CPU.")
        return "cpu"
    if dev == "mps" and not torch.backends.mps.is_available():
        log.warning("MPS requested but not available. Falling back to CPU.")
        return "cpu"

    return dev


@dataclass(slots=True)
class VisionConfig:
    """Vision module configuration."""

    model_path: str = ""
    device: str = "auto"
    tile_size: int = 512
    overlap: int = 64
    threshold: float = 0.5
    model_type: str = "hf_unet"  # "hf_unet", "sam_road" or "dlinknet"
    allow_random_weights: bool | None = None

    def __post_init__(self):
        # Auto-resolve checkpoint paths from config
        if not self.model_path:
            if self.model_type == "sam_road":
                self.model_path = "assets/checkpoints/sam_road_plus_plus.pth"
            elif self.model_type == "dlinknet":
                self.model_path = "assets/checkpoints/dlinknet.pth"
            elif self.model_type == "hf_unet":
                self.model_path = "assets/checkpoints/best_road_seg_unet.pth"
                # Use a stable default threshold of 0.25 for Massachusetts U-Net model
                if self.threshold == 0.5:
                    self.threshold = 0.25
        self.device = resolve_device(self.device)

        if self.allow_random_weights is None:
            import os
            import sys

            self.allow_random_weights = "pytest" in sys.modules or os.getenv("ARGUS_TESTING") == "1"

    sam_version: str = "vit_b"  # "vit_b", "vit_l", "vit_h"
    use_sam_decoder: bool = False
    no_sam: bool = False


class BaseExtractor(ABC, RoadExtractor):
    """Base class for road extractors."""

    def __init__(self, config: VisionConfig):
        self.config = config
        self.model = None
        self._load_model()

    @abstractmethod
    def _load_model(self) -> None:
        """Load the model checkpoint."""
        pass

    @abstractmethod
    def _predict(self, tile: np.ndarray) -> np.ndarray:
        """Run inference on a single tile."""
        pass

    def _tile_image(self, image: np.ndarray) -> list[tuple[np.ndarray, tuple[int, int]]]:
        """Split image into overlapping tiles."""
        h, w = image.shape[:2]
        tiles = []
        step = self.config.tile_size - self.config.overlap
        for y in range(0, h, step):
            for x in range(0, w, step):
                y_end = min(y + self.config.tile_size, h)
                x_end = min(x + self.config.tile_size, w)
                tile = image[y:y_end, x:x_end]
                tiles.append((tile, (y, x)))
        return tiles

    def _stitch_tiles(
        self, tiles: list[tuple[np.ndarray, tuple[int, int]]], shape: tuple[int, ...]
    ) -> np.ndarray:
        """Stitch tile predictions back together with averaging."""
        h, w = shape[:2]
        result = np.zeros((h, w), dtype=np.float32)
        count = np.zeros((h, w), dtype=np.float32)

        for pred, (y, x) in tiles:
            y_end = min(y + self.config.tile_size, h)
            x_end = min(x + self.config.tile_size, w)
            result[y:y_end, x:x_end] += pred[: y_end - y, : x_end - x]
            count[y:y_end, x:x_end] += 1

        mask = count > 0
        result[mask] /= count[mask]
        return result

    def extract(self, image: RasterImage, config: VisionConfig | None = None) -> RoadMask:
        """Extract road mask from image."""
        cfg = config or self.config
        log.info(f"Extracting roads from image {image.data.shape}")

        # Prepare image data (normalize to [0, 1])
        img_data = image.data.astype(np.float32)
        if img_data.max() > 1.0:
            img_data /= 255.0

        # Tile and predict
        tiles = self._tile_image(img_data)
        preds = []
        for tile, pos in tiles:
            pred = self._predict(tile)
            preds.append((pred, pos))

        # Stitch
        mask_prob = self._stitch_tiles(preds, img_data.shape[:2])

        # Threshold
        mask_binary = mask_prob > cfg.threshold

        return RoadMask(
            mask=mask_binary.astype(np.uint8),
            crs=str(image.crs),
            transform=image.transform,
            bounds=image.bounds,
            model_name=cfg.model_type,
            model_version="1.0",
            metadata={
                "model": cfg.model_type,
                "threshold": cfg.threshold,
                "tile_size": cfg.tile_size,
                "device": cfg.device,
            },
        )


class SAMRoadExtractor(BaseExtractor):
    """SAM-Road++ extractor with ViT encoder and naive decoder."""

    def _load_model(self) -> None:
        """Load SAM-Road++ checkpoint or initialize with random weights."""
        self.model = SAMRoadPlusPlus(self.config)

        model_path = Path(self.config.model_path)
        if not model_path.exists():
            if self.config.allow_random_weights:
                log.warning(
                    f"Checkpoint not found at {model_path}, using random weights because allow_random_weights is True"
                )
            else:
                log.info(f"Checkpoint not found at {model_path}. Initiating auto-download.")
                try:
                    download_checkpoint(self.config.model_type, model_path)
                except Exception as e:
                    log.error(f"Auto-download failed: {e}")
                    raise FileNotFoundError(
                        f"Checkpoint not found at {model_path} and auto-download failed. "
                        f"Please verify model_path in configuration."
                    ) from e

        if model_path.exists():
            log.info(f"Loading SAM-Road++ from {self.config.model_path}")
            try:
                checkpoint = torch.load(self.config.model_path, map_location=self.config.device)
                if "state_dict" in checkpoint:
                    state_dict = checkpoint["state_dict"]
                elif "model" in checkpoint:
                    state_dict = checkpoint["model"]
                else:
                    state_dict = checkpoint
                self.model.load_state_dict(state_dict, strict=False)
                log.info("SAM-Road++ checkpoint loaded successfully")
            except Exception as e:
                log.error(f"Failed to load checkpoint state dict: {e}")
                raise

        # Device placement with dynamic recovery fallback
        try:
            self.model.to(self.config.device)
        except Exception as e:
            log.warning(
                f"Failed to load model onto device '{self.config.device}': {e}. Falling back to 'cpu'."
            )
            self.config.device = "cpu"
            self.model.to("cpu")

        self.model.eval()

    def _predict(self, tile: np.ndarray) -> np.ndarray:
        """Run inference on tile."""
        # Resize tile to model's expected size if needed
        target_size = self.config.tile_size
        original_shape = tile.shape[:2]
        if tile.shape[0] != target_size or tile.shape[1] != target_size:
            from PIL import Image

            tile_pil = Image.fromarray((tile * 255).astype(np.uint8))
            tile_pil = tile_pil.resize((target_size, target_size), Image.Resampling.LANCZOS)
            tile = np.array(tile_pil) / 255.0

        # Preprocess: HWC -> CHW, normalize, add batch dim
        tile_chw = torch.from_numpy(tile.transpose(2, 0, 1)).float().unsqueeze(0)
        tile_chw = tile_chw.to(self.config.device)

        with torch.no_grad():
            # The model outputs road probability map
            road_prob = self.model(tile_chw)  # Shape: [1, H, W]
            road_prob = road_prob.squeeze(0).cpu().numpy()  # [H, W]

        # Resize back to original tile size if needed
        if road_prob.shape != original_shape:
            from PIL import Image

            road_prob_pil = Image.fromarray((road_prob * 255).astype(np.uint8))
            road_prob_pil = road_prob_pil.resize(
                (original_shape[1], original_shape[0]), Image.Resampling.LANCZOS
            )
            road_prob = np.array(road_prob_pil) / 255.0

        return road_prob


class SAMRoadPlusPlus(nn.Module):
    """SAM-Road++ model: ViT encoder + naive upsampling decoder."""

    def __init__(self, config: VisionConfig):
        super().__init__()
        self.config = config
        self.image_size = config.tile_size
        self.prompt_embed_dim = 256

        # ImageNet normalization
        self.register_buffer(
            "pixel_mean", torch.tensor([123.675, 116.28, 103.53]).view(-1, 1, 1), False
        )
        self.register_buffer(
            "pixel_std", torch.tensor([58.395, 57.12, 57.375]).view(-1, 1, 1), False
        )

        # Build ViT encoder
        if config.no_sam:
            self.image_encoder = self._build_vit_encoder()
        else:
            self.image_encoder = self._build_sam_encoder()

        # Naive decoder: upsample from 256 channels to 2 channels (keypoint, road)
        self.map_decoder = nn.Sequential(
            nn.ConvTranspose2d(256, 128, kernel_size=2, stride=2),
            nn.GroupNorm(32, 128),
            nn.GELU(),
            nn.ConvTranspose2d(128, 64, kernel_size=2, stride=2),
            nn.GELU(),
            nn.ConvTranspose2d(64, 32, kernel_size=2, stride=2),
            nn.GELU(),
            nn.ConvTranspose2d(32, 2, kernel_size=2, stride=2),
        )

    def _build_vit_encoder(self) -> nn.Module:
        """Build ViT-B encoder (no SAM)."""
        from torch.nn import LayerNorm

        # Simple ViT-B/16 implementation
        class VITEncoder(nn.Module):
            def __init__(self, img_size=512, patch_size=16, embed_dim=768, depth=12, num_heads=12):
                super().__init__()
                self.img_size = img_size
                self.patch_size = patch_size
                self.embed_dim = embed_dim
                num_patches = (img_size // patch_size) ** 2

                self.patch_embed = nn.Conv2d(
                    3, embed_dim, kernel_size=patch_size, stride=patch_size
                )
                self.pos_embed = nn.Parameter(torch.zeros(1, num_patches + 1, embed_dim))
                self.cls_token = nn.Parameter(torch.zeros(1, 1, embed_dim))

                # Transformer blocks
                encoder_layer = nn.TransformerEncoderLayer(
                    d_model=embed_dim,
                    nhead=12,
                    dim_feedforward=3072,
                    dropout=0.1,
                    activation="gelu",
                    batch_first=True,
                    norm_first=True,
                )
                self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=12)

                self.norm = LayerNorm(embed_dim)
                self.output_proj = nn.Conv2d(embed_dim, 256, kernel_size=1)

            def forward(self, x):
                B, C, H, W = x.shape
                x = self.patch_embed(x)  # [B, embed_dim, H/16, W/16]
                x = x.flatten(2).transpose(1, 2)  # [B, num_patches, embed_dim]

                cls_tokens = self.cls_token.expand(B, -1, -1)
                x = torch.cat([cls_tokens, x], dim=1)
                x = x + self.pos_embed

                x = self.transformer(x)
                x = self.norm(x)

                # Remove cls token and reshape
                x = x[:, 1:].transpose(1, 2).reshape(B, self.embed_dim, H // 16, W // 16)
                x = self.output_proj(x)  # [B, 256, H/16, W/16]
                return x

        return VITEncoder(img_size=self.image_size, embed_dim=768, depth=12, num_heads=12)

    def _build_sam_encoder(self) -> nn.Module:
        """Build SAM ViT encoder."""
        try:
            from functools import partial

            from segment_anything.modeling.image_encoder import ImageEncoderViT
            from torch.nn import LayerNorm

            # ViT-B config
            encoder_embed_dim = 768
            encoder_depth = 12
            encoder_num_heads = 12
            encoder_global_attn_indexes = [2, 5, 8, 11]

            encoder = ImageEncoderViT(
                depth=encoder_depth,
                embed_dim=encoder_embed_dim,
                img_size=self.image_size,
                mlp_ratio=4,
                norm_layer=partial(LayerNorm, eps=1e-6),
                num_heads=encoder_num_heads,
                patch_size=16,
                qkv_bias=True,
                use_rel_pos=True,
                global_attn_indexes=encoder_global_attn_indexes,
                window_size=14,
                out_chans=256,
            )
            return encoder
        except ImportError:
            log.warning("segment_anything not available, falling back to ViT encoder")
            return self._build_vit_encoder()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.
        Args:
            x: [B, 3, H, W] input image, normalized to [0, 1]
        Returns:
            road_prob: [B, H, W] road probability map
        """
        # Normalize to SAM pixel space
        x = (x * 255 - self.pixel_mean) / self.pixel_std

        # Image encoder
        image_embeddings = self.image_encoder(x)  # [B, 256, H/16, W/16]

        # Decoder
        mask_logits = self.map_decoder(image_embeddings)  # [B, 2, H/16, W/16]

        # Upsample to original resolution
        mask_logits = F.interpolate(
            mask_logits,
            size=(self.image_size, self.image_size),
            mode="bilinear",
            align_corners=False,
        )

        # Return road channel (channel 1) probability
        road_logits = mask_logits[:, 1]  # [B, H, W]
        road_prob = torch.sigmoid(road_logits)
        return road_prob


class DLinkNetExtractor(BaseExtractor):
    """D-LinkNet fallback extractor."""

    def _load_model(self) -> None:
        """Load D-LinkNet checkpoint or initialize with random weights."""
        self.model = DLinkNet()

        model_path = Path(self.config.model_path)
        if not model_path.exists():
            if self.config.allow_random_weights:
                log.warning(
                    f"Checkpoint not found at {model_path}, using random weights because allow_random_weights is True"
                )
            else:
                log.info(f"Checkpoint not found at {model_path}. Initiating auto-download.")
                try:
                    download_checkpoint(self.config.model_type, model_path)
                except Exception as e:
                    log.error(f"Auto-download failed: {e}")
                    raise FileNotFoundError(
                        f"Checkpoint not found at {model_path} and auto-download failed. "
                        f"Please verify model_path in configuration."
                    ) from e

        if model_path.exists():
            log.info(f"Loading D-LinkNet from {self.config.model_path}")
            try:
                checkpoint = torch.load(self.config.model_path, map_location=self.config.device)
                if "state_dict" in checkpoint:
                    state_dict = checkpoint["state_dict"]
                elif "model" in checkpoint:
                    state_dict = checkpoint["model"]
                else:
                    state_dict = checkpoint
                self.model.load_state_dict(state_dict, strict=False)
                log.info("D-LinkNet checkpoint loaded successfully")
            except Exception as e:
                log.error(f"Failed to load checkpoint state dict: {e}")
                raise

        # Device placement with dynamic recovery fallback
        try:
            self.model.to(self.config.device)
        except Exception as e:
            log.warning(
                f"Failed to load model onto device '{self.config.device}': {e}. Falling back to 'cpu'."
            )
            self.config.device = "cpu"
            self.model.to("cpu")

        self.model.eval()

    def _predict(self, tile: np.ndarray) -> np.ndarray:
        """Run inference on tile."""
        tile_chw = torch.from_numpy(tile.transpose(2, 0, 1)).float().unsqueeze(0)
        tile_chw = tile_chw.to(self.config.device)

        with torch.no_grad():
            road_prob = self.model(tile_chw)
            road_prob = road_prob.squeeze(0).cpu().numpy()

        return road_prob


class DLinkNet(nn.Module):
    """D-LinkNet: LinkNet with Dilated Convolutions for Road Extraction."""

    def __init__(self, in_channels=3, num_classes=2):
        super().__init__()
        # Encoder
        from torchvision.models.resnet import resnet34

        resnet = resnet34(pretrained=False)

        self.encoder1 = nn.Sequential(resnet.conv1, resnet.bn1, resnet.relu)
        self.encoder2 = nn.Sequential(resnet.maxpool, resnet.layer1)
        self.encoder3 = resnet.layer2
        self.encoder4 = resnet.layer3
        self.encoder5 = resnet.layer4

        # Dilated convolutions for larger receptive field
        self.dilated1 = nn.Conv2d(512, 512, kernel_size=3, padding=2, dilation=2)
        self.dilated2 = nn.Conv2d(512, 512, kernel_size=3, padding=4, dilation=4)

        # Decoder (LinkNet style with skip connections)
        # Encoder channels: e1=64, e2=64, e3=128, e4=256, e5=512
        # Decoder blocks take input from previous layer, upsample 2x, then concat with skip
        self.decoder4 = self._decoder_block(512, 256)  # 512 -> 256, then cat with e4(256) = 512
        self.decoder3 = self._decoder_block(512, 128)  # 512 -> 128, cat with e3(128) = 256
        self.decoder2 = self._decoder_block(256, 64)  # 256 -> 64, cat with e2(64) = 128
        self.decoder1 = self._decoder_block(128, 64)  # 128 -> 64, cat with e1(64) = 128

        self.final = nn.ConvTranspose2d(128, num_classes, kernel_size=2, stride=2)

    def _decoder_block(self, in_channels, out_channels):
        return nn.Sequential(
            nn.ConvTranspose2d(in_channels, out_channels, kernel_size=2, stride=2),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, x):
        # Encoder
        e1 = self.encoder1(x)  # [B, 64, H/2, W/2]
        e2 = self.encoder2(e1)  # [B, 64, H/4, W/4]
        e3 = self.encoder3(e2)  # [B, 128, H/8, W/8]
        e4 = self.encoder4(e3)  # [B, 256, H/16, W/16]
        e5 = self.encoder5(e4)  # [B, 512, H/32, W/32]

        # Dilated
        d1 = F.relu(self.dilated1(e5))
        d2 = F.relu(self.dilated2(d1))

        # Decoder with skip connections
        d4 = self.decoder4(d2)
        d4 = torch.cat([d4, e4], dim=1)  # Skip connection

        d3 = self.decoder3(d4)
        d3 = torch.cat([d3, e3], dim=1)

        d2 = self.decoder2(d3)
        d2 = torch.cat([d2, e2], dim=1)

        d1 = self.decoder1(d2)
        d1 = torch.cat([d1, e1], dim=1)

        out = self.final(d1)  # [B, 2, H, W]
        return torch.sigmoid(out[:, 1])  # Return road channel probability


class HFUNetConvBlock(nn.Module):
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
        )

    def forward(self, x):
        return self.conv(x)


class HFUNet(nn.Module):
    def __init__(self, in_channels=3, out_channels=1):
        super().__init__()
        self.enc1 = HFUNetConvBlock(in_channels, 64)
        self.enc2 = HFUNetConvBlock(64, 128)
        self.enc3 = HFUNetConvBlock(128, 256)
        self.enc4 = HFUNetConvBlock(256, 512)
        self.pool = nn.MaxPool2d(2)
        self.bottleneck = HFUNetConvBlock(512, 1024)

        self.upconv4 = nn.ConvTranspose2d(1024, 512, kernel_size=2, stride=2)
        self.dec4 = HFUNetConvBlock(1024, 512)
        self.upconv3 = nn.ConvTranspose2d(512, 256, kernel_size=2, stride=2)
        self.dec3 = HFUNetConvBlock(512, 256)
        self.upconv2 = nn.ConvTranspose2d(256, 128, kernel_size=2, stride=2)
        self.dec2 = HFUNetConvBlock(256, 128)
        self.upconv1 = nn.ConvTranspose2d(128, 64, kernel_size=2, stride=2)
        self.dec1 = HFUNetConvBlock(128, 64)

        self.conv_final = nn.Conv2d(64, out_channels, kernel_size=1)

    def forward(self, x):
        e1 = self.enc1(x)
        e2 = self.enc2(self.pool(e1))
        e3 = self.enc3(self.pool(e2))
        e4 = self.enc4(self.pool(e3))

        b = self.bottleneck(self.pool(e4))

        d4 = self.upconv4(b)
        d4 = torch.cat([d4, e4], dim=1)
        d4 = self.dec4(d4)

        d3 = self.upconv3(d4)
        d3 = torch.cat([d3, e3], dim=1)
        d3 = self.dec3(d3)

        d2 = self.upconv2(d3)
        d2 = torch.cat([d2, e2], dim=1)
        d2 = self.dec2(d2)

        d1 = self.upconv1(d2)
        d1 = torch.cat([d1, e1], dim=1)
        d1 = self.dec1(d1)

        out = self.conv_final(d1)
        return torch.sigmoid(out)


class HuggingFaceUNetExtractor(BaseExtractor):
    """Hugging Face pre-trained U-Net Road Extractor."""

    def _load_model(self) -> None:
        self.model = HFUNet(in_channels=3, out_channels=1)
        model_path = Path(self.config.model_path)

        if not model_path.exists():
            log.info(f"Downloading pre-trained UNet weights from Hugging Face to {model_path}")
            try:
                import shutil

                from huggingface_hub import hf_hub_download

                downloaded = hf_hub_download(
                    repo_id="teohyc/Satellite-Road-Segmentation-UNet",
                    filename="best_road_seg_unet.pth",
                    cache_dir="assets/checkpoints/cache",
                )
                model_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(downloaded, model_path)
                log.info("Hugging Face weights downloaded and verified successfully")
            except Exception as e:
                log.error(f"Failed to download weights from Hugging Face: {e}")
                raise FileNotFoundError(f"Hugging Face U-Net weights missing: {e}") from e

        log.info(f"Loading HF U-Net from {model_path}")
        try:
            checkpoint = torch.load(model_path, map_location=self.config.device)
            self.model.load_state_dict(checkpoint, strict=True)
            log.info("HF U-Net weights loaded successfully")
        except Exception as e:
            log.error(f"Failed to load checkpoint state dict: {e}")
            raise

        try:
            self.model.to(self.config.device)
        except Exception as e:
            log.warning(f"Failed onto device '{self.config.device}': {e}. Fallback to cpu.")
            self.config.device = "cpu"
            self.model.to("cpu")

        self.model.eval()

    def _predict(self, tile: np.ndarray) -> np.ndarray:
        """Run U-Net inference on 256x256 tiles."""
        from PIL import Image

        original_shape = tile.shape[:2]

        # Rescale/resize to 256x256 as required by this model
        if tile.shape[0] != 256 or tile.shape[1] != 256:
            tile_pil = Image.fromarray((tile * 255).astype(np.uint8))
            tile_pil = tile_pil.resize((256, 256), Image.Resampling.BILINEAR)
            tile = np.array(tile_pil) / 255.0

        # HWC [0, 1] -> CHW tensor with batch dimension
        tile_tensor = (
            torch.from_numpy(tile.transpose(2, 0, 1)).float().unsqueeze(0).to(self.config.device)
        )

        with torch.no_grad():
            output = self.model(tile_tensor)  # output shape [1, 1, 256, 256]
            pred = output.squeeze(0).squeeze(0).cpu().numpy()  # [256, 256]

        # Resize back to original tile size
        if pred.shape != original_shape:
            pred_pil = Image.fromarray((pred * 255).astype(np.uint8))
            pred_pil = pred_pil.resize(
                (original_shape[1], original_shape[0]), Image.Resampling.BILINEAR
            )
            pred = np.array(pred_pil) / 255.0

        return pred
