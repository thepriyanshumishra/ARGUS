"""ARGUS FastAPI backend — road graph extraction endpoint."""

from __future__ import annotations

import base64
import io
import logging
import os
from collections import deque

import cv2
import networkx as nx
import numpy as np
import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from PIL import Image
from pydantic import BaseModel
from skimage.morphology import skeletonize

logger = logging.getLogger("argus.api")

app = FastAPI(
    title="ARGUS API",
    description="Backend API for the ARGUS web application.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Response schema
# ---------------------------------------------------------------------------


class NodePoint(BaseModel):
    x: float
    y: float


class EdgeSegment(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


class GraphResponse(BaseModel):
    nodes: list[NodePoint]
    edges: list[EdgeSegment]
    imgWidth: int
    imgHeight: int
    nodeCount: int
    edgeCount: int
    maskB64: str | None = None
    skeletonB64: str | None = None


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy", "version": "0.2.0"}


# ---------------------------------------------------------------------------
# Pure-numpy skeleton graph builder (replaces sknw, no LLVM/numba needed)
# ---------------------------------------------------------------------------

# 8-connectivity neighbour offsets: (dy, dx)
_NEIGHBORS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def _count_neighbors(skel: np.ndarray, r: int, c: int) -> int:
    """Count skeleton pixels in the 8-neighbourhood of (r, c)."""
    h, w = skel.shape
    count = 0
    for dr, dc in _NEIGHBORS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < h and 0 <= nc < w and skel[nr, nc]:
            count += 1
    return count


def _find_junctions_and_tips(skel: np.ndarray) -> np.ndarray:
    """
    Return a boolean mask where pixel is a junction (≥3 neighbours)
    or a tip (exactly 1 neighbour).
    """
    rows, cols = np.where(skel)
    mask = np.zeros_like(skel, dtype=bool)
    for r, c in zip(rows, cols, strict=True):
        n = _count_neighbors(skel, r, c)
        if n == 1 or n >= 3:
            mask[r, c] = True
    return mask


def _skeleton_to_graph(skel: np.ndarray) -> tuple[nx.Graph, dict[int, tuple[int, int]]]:
    """
    Trace the skeleton into a NetworkX graph.

    Each junction/tip becomes a node; each run of non-junction pixels
    between two junctions becomes an edge with the full pixel path attached.

    Returns
    -------
    graph : nx.Graph
    node_coords : dict mapping node_id -> (col, row)  i.e. (x, y)
    """
    h, w = skel.shape
    junction_mask = _find_junctions_and_tips(skel)

    # Label each junction/tip with a unique node ID
    node_id_map: dict[tuple[int, int], int] = {}
    node_coords: dict[int, tuple[int, int]] = {}
    next_id = 0
    jr, jc = np.where(junction_mask)
    for r, c in zip(jr, jc, strict=True):
        node_id_map[(r, c)] = next_id
        node_coords[next_id] = (c, r)  # store as (x, y)
        next_id += 1

    graph = nx.Graph()
    for nid, (x, y) in node_coords.items():
        graph.add_node(nid, x=x, y=y)

    visited_edges: set[frozenset[int]] = set()

    # BFS from each junction to find connecting junctions
    for start_r, start_c in zip(jr, jc, strict=True):
        start_id = node_id_map[(start_r, start_c)]

        for dr, dc in _NEIGHBORS:
            nr, nc = start_r + dr, start_c + dc
            if not (0 <= nr < h and 0 <= nc < w and skel[nr, nc]):
                continue
            if (nr, nc) in node_id_map:
                # Immediate neighbour is also a junction: direct edge
                end_id = node_id_map[(nr, nc)]
                eid = frozenset((start_id, end_id))
                if eid not in visited_edges and start_id != end_id:
                    graph.add_edge(start_id, end_id, pts=[(start_c, start_r), (nc, nr)])
                    visited_edges.add(eid)
                continue

            # BFS along non-junction pixels until we hit another junction
            path: list[tuple[int, int]] = [(start_c, start_r), (nc, nr)]
            frontier: deque[tuple[int, int]] = deque([(nr, nc)])
            local_visited: set[tuple[int, int]] = {(start_r, start_c), (nr, nc)}
            found_junction: int | None = None

            while frontier:
                cr, cc = frontier.popleft()
                for dr2, dc2 in _NEIGHBORS:
                    er, ec = cr + dr2, cc + dc2
                    if not (0 <= er < h and 0 <= ec < w and skel[er, ec]):
                        continue
                    if (er, ec) in local_visited:
                        continue
                    local_visited.add((er, ec))
                    path.append((ec, er))
                    if (er, ec) in node_id_map:
                        found_junction = node_id_map[(er, ec)]
                        frontier.clear()
                        break
                    frontier.append((er, ec))

            if found_junction is not None:
                eid = frozenset((start_id, found_junction))
                if eid not in visited_edges and start_id != found_junction:
                    graph.add_edge(start_id, found_junction, pts=path)
                    visited_edges.add(eid)

    return graph, node_coords


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

_MAX_SIDE = 1024

try:
    from argus.core.types import RasterImage
    from argus.vision import HuggingFaceUNetExtractor, VisionConfig

    vision_config = VisionConfig(model_type="hf_unet", device="auto")
    extractor = HuggingFaceUNetExtractor(vision_config)
    logger.info("Successfully loaded pre-trained Hugging Face U-Net Road Extractor")
except Exception as e:
    logger.exception(
        f"Failed to load Hugging Face UNet Extractor: {e}. Fallback to OpenCV Canny is active."
    )
    extractor = None


def _extract_road_graph(
    img_bgr: np.ndarray, method: str = "classical"
) -> tuple[nx.Graph, dict[int, tuple[int, int]], int, int, np.ndarray, np.ndarray]:
    h, w = img_bgr.shape[:2]

    # 1. Resize to max side
    scale = min(_MAX_SIDE / max(h, w), 1.0)
    if scale < 1.0:
        new_w, new_h = int(w * scale), int(h * scale)
        img_bgr = cv2.resize(img_bgr, (new_w, new_h), interpolation=cv2.INTER_AREA)
        h, w = new_h, new_w

    # 2. Extract road mask
    binary = None
    if method == "ai" and extractor is not None:
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        raster = RasterImage(
            data=img_rgb,
            crs="EPSG:3857",
            transform=(1.0, 0.0, 0.0, 0.0, -1.0, 0.0),
            bounds=(0.0, 0.0, float(w), float(h)),
            metadata={},
        )
        try:
            road_mask = extractor.extract(raster)
            binary = road_mask.mask.astype(np.uint8)
        except Exception as e:
            logger.error(f"Inference failed: {e}. Falling back to OpenCV Canny.")
            binary = None

    if binary is None:
        # Fallback to classical OpenCV Canny if model is not loaded or fails
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        blurred = cv2.GaussianBlur(enhanced, (13, 13), 0)
        edges = cv2.Canny(blurred, threshold1=120, threshold2=240)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        dilated = cv2.dilate(edges, kernel, iterations=1)
        closed = cv2.morphologyEx(dilated, cv2.MORPH_CLOSE, kernel, iterations=1)
        binary = (closed > 0).astype(np.uint8)

    # 3. Skeletonize → 1-pixel wide centerlines
    skeleton = skeletonize(binary)

    # 4. Build graph from skeleton
    graph, node_coords = _skeleton_to_graph(skeleton)

    return graph, node_coords, w, h, binary, skeleton


def _graph_to_response(
    graph: nx.Graph,
    node_coords: dict[int, tuple[int, int]],
    img_w: int,
    img_h: int,
) -> GraphResponse:
    node_points = [NodePoint(x=float(x), y=float(y)) for x, y in node_coords.values()]

    edge_segments: list[EdgeSegment] = []
    for u, v, data in graph.edges(data=True):
        pts = data.get("path_pixels", [])
        if len(pts) >= 2:
            for i in range(len(pts) - 1):
                x1, y1 = pts[i]
                x2, y2 = pts[i + 1]
                edge_segments.append(
                    EdgeSegment(x1=float(x1), y1=float(y1), x2=float(x2), y2=float(y2))
                )
        elif u in node_coords and v in node_coords:
            x1, y1 = node_coords[u]
            x2, y2 = node_coords[v]
            edge_segments.append(
                EdgeSegment(x1=float(x1), y1=float(y1), x2=float(x2), y2=float(y2))
            )

    return GraphResponse(
        nodes=node_points,
        edges=edge_segments,
        imgWidth=img_w,
        imgHeight=img_h,
        nodeCount=len(node_points),
        edgeCount=graph.number_of_edges(),
    )


@app.post("/api/extract-graph", response_model=GraphResponse)
async def extract_graph(file: UploadFile = File(...), method: str = "classical") -> GraphResponse:
    """
    Accept a satellite image and return the extracted road graph.

    Pixel coordinates are relative to the (possibly downscaled) processing
    image. The frontend scales them to the rendered image dimensions.
    """
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=415, detail="Only image files are supported.")

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty file received.")

    # Save the raw file for debugging/diagnostic inspection
    try:
        with open("/tmp/last_uploaded.png", "wb") as f:
            f.write(raw)
        logger.info(f"Saved uploaded image to /tmp/last_uploaded.png, size: {len(raw)} bytes")
    except Exception as e:
        logger.warning(f"Failed to save temp file: {e}")

    try:
        pil_img = Image.open(io.BytesIO(raw)).convert("RGB")
        img_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Cannot decode image: {exc}") from exc

    try:
        graph, node_coords, img_w, img_h, mask, skel = _extract_road_graph(img_bgr, method=method)
    except Exception as exc:
        logger.exception("Road extraction pipeline failed")
        raise HTTPException(status_code=500, detail=f"Extraction failed: {exc}") from exc

    # Encode mask to base64 PNG
    _, mask_png = cv2.imencode(".png", (mask * 255).astype(np.uint8))
    mask_b64 = base64.b64encode(mask_png).decode("utf-8")

    # Encode skeleton to base64 PNG
    _, skel_png = cv2.imencode(".png", (skel * 255).astype(np.uint8))
    skel_b64 = base64.b64encode(skel_png).decode("utf-8")

    resp = _graph_to_response(graph, node_coords, img_w, img_h)
    resp.maskB64 = f"data:image/png;base64,{mask_b64}"
    resp.skeletonB64 = f"data:image/png;base64,{skel_b64}"
    return resp


class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/api/login")
def login(req: LoginRequest):
    expected_password = os.getenv("ARGUS_PASSWORD", "argus2026")
    if req.username == "admin" and req.password == expected_password:
        return {"status": "success", "token": "mock-token-2026"}
    raise HTTPException(status_code=401, detail="Invalid username or password")


# Mount React static files (only if the build folder exists)
frontend_dist_path = os.path.abspath("frontend/dist")
if os.path.exists(frontend_dist_path):
    app.mount("/", StaticFiles(directory=frontend_dist_path, html=True), name="frontend")


if __name__ == "__main__":
    uvicorn.run("argus.api.main:app", host="0.0.0.0", port=8000, reload=True)
