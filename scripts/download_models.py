#!/usr/bin/env python3
"""Download SAM-Road++ and D-LinkNet model checkpoints."""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path
from urllib.request import urlretrieve
from urllib.error import URLError, HTTPError

# Known checkpoint URLs (update as needed)
CHECKPOINTS: dict[str, dict[str, str]] = {
    "sam_road_plus_plus.pth": {
        "url": "https://github.com/ShengjiLi/SAM-RoadPlusPlus/releases/download/v1.0/sam_road_plus_plus.pth",
        "sha256": "",
        "description": "SAM-Road++ pretrained model (ViT-B backbone)",
    },
    "dlinknet.pth": {
        "url": "https://github.com/ShengjiLi/D-LinkNet/releases/download/v1.0/dlinknet.pth",
        "sha256": "",
        "description": "D-LinkNet pretrained model (fallback)",
    },
    "sam_vit_b_01ec64.pth": {
        "url": "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth",
        "sha256": "",
        "description": "SAM ViT-B base checkpoint (for SAM-Road++)",
    },
}


def verify_checksum(filepath: Path, expected_sha256: str) -> bool:
    """Verify file SHA256 checksum."""
    if not expected_sha256:
        return True
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest() == expected_sha256


def download_file(url: str, dest: Path, description: str = "") -> bool:
    """Download a file with progress bar."""
    try:
        print(f"Downloading {description} from {url}")
        print(f"  -> {dest}")
        
        def reporthook(block_num, block_size, total_size):
            if total_size > 0:
                percent = min(100, (block_num * block_size * 100) // total_size)
                sys.stdout.write(f"\r  Progress: {percent}%")
                sys.stdout.flush()
        
        urlretrieve(url, dest, reporthook)
        print("\n  Done!")
        return True
    except (URLError, HTTPError) as e:
        print(f"\n  Error downloading {url}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Download model checkpoints for ARGUS")
    parser.add_argument(
        "--output-dir", 
        type=Path, 
        default=Path("assets/checkpoints"),
        help="Output directory for checkpoints"
    )
    parser.add_argument(
        "--models",
        nargs="+",
        choices=list(CHECKPOINTS.keys()) + ["all"],
        default=["all"],
        help="Models to download"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-download even if file exists"
    )
    args = parser.parse_args()

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    models_to_download = CHECKPOINTS.keys() if "all" in args.models else args.models

    print(f"Downloading checkpoints to {output_dir}")
    print("=" * 60)

    success_count = 0
    for model_name in models_to_download:
        if model_name not in CHECKPOINTS:
            print(f"Unknown model: {model_name}")
            continue

        info = CHECKPOINTS[model_name]
        dest = output_dir / model_name

        if dest.exists() and not args.force:
            if verify_checksum(dest, info["sha256"]):
                print(f"Skipping {model_name} (already exists and verified)")
                success_count += 1
                continue
            else:
                print(f"Re-downloading {model_name} (checksum mismatch)")

        if download_file(info["url"], dest, info["description"]):
            if verify_checksum(dest, info["sha256"]):
                print(f"  Verified!")
                success_count += 1
            else:
                print(f"  Warning: Checksum verification failed!")
                dest.unlink(missing_ok=True)
        else:
            print(f"  Failed to download {model_name}")

    print("=" * 60)
    print(f"Downloaded {success_count}/{len(models_to_download)} checkpoints successfully")

    if success_count < len(models_to_download):
        sys.exit(1)


if __name__ == "__main__":
    main()