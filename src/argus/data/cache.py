"""Artifact caching for intermediate results."""

from __future__ import annotations

import hashlib
import json
import pickle
from pathlib import Path
from typing import Any

import geopandas as gpd
import networkx as nx
import numpy as np

from argus.core.config import load_config
from argus.core.logging import get_logger
from argus.core.types import (
    RasterImage,
    RoadGraph,
)

log = get_logger(__name__)


def calculate_array_hash(data: np.ndarray) -> str:
    """Calculate SHA256 checksum of an array's bytes."""
    return hashlib.sha256(data.tobytes()).hexdigest()


class ArtifactCache:
    """Cache intermediate artifacts to disk."""

    def __init__(self, cache_dir: Path | None = None):
        if cache_dir is None:
            config = load_config("data")
            cache_dir = (
                Path(config.cache_dir) if hasattr(config, "cache_dir") else Path(".cache/argus")
            )
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_path(self, key: str, format: str) -> Path:
        return self.cache_dir / f"{key}.{format}"

    def save(self, key: str, data: Any, format: str = "pickle", source_hash: str | None = None) -> Path:
        """Save an artifact to cache."""
        path = self._get_path(key, format)
        log.debug(f"Caching {key} to {path}")

        if format == "pickle":
            with open(path, "wb") as f:
                pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
        elif format == "json":
            with open(path, "w") as f:
                json.dump(data, f, indent=2, default=str)
        elif format == "npy":
            np.save(path, data)
        elif format == "geojson":
            if isinstance(data, gpd.GeoDataFrame):
                data.to_file(path, driver="GeoJSON")
            else:
                raise ValueError("geojson format requires GeoDataFrame")
        elif format == "graphml":
            if isinstance(data, RoadGraph):
                nx.write_graphml(data.graph, path)
            elif isinstance(data, nx.MultiDiGraph):
                nx.write_graphml(data, path)
            else:
                raise ValueError("graphml format requires RoadGraph or MultiDiGraph")
        elif format == "npz":
            # For RasterImage: save array + metadata
            if isinstance(data, RasterImage):
                metadata = dict(data.metadata)
                # Auto-calculate and store data hash
                img_hash = source_hash or calculate_array_hash(data.data)
                metadata["_data_hash"] = img_hash
                np.savez_compressed(
                    path,
                    data=data.data,
                    crs=data.crs,
                    transform=np.array(data.transform),
                    bounds=np.array(data.bounds),
                    metadata=json.dumps(metadata),
                )
            else:
                raise ValueError("npz format expects RasterImage")
        else:
            raise ValueError(f"Unknown format: {format}")

        return path

    def load(self, key: str, format: str = "pickle", expected_hash: str | None = None) -> Any:
        """Load an artifact from cache, optionally verifying its checksum."""
        path = self._get_path(key, format)
        if not path.exists():
            raise FileNotFoundError(f"Cache miss: {path}")

        log.debug(f"Loading {key} from {path}")

        if format == "pickle":
            with open(path, "rb") as f:
                return pickle.load(f)
        elif format == "json":
            with open(path) as f:
                return json.load(f)
        elif format == "npy":
            return np.load(path)
        elif format == "geojson":
            return gpd.read_file(path)
        elif format == "graphml":
            graph = nx.read_graphml(path)
            return graph
        elif format == "npz":
            npz_data = np.load(path, allow_pickle=True)
            meta_str = str(npz_data["metadata"])
            metadata = json.loads(meta_str) if meta_str else {}
            
            if expected_hash and metadata.get("_data_hash") != expected_hash:
                raise FileNotFoundError(f"Cache hash validation failed for {key}")

            return RasterImage(
                data=npz_data["data"],
                crs=str(npz_data["crs"]),
                transform=tuple(npz_data["transform"].tolist()),
                bounds=tuple(npz_data["bounds"].tolist()),
                metadata=metadata,
            )
        else:
            raise ValueError(f"Unknown format: {format}")

    def load_road_graph(self, key: str, expected_hash: str | None = None) -> RoadGraph:
        """Load a RoadGraph from graphml + metadata, optionally verifying its checksum."""
        graph_path = self._get_path(key, "graphml")
        meta_path = self._get_path(key, "json")

        if not graph_path.exists():
            raise FileNotFoundError(f"Cache miss: {graph_path}")

        if meta_path.exists():
            with open(meta_path) as f:
                meta = json.load(f)
        else:
            meta = {"crs": "EPSG:4326", "bounds": [0.0, 0.0, 1.0, 1.0]}

        if expected_hash and meta.get("_source_hash") != expected_hash:
            raise FileNotFoundError(f"Cache validation failed for {key}: source hash mismatch")

        graph = nx.read_graphml(graph_path)
        mgraph = nx.MultiDiGraph(graph)

        bounds_val = meta.get("bounds", [0.0, 0.0, 1.0, 1.0])
        return RoadGraph(
            graph=mgraph,
            crs=str(meta.get("crs", "EPSG:4326")),
            bounds=(
                float(bounds_val[0]),
                float(bounds_val[1]),
                float(bounds_val[2]),
                float(bounds_val[3]),
            ),
            metadata=meta.get("metadata", {}) if isinstance(meta.get("metadata"), dict) else {},
        )

    def save_road_graph(self, key: str, road_graph: RoadGraph, source_hash: str | None = None) -> tuple[Path, Path]:
        """Save a RoadGraph as graphml + metadata json."""
        graph_path = self._get_path(key, "graphml")
        meta_path = self._get_path(key, "json")

        nx.write_graphml(road_graph.graph, graph_path)

        meta = {
            "crs": road_graph.crs,
            "bounds": list(road_graph.bounds),
            "metadata": road_graph.metadata,
        }
        if source_hash:
            meta["_source_hash"] = source_hash

        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)

        return graph_path, meta_path

    def exists(self, key: str, format: str = "pickle") -> bool:
        """Check if artifact exists in cache."""
        return self._get_path(key, format).exists()

    def clear(self, key: str | None = None) -> None:
        """Clear cache (all or specific key)."""
        if key is None:
            for f in self.cache_dir.glob("*"):
                f.unlink()
        else:
            for ext in ["pickle", "json", "npy", "geojson", "graphml", "npz"]:
                path = self.cache_dir / f"{key}.{ext}"
                if path.exists():
                    path.unlink()
