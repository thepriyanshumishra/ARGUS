"""Dashboard Engine — Streamlit interactive UI for ARGUS M7.

Displays road network, criticality analysis, simulation impact,
route comparison, accessibility, and exports.
"""

from __future__ import annotations

import os
# Force Arrow to use system memory allocator instead of mimalloc to prevent SIGSEGV crashes on macOS threads
os.environ["ARROW_DEFAULT_MEMORY_POOL"] = "system"

import io
import json
import tempfile
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import streamlit as st
from omegaconf import OmegaConf

from argus.core.logging import get_logger

log = get_logger(__name__)

def _find_project_root() -> Path:
    """Walk up from this file to find the project root (contains configs/)."""
    candidate = Path(__file__).resolve().parent
    for _ in range(6):  # max 6 levels up
        if (candidate / "configs" / "dashboard.yaml").exists():
            return candidate
        candidate = candidate.parent
    # Fallback: cwd
    return Path.cwd()


_PROJECT_ROOT = _find_project_root()
_DASHBOARD_CFG_PATH = _PROJECT_ROOT / "configs" / "dashboard.yaml"

try:
    _dashboard_cfg = OmegaConf.load(str(_DASHBOARD_CFG_PATH))
except Exception:
    # Fallback: minimal in-memory config so the app never shows a blank screen
    from omegaconf import DictConfig
    _dashboard_cfg = OmegaConf.create({
        "streamlit": {"page_title": "ARGUS", "page_icon": "🛰️", "layout": "wide", "initial_sidebar_state": "expanded"},
        "map": {"default_center": [12.97, 77.59], "default_zoom": 12},
        "layers": {
            "road_color": [0, 100, 200],
            "critical_node_color": [255, 0, 0],
            "route_color": [0, 200, 0],
            "flood_color": [0, 0, 255, 100],
        },
    })


st.set_page_config(
    page_title="ARGUS — Urban Mobility Resilience",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Demo data paths — absolute so they work regardless of cwd
DEMO_DATA: dict[str, str] = {
    "graph": str(_PROJECT_ROOT / "assets" / "samples" / "demo_graph.pkl"),
    "criticality": str(_PROJECT_ROOT / "assets" / "samples" / "demo_criticality.pkl"),
    "simulation": str(_PROJECT_ROOT / "assets" / "samples" / "demo_simulation.pkl"),
    "route": str(_PROJECT_ROOT / "assets" / "samples" / "demo_route.pkl"),
}

# ---------------------------------------------------------------------------
# PREMIUM STYLES — injected once at startup
# ---------------------------------------------------------------------------

def _inject_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

        /* ── global reset ─────────────────────────────────────────── */
        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        /* Remove Streamlit top padding */
        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 2rem !important;
        }

        /* ── sidebar ──────────────────────────────────────────────── */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0d1117 0%, #161b22 100%);
            border-right: 1px solid #30363d;
        }
        [data-testid="stSidebar"] * {
            color: #e6edf3 !important;
        }
        [data-testid="stSidebar"] .stMarkdown h1,
        [data-testid="stSidebar"] .stMarkdown h2,
        [data-testid="stSidebar"] .stMarkdown h3 {
            color: #f0f6fc !important;
            font-weight: 700;
        }

        /* Sidebar section dividers */
        [data-testid="stSidebar"] hr {
            border-color: #30363d !important;
            margin: 12px 0 !important;
        }

        /* Custom styling for sidebar expanders */
        [data-testid="stSidebar"] [data-testid="stExpander"] {
            background: #161b22 !important;
            border: 1px solid #30363d !important;
            border-radius: 10px !important;
            margin-bottom: 8px !important;
        }
        [data-testid="stSidebar"] [data-testid="stExpander"] details {
            border: none !important;
            background: transparent !important;
        }
        [data-testid="stSidebar"] [data-testid="stExpander"] summary {
            font-size: 0.82rem !important;
            font-weight: 700 !important;
            letter-spacing: 0.03em;
            text-transform: uppercase;
            color: #58a6ff !important;
            background: transparent !important;
            padding: 8px 12px !important;
        }
        [data-testid="stSidebar"] [data-testid="stExpander"] summary:hover {
            color: #79c0ff !important;
        }
        [data-testid="stSidebar"] [data-testid="stExpander"] [data-testid="stExpanderDetails"] {
            padding: 12px !important;
            background: transparent !important;
        }

        /* Sidebar buttons */
        [data-testid="stSidebar"] .stButton > button {
            background: #238636 !important;
            color: #ffffff !important;
            border: 1px solid #2ea043 !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            font-size: 0.82rem !important;
            padding: 6px 14px !important;
            width: 100% !important;
            transition: background 0.15s, transform 0.1s !important;
            box-shadow: none !important;
        }
        [data-testid="stSidebar"] .stButton > button:hover {
            background: #2ea043 !important;
            transform: translateY(-1px) !important;
        }

        /* Sidebar select/slider labels */
        [data-testid="stSidebar"] label {
            color: #8b949e !important;
            font-size: 0.78rem !important;
            font-weight: 500 !important;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }

        /* Sidebar text inputs */
        [data-testid="stSidebar"] input[type="text"] {
            background: #161b22 !important;
            border: 1px solid #30363d !important;
            border-radius: 8px !important;
            color: #e6edf3 !important;
            font-size: 0.85rem !important;
        }

        /* File uploader in sidebar */
        [data-testid="stSidebar"] [data-testid="stFileUploader"] {
            background: #161b22 !important;
            border: 1px dashed #30363d !important;
            border-radius: 10px !important;
        }

        /* ── main content area ────────────────────────────────────── */
        .main .block-container {
            background: #f6f8fa;
        }

        /* ── hero header ──────────────────────────────────────────── */
        .argus-hero {
            background: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #0d1117 100%);
            border-radius: 16px;
            padding: 36px 40px;
            margin-bottom: 24px;
            border: 1px solid #30363d;
            position: relative;
            overflow: hidden;
        }
        .argus-hero::before {
            content: '';
            position: absolute;
            top: -40%;
            right: -10%;
            width: 400px;
            height: 400px;
            background: radial-gradient(circle, rgba(56,139,253,0.15) 0%, transparent 70%);
            pointer-events: none;
        }
        .argus-hero-title {
            font-size: 2rem;
            font-weight: 800;
            color: #f0f6fc;
            margin: 0 0 6px 0;
            letter-spacing: -0.03em;
            line-height: 1.2;
        }
        .argus-hero-sub {
            font-size: 0.95rem;
            color: #8b949e;
            margin: 0;
            font-weight: 400;
        }
        .argus-badge {
            display: inline-block;
            background: rgba(56,139,253,0.15);
            border: 1px solid rgba(56,139,253,0.4);
            color: #58a6ff;
            border-radius: 20px;
            padding: 3px 12px;
            font-size: 0.72rem;
            font-weight: 600;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            margin-bottom: 12px;
        }

        /* ── stat cards ───────────────────────────────────────────── */
        .stat-card {
            background: #ffffff;
            border: 1px solid #d0d7de;
            border-radius: 12px;
            padding: 20px 22px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.06);
            transition: box-shadow 0.2s, transform 0.2s;
        }
        .stat-card:hover {
            box-shadow: 0 8px 24px rgba(0,0,0,0.1);
            transform: translateY(-2px);
        }
        .stat-label {
            font-size: 0.72rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.07em;
            color: #57606a;
            margin-bottom: 6px;
        }
        .stat-value {
            font-size: 1.75rem;
            font-weight: 800;
            color: #0d1117;
            letter-spacing: -0.03em;
            line-height: 1;
        }
        .stat-sub {
            font-size: 0.75rem;
            color: #8b949e;
            margin-top: 4px;
        }
        .stat-icon {
            font-size: 1.4rem;
            margin-bottom: 8px;
        }

        /* ── tabs ─────────────────────────────────────────────────── */
        div[data-testid="stTabBar"] {
            background: transparent;
            border-bottom: 2px solid #d0d7de;
            gap: 0;
            margin-bottom: 28px;
        }
        button[data-baseweb="tab"] {
            background: transparent !important;
            border: none !important;
            border-bottom: 3px solid transparent !important;
            padding: 10px 20px !important;
            font-size: 0.88rem !important;
            font-weight: 600 !important;
            color: #57606a !important;
            border-radius: 0 !important;
            transition: color 0.15s, border-color 0.15s !important;
            margin-bottom: -2px;
        }
        button[data-baseweb="tab"]:hover {
            color: #0d1117 !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            color: #0969da !important;
            border-bottom-color: #0969da !important;
        }
        div[data-baseweb="tab-highlight"] {
            display: none !important;
        }

        /* ── main page buttons ────────────────────────────────────── */
        .main .stButton > button {
            background: #0969da !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            font-size: 0.88rem !important;
            padding: 8px 20px !important;
            transition: background 0.15s, transform 0.1s, box-shadow 0.15s !important;
            box-shadow: 0 1px 3px rgba(9,105,218,0.3) !important;
        }
        .main .stButton > button:hover {
            background: #0860ca !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 12px rgba(9,105,218,0.35) !important;
        }

        /* ── section headers ──────────────────────────────────────── */
        .section-header {
            font-size: 1.1rem;
            font-weight: 700;
            color: #0d1117;
            padding-bottom: 10px;
            border-bottom: 2px solid #eaecef;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        /* ── info / alert boxes ───────────────────────────────────── */
        div[data-testid="stAlert"] {
            border-radius: 10px !important;
            border: 1px solid !important;
            font-size: 0.88rem !important;
        }

        /* ── metrics ──────────────────────────────────────────────── */
        div[data-testid="metric-container"] {
            background: #ffffff;
            border: 1px solid #d0d7de;
            border-radius: 12px;
            padding: 18px 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        div[data-testid="metric-container"] label {
            font-size: 0.72rem !important;
            font-weight: 700 !important;
            text-transform: uppercase;
            letter-spacing: 0.07em;
            color: #57606a !important;
        }
        div[data-testid="metric-container"] [data-testid="stMetricValue"] {
            font-size: 1.65rem !important;
            font-weight: 800 !important;
            color: #0d1117 !important;
            letter-spacing: -0.03em !important;
        }

        /* ── dataframe ────────────────────────────────────────────── */
        div[data-testid="stDataFrameContainer"] {
            border-radius: 10px !important;
            border: 1px solid #d0d7de !important;
            overflow: hidden;
        }

        /* ── map iframes ──────────────────────────────────────────── */
        iframe {
            border-radius: 12px !important;
            border: 1px solid #d0d7de !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.06) !important;
        }

        /* ── status chips ─────────────────────────────────────────── */
        .status-chip {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }
        .chip-green  { background: #dafbe1; color: #1a7f37; border: 1px solid #aceebb; }
        .chip-orange { background: #fff1e5; color: #bc4c00; border: 1px solid #ffc680; }
        .chip-red    { background: #ffebe9; color: #cf222e; border: 1px solid #ff8182; }
        .chip-blue   { background: #ddf4ff; color: #0969da; border: 1px solid #80ccff; }

        /* ── comparison banner ────────────────────────────────────── */
        .compare-banner {
            background: #fff8c5;
            border: 1px solid #d4a72c;
            border-radius: 10px;
            padding: 12px 18px;
            font-size: 0.88rem;
            font-weight: 500;
            color: #633c01;
            margin-bottom: 20px;
        }

        /* ── pipeline progress bar ────────────────────────────────── */
        .pipeline-steps {
            display: flex;
            align-items: center;
            gap: 0;
            margin-bottom: 24px;
        }
        .pipeline-step {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 0.75rem;
            font-weight: 600;
            color: #57606a;
        }
        .pipeline-step.done { color: #1a7f37; }
        .pipeline-step.active { color: #0969da; }
        .pipeline-dot {
            width: 10px; height: 10px;
            border-radius: 50%;
            background: #d0d7de;
        }
        .pipeline-dot.done   { background: #1a7f37; }
        .pipeline-dot.active { background: #0969da; }
        .pipeline-line {
            flex: 1; height: 2px;
            background: #d0d7de;
            max-width: 32px;
        }
        .pipeline-line.done { background: #1a7f37; }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------------------------

def _init_session_state() -> None:
    defaults = {
        "graph": None,
        "criticality_result": None,
        "simulation_result": None,
        "route_result": None,
        "route_comparison": None,
        "route_modified_result": None,
        "route_accessibility": None,
        "graph_source": None,
        "simulation_source": None,
        "uploaded_image_bytes": None,
        "uploaded_image_name": None,
        "extracted_mask": None,
        "extracted_road_mask_obj": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ---------------------------------------------------------------------------
# PIPELINE STATUS HELPERS
# ---------------------------------------------------------------------------

def _pipeline_status() -> dict[str, bool]:
    return {
        "graph": st.session_state.get("graph") is not None,
        "criticality": st.session_state.get("criticality_result") is not None,
        "simulation": st.session_state.get("simulation_result") is not None,
        "routing": st.session_state.get("route_result") is not None,
    }


def _render_pipeline_bar() -> None:
    s = _pipeline_status()
    steps = [
        ("Graph", s["graph"]),
        ("Analysis", s["criticality"]),
        ("Simulation", s["simulation"]),
        ("Routing", s["routing"]),
    ]
    done_list = [v for _, v in steps]
    parts = []
    for i, (label, done) in enumerate(steps):
        dot_cls = "done" if done else ("active" if (i == 0 or done_list[i - 1]) and not done else "")
        step_cls = "done" if done else ("active" if dot_cls == "active" else "")
        icon = "✓" if done else "○"
        parts.append(
            f'<div class="pipeline-step {step_cls}">'
            f'  <div class="pipeline-dot {dot_cls}"></div>{icon} {label}'
            f'</div>'
        )
        if i < len(steps) - 1:
            line_cls = "done" if done else ""
            parts.append(f'<div class="pipeline-line {line_cls}"></div>')
    st.markdown(f'<div class="pipeline-steps">{"".join(parts)}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# MAIN ENTRY
# ---------------------------------------------------------------------------

def run_dashboard() -> None:
    """Main dashboard entry point."""
    _inject_styles()
    _init_session_state()
    _render_sidebar()

    # Hero header
    g = st.session_state.get("graph")
    status_badge = '<span class="argus-badge">🟢 Active</span>' if g else '<span class="argus-badge">⚪ No Data</span>'
    st.markdown(
        f"""
        <div class="argus-hero">
            {status_badge}
            <div class="argus-hero-title">🛰️ ARGUS — Urban Mobility Resilience</div>
            <div class="argus-hero-sub">
                Satellite-to-Route intelligence · Road network criticality · Disaster simulation · Adaptive routing
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _render_pipeline_bar()

    tab_p, tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🛰️ Image Processor",
        "🏠 Overview",
        "🗺️ Road Network",
        "📊 Criticality",
        "📋 Report",
        "🌊 Simulation",
        "🛣️ Routing",
    ])

    with tab_p:
        _tab_image_processor()
    with tab0:
        _tab_overview()
    with tab1:
        _tab_road_network()
    with tab2:
        _tab_criticality()
    with tab3:
        _tab_report()
    with tab4:
        _tab_simulation()
    with tab5:
        _tab_routing()


# ---------------------------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------------------------

def _render_sidebar() -> None:
    with st.sidebar:
        st.markdown(
            """
            <div style="padding: 20px 4px 16px 4px;">
                <div style="font-size:1.2rem;font-weight:800;color:#f0f6fc;letter-spacing:-0.02em;">
                    🛰️ ARGUS
                </div>
                <div style="font-size:0.72rem;color:#8b949e;font-weight:500;margin-top:2px;letter-spacing:0.04em;text-transform:uppercase;">
                    Pipeline Controls
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── Quick Load ──────────────────────────────────────────────────
        with st.expander("⚡  Quick Load Demo", expanded=True):
            _sidebar_quick_load()

        # ── Step 1: Graph ───────────────────────────────────────────────
        with st.expander("📂  Step 1 — Load Graph", expanded=True):
            _sidebar_graph_loader()

        st.markdown("<hr>", unsafe_allow_html=True)

        # ── Step 2: Analyze ─────────────────────────────────────────────
        with st.expander("🔍  Step 2 — Criticality Analysis"):
            _sidebar_analysis_trigger()

        # ── Step 3: Simulate ────────────────────────────────────────────
        with st.expander("🌊  Step 3 — Disaster Simulation"):
            _sidebar_simulation()

        # ── Step 4: Route ───────────────────────────────────────────────
        with st.expander("🛣️  Step 4 — Routing"):
            _sidebar_routing()

        st.markdown("<hr>", unsafe_allow_html=True)

        # ── Step 5: Export ──────────────────────────────────────────────
        with st.expander("📤  Export All Results"):
            _sidebar_exports()

        # ── Footer ──────────────────────────────────────────────────────
        s = _pipeline_status()
        done_count = sum(s.values())
        st.markdown(
            f"""
            <div style="margin-top:24px;padding:12px 14px;background:#161b22;border:1px solid #30363d;
                        border-radius:10px;font-size:0.75rem;color:#8b949e;text-align:center;">
                Pipeline: <span style="color:#58a6ff;font-weight:700;">{done_count}/4</span> stages ready
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# SIDEBAR — QUICK LOAD
# ---------------------------------------------------------------------------

def _sidebar_quick_load() -> None:
    if st.button("▶ Load Demo Dataset", use_container_width=True):
        with st.spinner("Loading pre-computed demo data..."):
            _load_demo_data()
        st.success("Demo ready — explore the tabs!")
        st.rerun()


def _load_demo_data() -> None:
    import pickle

    from argus.graph.export import load_pickle

    for key, path in DEMO_DATA.items():
        p = Path(path)
        if not p.exists():
            continue
        if key == "graph":
            st.session_state["graph"] = load_pickle(p)
            st.session_state["graph_source"] = "demo_graph.pkl"
        elif key == "criticality":
            with open(p, "rb") as f:
                st.session_state["criticality_result"] = pickle.load(f)
        elif key == "simulation":
            with open(p, "rb") as f:
                st.session_state["simulation_result"] = pickle.load(f)
            st.session_state["simulation_source"] = "flood_zone_a"
        elif key == "route":
            with open(p, "rb") as f:
                st.session_state["route_result"] = pickle.load(f)


# ---------------------------------------------------------------------------
# SIDEBAR — GRAPH LOADER
# ---------------------------------------------------------------------------

def _sidebar_graph_loader() -> None:
    mode = st.radio("Load Mode", ["Pre-computed Graph (.pkl)", "Process Satellite Image"], key="load_mode_radio")
    
    if mode == "Pre-computed Graph (.pkl)":
        uploaded = st.file_uploader(
            "Upload graph (.pkl)",
            type=["pkl", "pickle"],
            key="graph_uploader",
            label_visibility="collapsed",
        )
        if uploaded is not None:
            with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as tmp:
                tmp.write(uploaded.read())
                tmp.flush()
                from argus.graph.export import load_pickle

                # Reset all previous results when a new graph is loaded
                st.session_state["criticality_result"] = None
                st.session_state["simulation_result"] = None
                st.session_state["route_result"] = None
                st.session_state["route_comparison"] = None
                st.session_state["route_modified_result"] = None
                st.session_state["route_accessibility"] = None

                st.session_state["graph"] = load_pickle(Path(tmp.name))
                st.session_state["graph_source"] = uploaded.name
                Path(tmp.name).unlink(missing_ok=True)
            st.rerun()
    else:
        uploaded_img = st.file_uploader(
            "Upload Satellite Image",
            type=["png", "jpg", "jpeg", "tif", "tiff"],
            key="sat_image_uploader",
        )
        if uploaded_img is not None:
            # Store uploaded image bytes and reset mask/graph if it's a new file
            img_bytes = uploaded_img.read()
            if st.session_state.get("uploaded_image_name") != uploaded_img.name:
                st.session_state["uploaded_image_bytes"] = img_bytes
                st.session_state["uploaded_image_name"] = uploaded_img.name
                st.session_state["extracted_mask"] = None
                st.session_state["extracted_road_mask_obj"] = None
        
        # Collapsible Advanced Settings (Keeps sidebar clean and user friendly)
        with st.expander("🛠️ Advanced Settings"):
            model_type = st.selectbox("Inference Model", ["sam_road", "dlinknet"], key="extractor_model")
            threshold = st.slider("Binarization Threshold", 0.1, 0.9, 0.5, step=0.05, key="extractor_threshold")
            use_mock = st.checkbox("Quick Demo Mode (Uses Mock Mask)", value=True, key="use_demo_mock_cb")
        
        if st.session_state.get("uploaded_image_bytes") is not None:
            if st.button("▶ Run Road Extraction", use_container_width=True):
                with st.spinner("Extracting roads via Deep Learning..."):
                    if use_mock:
                        # Load mock demo mask and simulate processing
                        mock_mask_path = _PROJECT_ROOT / "assets" / "samples" / "demo_mask.png"
                        if mock_mask_path.exists():
                            from PIL import Image
                            img_pil = Image.open(mock_mask_path).convert("L")
                            mask_arr = np.array(img_pil) / 255.0
                            mask_arr = (mask_arr > 0.5).astype(np.uint8)
                            st.session_state["extracted_mask"] = mask_arr
                            
                            # Construct a mock RoadMask object so graph builder doesn't crash
                            from argus.core.types import RoadMask
                            st.session_state["extracted_road_mask_obj"] = RoadMask(
                                mask=mask_arr,
                                crs="EPSG:4326",
                                bounds=(77.58, 12.96, 77.60, 12.98),
                                transform=(0.0001, 0.0, 77.58, 0.0, -0.0001, 12.98),
                                model_name="sam_road_mock",
                                model_version="1.0"
                            )
                        else:
                            st.error("Mock mask file not found in assets/samples/demo_mask.png")
                    else:
                        try:
                            # Live model inference
                            from argus.data.imagery import RasterImageLoader
                            from argus.vision import VisionConfig, SAMRoadExtractor, DLinkNetExtractor
                            
                            suffix = Path(st.session_state["uploaded_image_name"]).suffix
                            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                                tmp.write(st.session_state["uploaded_image_bytes"])
                                tmp.flush()
                                loader = RasterImageLoader(target_crs="EPSG:4326")
                                img = loader.load_and_reproject(tmp.name)
                                Path(tmp.name).unlink(missing_ok=True)
                            
                            vision_config = VisionConfig(
                                model_type=model_type,
                                threshold=threshold,
                                device="auto"
                            )
                            if model_type == "sam_road":
                                extractor = SAMRoadExtractor(vision_config)
                            else:
                                extractor = DLinkNetExtractor(vision_config)
                                
                            road_mask = extractor.extract(img)
                            st.session_state["extracted_mask"] = road_mask.mask
                            st.session_state["extracted_road_mask_obj"] = road_mask
                        except Exception as e:
                            st.error(f"Inference error: {e}")

                if st.session_state.get("extracted_mask") is not None:
                    st.success("Extraction complete! Check the '🛰️ Image Processor' tab.")
                    st.rerun()

    g = st.session_state.get("graph")
    if g is not None:
        st.markdown(
            f"""
            <div style="background:#1a2332;border:1px solid #2ea043;border-radius:8px;
                        padding:8px 12px;font-size:0.78rem;margin-top:8px;">
                <span style="color:#2ea043;font-weight:700;">✓</span>
                <span style="color:#e6edf3;"> {g.node_count:,} nodes · {g.edge_count:,} edges</span><br>
                <span style="color:#8b949e;font-size:0.72rem;">{st.session_state.get('graph_source','')}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# SIDEBAR — ANALYSIS
# ---------------------------------------------------------------------------

def _sidebar_analysis_trigger() -> None:
    if st.session_state.get("graph") is None:
        st.caption("Load a graph first.")
        return

    metrics = st.multiselect(
        "Metrics",
        options=sorted(["betweenness", "closeness", "degree", "articulation", "bridges"]),
        default=["betweenness", "articulation", "bridges"],
        label_visibility="collapsed",
    )
    top_n = st.slider("Top-N", 3, 50, 10)
    if st.button("🔍 Run Analysis", use_container_width=True):
        with st.spinner("Computing criticality metrics..."):
            from argus.analytics.analyzer import AnalyticsConfig, CriticalityAnalyzerImpl

            cfg = AnalyticsConfig(metrics=list(metrics), top_n=top_n)
            analyzer = CriticalityAnalyzerImpl(cfg)
            st.session_state["criticality_result"] = analyzer.analyze(st.session_state["graph"])
        st.success("Analysis complete!")
        st.rerun()


# ---------------------------------------------------------------------------
# SIDEBAR — SIMULATION
# ---------------------------------------------------------------------------

def _sidebar_simulation() -> None:
    graph = st.session_state.get("graph")
    if graph is None:
        st.caption("Load a graph first.")
        return

    import glob

    from argus.simulation import DisasterSimulatorImpl, load_scenario

    scenario_dir = str(_PROJECT_ROOT / "configs" / "scenarios")
    yaml_files = sorted(glob.glob(os.path.join(scenario_dir, "*.yaml")))
    if not yaml_files:
        st.caption(f"No scenarios found in {scenario_dir}/")
        return

    scenario_names = [os.path.basename(f).replace(".yaml", "") for f in yaml_files]
    selected_name = st.selectbox("Scenario", scenario_names, label_visibility="collapsed")
    scenario_path = os.path.join(scenario_dir, f"{selected_name}.yaml")
    severity = st.slider("Severity", 0.0, 1.0, 1.0, 0.1)
    if st.button("🌊 Run Simulation", use_container_width=True):
        with st.spinner(f"Simulating {selected_name}..."):
            scen = load_scenario(scenario_path)
            object.__setattr__(scen, "severity", severity)
            sim = DisasterSimulatorImpl()
            st.session_state["simulation_result"] = sim.simulate(graph, scen)
            st.session_state["simulation_source"] = selected_name
        st.success("Simulation complete!")
        st.rerun()


# ---------------------------------------------------------------------------
# SIDEBAR — ROUTING
# ---------------------------------------------------------------------------

def _sidebar_routing() -> None:
    graph = st.session_state.get("graph")
    if graph is None:
        st.caption("Load a graph first.")
        return

    from argus.routing import RouteQuery, RouterImpl

    algo = st.selectbox("Algorithm", ["dijkstra", "astar", "k_shortest"], label_visibility="collapsed")
    k_val = st.slider("K alternatives", 1, 5, 1) if algo == "k_shortest" else 1
    origin_str = st.text_input("Origin (lat,lon)", placeholder="12.97, 77.59", key="route_origin")
    dest_str = st.text_input("Destination (lat,lon)", placeholder="12.99, 77.61", key="route_dest")
    show_access = st.checkbox("Show accessibility", key="route_access_check")
    use_sim = st.checkbox("Compare vs simulation", key="route_compare_sim")

    if st.button("🛣️ Find Route", use_container_width=True):
        if not origin_str or not dest_str:
            st.warning("Enter both origin and destination")
            return
        try:
            o_lat, o_lon = (float(x) for x in origin_str.split(","))
            d_lat, d_lon = (float(x) for x in dest_str.split(","))
        except (ValueError, AttributeError):
            st.error("Use 'lat,lon' format e.g. 12.97,77.59")
            return

        router = RouterImpl()
        q = RouteQuery(origin=(o_lat, o_lon), destination=(d_lat, d_lon), algorithm=algo, k=k_val)
        with st.spinner("Routing..."):
            result = router.find_route(graph, q)
            st.session_state["route_result"] = result
            st.session_state["route_query"] = q

            if show_access:
                from argus.routing import AccessibilityQuery

                aq = AccessibilityQuery(origins=[(o_lat, o_lon)], destinations=[(d_lat, d_lon)])
                st.session_state["route_accessibility"] = router.accessibility(graph, aq)

            if use_sim:
                sim_result = st.session_state.get("simulation_result")
                if sim_result and sim_result.modified_graph:
                    mod_result = router.find_route(sim_result.modified_graph, q)
                    cmp = router.compare_routes(result.routes, mod_result.routes)
                    st.session_state["route_comparison"] = cmp
                    st.session_state["route_modified_result"] = mod_result
                else:
                    st.warning("No simulation result available")
                    st.session_state["route_comparison"] = None
            else:
                st.session_state["route_comparison"] = None

        st.success(f"Found {len(result.routes)} route(s)")
        st.rerun()


# ---------------------------------------------------------------------------
# SIDEBAR — EXPORT
# ---------------------------------------------------------------------------

def _sidebar_exports() -> None:
    if st.session_state.get("graph") is None:
        st.caption("Load a graph first.")
        return

    if st.button("📦 Export ZIP", use_container_width=True):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            cr = st.session_state.get("criticality_result")
            if cr is not None:
                rpt = {"report": cr.report, "summary": cr.summary}
                zf.writestr("criticality_report.json", json.dumps(rpt, indent=2, default=str))

            sr = st.session_state.get("simulation_result")
            if sr is not None:
                zf.writestr("simulation_impact.json", json.dumps(sr.impact_report, indent=2, default=str))

            rr = st.session_state.get("route_result")
            if rr is not None and rr.routes:
                from argus.routing import export_route_geojson

                tmp = Path(tempfile.gettempdir()) / "argus_routes.geojson"
                export_route_geojson(rr.routes, tmp)
                zf.write(tmp, "routes.geojson")
                tmp.unlink(missing_ok=True)

        buf.seek(0)
        st.download_button(
            "💾 Download ZIP",
            data=buf,
            file_name="argus_results.zip",
            mime="application/zip",
            use_container_width=True,
        )


# ---------------------------------------------------------------------------
# CONFIG HELPERS
# ---------------------------------------------------------------------------

def _cfg_road_color() -> str:
    rgb = _dashboard_cfg.layers.road_color
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def _cfg_critical_node_color() -> list[int]:
    return list(_dashboard_cfg.layers.critical_node_color)


def _cfg_flood_color() -> str:
    rgb = _dashboard_cfg.layers.flood_color[:3]
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def _cfg_route_color() -> str:
    rgb = _dashboard_cfg.layers.route_color
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def _affine_from_graph(graph: Any) -> tuple[float, ...]:
    transform = graph.metadata.get("transform")
    if transform and len(transform) == 6:
        return tuple(float(x) for x in transform)
    return (1.0, 0.0, 0.0, 0.0, -1.0, 0.0)


def _heatmap_color(ratio: float) -> str:
    r = int(min(255, ratio * 2 * 255))
    g = int(min(255, (1 - ratio) * 2 * 255))
    b = 50
    return f"#{r:02x}{g:02x}{b:02x}"


def _component_count(graph: Any) -> int:
    import networkx as nx

    return nx.number_connected_components(graph.graph.to_undirected())


def _is_valid_geographic_bounds(bounds: tuple[float, float, float, float]) -> bool:
    """Return True if bounds are within valid EPSG:4326 lat/lon limits."""
    min_lon, min_lat, max_lon, max_lat = bounds
    return -90 <= min_lat <= 90 and -90 <= max_lat <= 90 and -180 <= min_lon <= 180 and -180 <= max_lon <= 180


def _get_map_coords(graph: Any, lat: float, lon: float) -> tuple[float, float]:
    """Map coordinates to valid geographic space if the graph uses pixel coordinates."""
    bounds = graph.bounds
    if _is_valid_geographic_bounds(bounds):
        return lat, lon
    
    # Scale and center around the configured default center (Bangalore)
    min_lon, min_lat, max_lon, max_lat = bounds
    center_lat_orig = (min_lat + max_lat) / 2
    center_lon_orig = (min_lon + max_lon) / 2
    
    # 0.0001 degrees is ~11 meters.
    # Scale coordinates so the entire graph spans a reasonable local area
    lat_scaled = float(_dashboard_cfg.map.default_center[0]) + (lat - center_lat_orig) * 0.0001
    lon_scaled = float(_dashboard_cfg.map.default_center[1]) + (lon - center_lon_orig) * 0.0001
    return lat_scaled, lon_scaled


def _folium_base_map(graph: Any) -> Any:
    import folium

    bounds = graph.bounds
    if _is_valid_geographic_bounds(bounds):
        center_lat = (bounds[1] + bounds[3]) / 2
        center_lon = (bounds[0] + bounds[2]) / 2
        zoom = _dashboard_cfg.map.default_zoom
    else:
        center_lat = float(_dashboard_cfg.map.default_center[0])
        center_lon = float(_dashboard_cfg.map.default_center[1])
        # Force a slightly higher zoom for scaled pixel graphs so they look good in Bangalore
        zoom = 14

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        tiles="CartoDB positron",
    )
    return m


def _draw_graph_edges(
    m: Any, graph: Any, color: str = "#3388ff", weight: float = 2, opacity: float = 0.6
) -> None:
    import folium

    for u, v, _key, data in graph.graph.edges(keys=True, data=True):
        u_lat = graph.graph.nodes[u].get("lat", 0)
        u_lon = graph.graph.nodes[u].get("lon", 0)
        v_lat = graph.graph.nodes[v].get("lat", 0)
        v_lon = graph.graph.nodes[v].get("lon", 0)
        path_pixels = data.get("path_pixels")
        if path_pixels and len(path_pixels) >= 2:
            a, b, c, d, e, f = _affine_from_graph(graph)
            coords = []
            for px, py in path_pixels:
                raw_lat = d * px + e * py + f
                raw_lon = a * px + b * py + c
                coords.append(_get_map_coords(graph, raw_lat, raw_lon))
        else:
            coords = [_get_map_coords(graph, u_lat, u_lon), _get_map_coords(graph, v_lat, v_lon)]
        folium.PolyLine(locations=coords, color=color, weight=weight, opacity=opacity).add_to(m)


def _draw_graph_nodes(m: Any, graph: Any) -> None:
    import folium

    for node_id, data in graph.graph.nodes(data=True):
        lat = data.get("lat", 0)
        lon = data.get("lon", 0)
        lat, lon = _get_map_coords(graph, lat, lon)
        deg = data.get("degree", 0)
        color = "#e34c26" if deg <= 1 else "#f9826c" if deg == 2 else "#2ea043"
        radius = 3 if deg <= 1 else 4 if deg <= 2 else 6
        folium.CircleMarker(
            location=[lat, lon],
            radius=radius,
            color=color,
            fill=True,
            fill_opacity=0.85,
            popup=f"Node {node_id} (deg={deg})",
        ).add_to(m)


def _render_empty_map() -> None:
    import pydeck as pdk

    center = _dashboard_cfg.map.default_center
    view = pdk.ViewState(
        latitude=center[0], longitude=center[1], zoom=_dashboard_cfg.map.default_zoom
    )
    st.pydeck_chart(pdk.Deck(initial_view_state=view, map_style="light"))


def _section_header(icon: str, title: str, subtitle: str = "") -> None:
    sub_html = f'<div style="font-size:0.8rem;color:#57606a;margin-top:4px;">{subtitle}</div>' if subtitle else ""
    st.markdown(
        f"""
        <div style="margin-bottom:20px;">
          <div class="section-header"><span>{icon}</span> {title}</div>
          {sub_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _stat_card(icon: str, label: str, value: str, sub: str = "") -> str:
    sub_html = f'<div class="stat-sub">{sub}</div>' if sub else ""
    return (
        f'<div class="stat-card">'
        f'  <div class="stat-icon">{icon}</div>'
        f'  <div class="stat-label">{label}</div>'
        f'  <div class="stat-value">{value}</div>'
        f'  {sub_html}'
        f'</div>'
    )


def _render_stat_row(cards: list[tuple[str, str, str, str]]) -> None:
    """Render a row of stat cards. Each card is (icon, label, value, sub)."""
    cols = st.columns(len(cards))
    for col, (icon, label, value, sub) in zip(cols, cards):
        with col:
            st.markdown(_stat_card(icon, label, value, sub), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# TAB 0 — OVERVIEW
# ---------------------------------------------------------------------------

def _tab_overview() -> None:
    graph = st.session_state.get("graph")
    cr = st.session_state.get("criticality_result")
    sr = st.session_state.get("simulation_result")
    rr = st.session_state.get("route_result")

    if graph is None:
        _section_header("🏠", "Overview")
        st.info("👈 Load a road graph from the sidebar or click **Load Demo Dataset** to begin.")
        _render_empty_map()
        return

    # Stat cards row
    rt_count = len(rr.routes) if rr and rr.routes else 0
    crit_aps = cr.summary.get("resilience", {}).get("articulation_points_count", 0) if cr else "—"
    sim_nodes_removed = len(sr.impact_report.get("removed_nodes", [])) if sr else "—"
    _render_stat_row([
        ("🗺️", "Nodes", f"{graph.node_count:,}", f"{graph.edge_count:,} edges"),
        ("📊", "Art. Points", str(crit_aps), "critical junctions" if cr else "run analysis"),
        ("🌊", "Removed Nodes", str(sim_nodes_removed), "after disaster" if sr else "run simulation"),
        ("🛣️", "Routes", str(rt_count) if rt_count else "—", "computed paths" if rt_count else "run routing"),
    ])

    st.markdown("<br>", unsafe_allow_html=True)
    _section_header("🗺️", "Unified Map", "All active layers overlaid")

    col_l, col_r = st.columns([3, 1])
    with col_l:
        lc1, lc2, lc3 = st.columns(3)
        with lc1:
            show_crit = st.checkbox("Criticality layer", value=cr is not None)
        with lc2:
            show_sim = st.checkbox("Simulation layer", value=sr is not None)
        with lc3:
            show_route = st.checkbox("Routing layer", value=rr is not None)
        _render_overview_map(graph, cr if show_crit else None, sr if show_sim else None, rr if show_route else None)

    with col_r:
        st.metric("Nodes", f"{graph.node_count:,}")
        st.metric("Edges", f"{graph.edge_count:,}")
        st.metric("Components", _component_count(graph))
        if cr:
            res = cr.summary.get("resilience", {})
            vuln = res.get("vulnerability_ratio")
            st.metric("Vulnerability", f"{vuln:.1%}" if vuln else "—")
        if sr:
            impact = sr.impact_report
            st.metric("Edges Lost", len(impact.get("removed_edges", [])))


def _render_overview_map(
    graph: Any, criticality: Any | None, simulation: Any | None, routing: Any | None
) -> None:
    import folium
    from streamlit_folium import st_folium

    m = _folium_base_map(graph)
    _draw_graph_edges(m, graph, color=_cfg_road_color(), weight=1.5, opacity=0.35)

    if criticality is not None:
        _overlay_criticality_on(m, criticality)
    if simulation is not None:
        _overlay_simulation_on(m, simulation, graph)
        _overlay_sim_affected_region(m)
    if routing is not None and routing.routes:
        route_colors = ["#cf222e", "#2da44e", "#0969da"]
        for i, route in enumerate(routing.routes):
            color = route_colors[i % len(route_colors)]
            coords = route["geometry"]["coordinates"]
            locations = []
            for lon, lat in coords:
                lat_scaled, lon_scaled = _get_map_coords(graph, lat, lon)
                locations.append((lat_scaled, lon_scaled))
            folium.PolyLine(
                locations=locations, color=color, weight=5, opacity=0.9,
                popup=f"Route {i+1} ({route['properties']['length_m']:.0f}m)",
            ).add_to(m)

    st_folium(m, use_container_width=True, height=520, returned_objects=[])


def _overlay_criticality_on(m: Any, result: Any) -> None:
    import folium

    graph = result.annotated_graph
    metric_key = "betweenness"
    values = [float(d.get(metric_key, 0)) for _, d in graph.graph.nodes(data=True) if d.get(metric_key)]
    max_val = max(values) if values else 1.0
    for node_id, data in graph.graph.nodes(data=True):
        lat = data.get("lat", 0)
        lon = data.get("lon", 0)
        lat_scaled, lon_scaled = _get_map_coords(graph, lat, lon)
        val = float(data.get(metric_key, 0))
        ratio = val / max_val if max_val > 0 else 0
        color = _heatmap_color(ratio)
        is_ap = data.get("is_articulation", 0)
        folium.CircleMarker(
            location=[lat_scaled, lon_scaled], radius=6 if is_ap else 4,
            color="#cf222e" if is_ap else color,
            fill=True, fill_color=color, fill_opacity=0.8, weight=2 if is_ap else 1,
        ).add_to(m)


def _overlay_simulation_on(m: Any, simulation: Any, orig_graph: Any) -> None:
    import folium

    impact = simulation.impact_report
    removed_node_ids = {e["id"] for e in impact.get("removed_nodes", [])}
    for entry in impact.get("removed_edges", []):
        u_id, v_id = entry["u"], entry["v"]
        if u_id in orig_graph.graph.nodes and v_id in orig_graph.graph.nodes:
            u_lat = orig_graph.graph.nodes[u_id].get("lat", 0)
            u_lon = orig_graph.graph.nodes[u_id].get("lon", 0)
            v_lat = orig_graph.graph.nodes[v_id].get("lat", 0)
            v_lon = orig_graph.graph.nodes[v_id].get("lon", 0)
            u_lat_scaled, u_lon_scaled = _get_map_coords(orig_graph, u_lat, u_lon)
            v_lat_scaled, v_lon_scaled = _get_map_coords(orig_graph, v_lat, v_lon)
            folium.PolyLine(
                locations=[(u_lat_scaled, u_lon_scaled), (v_lat_scaled, v_lon_scaled)],
                color=_cfg_flood_color(), weight=3, opacity=0.7, dash_array="8,6",
            ).add_to(m)
    for entry in impact.get("removed_nodes", []):
        nid = entry["id"]
        if nid in orig_graph.graph.nodes:
            lat = orig_graph.graph.nodes[nid].get("lat", 0)
            lon = orig_graph.graph.nodes[nid].get("lon", 0)
            lat_scaled, lon_scaled = _get_map_coords(orig_graph, lat, lon)
            folium.CircleMarker(
                location=[lat_scaled, lon_scaled], radius=5,
                color=_cfg_flood_color(), fill=True, fill_color=_cfg_flood_color(), fill_opacity=0.6,
                popup=f"Removed: {nid}",
            ).add_to(m)


def _overlay_sim_affected_region(m: Any) -> None:
    import folium

    source_name = st.session_state.get("simulation_source", "")
    if not source_name:
        return
    try:
        from shapely.geometry import Polygon as ShapelyPolygon

        from argus.simulation import load_scenario

        scen = load_scenario(str(_PROJECT_ROOT / "configs" / "scenarios" / f"{source_name}.yaml"))
        region = ShapelyPolygon(scen.affected_region["coordinates"][0])
        lons, lats = region.exterior.xy
        orig_graph = st.session_state.get("graph")
        coords = []
        for lat, lon in zip(lats, lons, strict=False):
            lat_scaled, lon_scaled = _get_map_coords(orig_graph, lat, lon)
            coords.append((lat_scaled, lon_scaled))
        folium.Polygon(
            locations=coords,
            color=_cfg_flood_color(),
            weight=2,
            fill=True,
            fill_color=_cfg_flood_color(),
            fill_opacity=0.12,
            popup="Affected Region",
        ).add_to(m)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# TAB 1 — ROAD NETWORK
# ---------------------------------------------------------------------------

def _tab_road_network() -> None:
    graph = st.session_state.get("graph")
    if graph is None:
        _section_header("🗺️", "Road Network")
        st.info("Load a road graph from the sidebar to visualise the network.")
        _render_empty_map()
        return

    _section_header(
        "🗺️", "Road Network",
        "Node colours: 🟢 high-degree junctions · 🟠 degree-2 roads · 🔴 leaf/dangling nodes"
    )

    col_map, col_stats = st.columns([3, 1])
    with col_map:
        _render_network_map(graph)
    with col_stats:
        st.metric("Nodes", f"{graph.node_count:,}")
        st.metric("Edges", f"{graph.edge_count:,}")
        st.metric("Components", _component_count(graph))
        crs = graph.metadata.get("crs", "—")
        st.markdown(
            f'<div style="margin-top:16px;font-size:0.78rem;color:#57606a;"><b>CRS:</b> {crs}</div>',
            unsafe_allow_html=True,
        )


def _render_network_map(graph: Any) -> None:
    import folium
    from streamlit_folium import st_folium

    m = _folium_base_map(graph)
    _draw_graph_edges(m, graph, color=_cfg_road_color(), weight=2, opacity=0.7)
    _draw_graph_nodes(m, graph)
    st_folium(m, use_container_width=True, height=580, returned_objects=[])


# ---------------------------------------------------------------------------
# TAB 2 — CRITICALITY
# ---------------------------------------------------------------------------

def _tab_criticality() -> None:
    result = st.session_state.get("criticality_result")
    if result is None:
        _section_header("📊", "Criticality Analysis")
        st.info("Run criticality analysis from the sidebar to identify structurally important nodes and edges.")
        _render_empty_map()
        return

    available_metrics = [
        m for m in result.summary.get("metrics_computed", [])
        if m in ("betweenness", "closeness", "degree")
    ]
    if not available_metrics:
        available_metrics = ["betweenness"]

    res = result.summary.get("resilience", {})
    aps = res.get("articulation_points_count", 0)
    brs = res.get("bridges_count", 0)
    vuln = res.get("vulnerability_ratio")

    _section_header("📊", "Criticality Analysis", "Network resilience and structural vulnerability scoring")

    _render_stat_row([
        ("🔴", "Articulation Pts", str(aps), "removal disconnects graph"),
        ("🌉", "Bridges", str(brs), "critical single edges"),
        ("⚠️", "Vulnerability", f"{vuln:.1%}" if vuln is not None else "—", "ratio of critical nodes"),
        ("📏", "Avg Path Len", str(res.get("avg_path_length", "—")), "network diameter proxy"),
    ])

    st.markdown("<br>", unsafe_allow_html=True)

    col_l, col_r = st.columns([3, 1])
    with col_l:
        selected_metric = st.selectbox("Colour map by metric", available_metrics)
        _render_criticality_map(result, selected_metric)
    with col_r:
        _render_criticality_stats(result, selected_metric)


def _render_criticality_map(result: Any, metric: str) -> None:
    import folium
    from streamlit_folium import st_folium

    graph = result.annotated_graph
    m = _folium_base_map(graph)

    metric_key = {"betweenness": "betweenness", "closeness": "closeness", "degree": "degree_centrality"}.get(metric, "betweenness")
    values = [float(d.get(metric_key, 0)) for _, d in graph.graph.nodes(data=True) if d.get(metric_key)]
    max_val = max(values) if values else 1.0

    for u, v, _key, data in graph.graph.edges(keys=True, data=True):
        u_lat = graph.graph.nodes[u].get("lat", 0)
        u_lon = graph.graph.nodes[u].get("lon", 0)
        v_lat = graph.graph.nodes[v].get("lat", 0)
        v_lon = graph.graph.nodes[v].get("lon", 0)
        u_lat_scaled, u_lon_scaled = _get_map_coords(graph, u_lat, u_lon)
        v_lat_scaled, v_lon_scaled = _get_map_coords(graph, v_lat, v_lon)
        is_bridge = data.get("is_bridge", 0)
        folium.PolyLine(
            locations=[(u_lat_scaled, u_lon_scaled), (v_lat_scaled, v_lon_scaled)],
            color="#cf222e" if is_bridge else "#c9d1d9",
            weight=3 if is_bridge else 1, opacity=0.6,
        ).add_to(m)

    for node_id, data in graph.graph.nodes(data=True):
        lat = data.get("lat", 0)
        lon = data.get("lon", 0)
        lat_scaled, lon_scaled = _get_map_coords(graph, lat, lon)
        val = float(data.get(metric_key, 0))
        ratio = val / max_val if max_val > 0 else 0
        color = _heatmap_color(ratio)
        is_ap = data.get("is_articulation", 0)
        folium.CircleMarker(
            location=[lat_scaled, lon_scaled], radius=8 if is_ap else 5,
            color="#cf222e" if is_ap else color,
            fill=True, fill_color=color, fill_opacity=0.85, weight=2 if is_ap else 1,
            popup=f"Node {node_id}<br>{metric}={val:.4f}" + ("<br>🔴 Articulation Point" if is_ap else ""),
        ).add_to(m)

    st_folium(m, use_container_width=True, height=580, returned_objects=[])


def _render_criticality_stats(result: Any, metric: str) -> None:
    st.markdown('<div style="font-size:0.82rem;font-weight:700;color:#57606a;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:12px;">Top Nodes</div>', unsafe_allow_html=True)
    key = {"betweenness": "top_nodes_betweenness", "closeness": "top_nodes_closeness", "degree": "top_nodes_degree"}.get(metric, "top_nodes_betweenness")
    top_list = result.report.get(key, [])[:10]
    if top_list:
        import pandas as pd

        df = pd.DataFrame(top_list, columns=["Node ID", "Score"])
        st.dataframe(df.style.format({"Score": "{:.5f}"}), use_container_width=True, height=260)

    st.markdown('<div style="font-size:0.82rem;font-weight:700;color:#57606a;text-transform:uppercase;letter-spacing:0.05em;margin:16px 0 8px 0;">Articulation Points</div>', unsafe_allow_html=True)
    aps = result.report.get("articulation_points", [])[:8]
    if aps:
        for ap in aps:
            st.markdown(f'<span style="background:#ffebe9;color:#cf222e;border-radius:4px;padding:2px 8px;font-size:0.78rem;margin:2px;display:inline-block;">Node {ap}</span>', unsafe_allow_html=True)
    else:
        st.caption("None found")

    st.markdown('<div style="font-size:0.82rem;font-weight:700;color:#57606a;text-transform:uppercase;letter-spacing:0.05em;margin:16px 0 8px 0;">Bridge Edges</div>', unsafe_allow_html=True)
    bridges = result.report.get("bridges", [])[:5]
    if bridges:
        for u, v in bridges:
            st.markdown(f'<span style="background:#fff1e5;color:#bc4c00;border-radius:4px;padding:2px 8px;font-size:0.78rem;margin:2px;display:inline-block;">({u} → {v})</span>', unsafe_allow_html=True)
    else:
        st.caption("None found")


# ---------------------------------------------------------------------------
# TAB 3 — REPORT
# ---------------------------------------------------------------------------

def _tab_report() -> None:
    _section_header("📋", "Full Analysis Report", "JSON export of the complete criticality computation")
    result = st.session_state.get("criticality_result")
    if result is None:
        st.info("Run criticality analysis from the sidebar to generate the report.")
        return

    report_data = {"report": result.report, "summary": result.summary}
    raw = json.dumps(report_data, indent=2, default=str)

    col_a, col_b = st.columns([1, 2])
    with col_a:
        st.download_button(
            "📥 Download JSON Report",
            data=raw,
            file_name="criticality_report.json",
            mime="application/json",
            use_container_width=True,
        )

        # Summary pills
        res = result.summary.get("resilience", {})
        st.markdown("<br>", unsafe_allow_html=True)
        st.metric("Art. Points", res.get("articulation_points_count", 0))
        st.metric("Bridges", res.get("bridges_count", 0))
        vuln = res.get("vulnerability_ratio")
        st.metric("Vulnerability", f"{vuln:.2%}" if vuln is not None else "—")

    with col_b:
        with st.expander("📄 Raw JSON", expanded=False):
            st.code(raw[:8000], language="json")


# ---------------------------------------------------------------------------
# TAB 4 — SIMULATION
# ---------------------------------------------------------------------------

def _tab_simulation() -> None:
    result = st.session_state.get("simulation_result")
    if result is None:
        _section_header("🌊", "Disaster Simulation")
        st.info("Configure a disaster scenario in the sidebar and run simulation.")
        _render_empty_map()
        return

    impact = result.impact_report
    source = st.session_state.get("simulation_source", "unknown")
    scenario_id = result.scenario_metadata.get("scenario_id", source)

    _section_header("🌊", f"Scenario: {scenario_id}", f"Source: {source}")

    # Impact stat cards
    _render_stat_row([
        ("🔴", "Nodes Removed", str(len(impact.get("removed_nodes", []))), "flood/collapse"),
        ("❌", "Edges Removed", str(len(impact.get("removed_edges", []))), "severed connections"),
        ("🟡", "Edges Reweighted", str(len(impact.get("reweighted_edges", []))), "partial damage"),
        ("🔀", "New Isolated", str(impact.get("new_isolated_components", 0)), "disconnected clusters"),
    ])

    st.markdown("<br>", unsafe_allow_html=True)

    # Before / After maps
    _section_header("🗺️", "Before vs After", "Blue = road network · Red dashed = removed · Orange = reweighted")
    map_l, map_r = st.columns(2)
    graph = st.session_state["graph"]

    with map_l:
        st.markdown(
            '<div style="text-align:center;font-weight:700;font-size:0.85rem;color:#0d1117;margin-bottom:8px;'
            'background:#dafbe1;border:1px solid #aceebb;border-radius:8px;padding:6px;">✅ Before Disaster</div>',
            unsafe_allow_html=True,
        )
        import folium
        from streamlit_folium import st_folium

        m_before = _folium_base_map(graph)
        _draw_graph_edges(m_before, graph, color=_cfg_road_color())
        _draw_graph_nodes(m_before, graph)
        st_folium(m_before, use_container_width=True, height=480, returned_objects=[])

    with map_r:
        st.markdown(
            '<div style="text-align:center;font-weight:700;font-size:0.85rem;color:#0d1117;margin-bottom:8px;'
            'background:#ffebe9;border:1px solid #ff8182;border-radius:8px;padding:6px;">⚠️ After Disaster</div>',
            unsafe_allow_html=True,
        )
        _render_simulation_after_map(result, graph)

    # Impact detail tables
    st.markdown("<br>", unsafe_allow_html=True)
    col_nodes, col_edges = st.columns(2)
    with col_nodes:
        st.markdown('<div class="section-header">🔴 Removed Nodes</div>', unsafe_allow_html=True)
        removed_nodes = impact.get("removed_nodes", [])
        if removed_nodes:
            import pandas as pd
            df = pd.DataFrame(removed_nodes[:20])
            st.dataframe(df, use_container_width=True, height=220)
        else:
            st.caption("None removed.")

    with col_edges:
        st.markdown('<div class="section-header">❌ Removed Edges</div>', unsafe_allow_html=True)
        removed_edges = impact.get("removed_edges", [])
        if removed_edges:
            import pandas as pd
            df = pd.DataFrame(removed_edges[:20])
            st.dataframe(df, use_container_width=True, height=220)
        else:
            st.caption("None removed.")


def _render_simulation_after_map(result: Any, graph: Any) -> None:
    import folium
    from streamlit_folium import st_folium

    impact = result.impact_report
    modified = result.modified_graph
    removed_node_ids = {e["id"] for e in impact.get("removed_nodes", [])}
    removed_edges_set = {(e["u"], e["v"]) for e in impact.get("removed_edges", [])}
    reweighted_edges_set = {(e["u"], e["v"]) for e in impact.get("reweighted_edges", [])}

    m = _folium_base_map(graph)

    for u, v, _key, data in modified.graph.edges(data=True, keys=True):
        if u in removed_node_ids or v in removed_node_ids:
            continue
        if (u, v) in removed_edges_set or (v, u) in removed_edges_set:
            continue
        u_lat = modified.graph.nodes[u].get("lat", 0)
        u_lon = modified.graph.nodes[u].get("lon", 0)
        v_lat = modified.graph.nodes[v].get("lat", 0)
        v_lon = modified.graph.nodes[v].get("lon", 0)
        u_lat_scaled, u_lon_scaled = _get_map_coords(graph, u_lat, u_lon)
        v_lat_scaled, v_lon_scaled = _get_map_coords(graph, v_lat, v_lon)
        edge_color = "#f0883e" if (u, v) in reweighted_edges_set else _cfg_road_color()
        folium.PolyLine(locations=[(u_lat_scaled, u_lon_scaled), (v_lat_scaled, v_lon_scaled)], color=edge_color, weight=2, opacity=0.7).add_to(m)

    for entry in impact.get("removed_edges", []):
        u_id, v_id = entry["u"], entry["v"]
        if u_id in graph.graph.nodes and v_id in graph.graph.nodes:
            u_lat = graph.graph.nodes[u_id].get("lat", 0)
            u_lon = graph.graph.nodes[u_id].get("lon", 0)
            v_lat = graph.graph.nodes[v_id].get("lat", 0)
            v_lon = graph.graph.nodes[v_id].get("lon", 0)
            u_lat_scaled, u_lon_scaled = _get_map_coords(graph, u_lat, u_lon)
            v_lat_scaled, v_lon_scaled = _get_map_coords(graph, v_lat, v_lon)
            folium.PolyLine(
                locations=[(u_lat_scaled, u_lon_scaled), (v_lat_scaled, v_lon_scaled)],
                color=_cfg_flood_color(), weight=3, opacity=0.7, dash_array="8,6",
            ).add_to(m)

    for entry in impact.get("removed_nodes", []):
        nid = entry["id"]
        if nid in graph.graph.nodes:
            lat = graph.graph.nodes[nid].get("lat", 0)
            lon = graph.graph.nodes[nid].get("lon", 0)
            lat_scaled, lon_scaled = _get_map_coords(graph, lat, lon)
            folium.CircleMarker(
                location=[lat_scaled, lon_scaled], radius=6, color=_cfg_flood_color(),
                fill=True, fill_color=_cfg_flood_color(), fill_opacity=0.6,
                popup=f"Removed: {nid}",
            ).add_to(m)

    _overlay_sim_affected_region(m)
    st_folium(m, use_container_width=True, height=480, returned_objects=[])


# ---------------------------------------------------------------------------
# TAB 5 — ROUTING
# ---------------------------------------------------------------------------

def _tab_routing() -> None:
    result = st.session_state.get("route_result")
    if result is None:
        _section_header("🛣️", "Routing")
        st.info("Enter an origin and destination in the sidebar, then click **Find Route**.")
        _render_empty_map()
        return

    routes = result.routes
    if not routes:
        _section_header("🛣️", "Routing")
        st.warning("No routes found between the given points. Try different coordinates.")
        _render_empty_map()
        return

    primary = routes[0]
    props = primary["properties"]

    _section_header("🛣️", "Routing Results", f"{len(routes)} route(s) computed")

    # Route metrics
    _render_stat_row([
        ("📏", "Distance", f"{props['length_m']:.0f} m", "shortest path length"),
        ("⏱️", "Travel Time", f"{props['travel_time_s']:.0f} s", f"{props.get('speed_kmh', 40):.0f} km/h assumed"),
        ("🔀", "Routes Found", str(len(routes)), "total computed"),
        ("📍", "Nodes", str(len(props.get("nodes", []))), "in path"),
    ])

    # Comparison banner
    cmp = st.session_state.get("route_comparison")
    if cmp:
        status = cmp.get("status", "unknown")
        delta = cmp.get("delta_length_m", 0) or 0
        chip_cls = {"unchanged": "chip-green", "detour": "chip-orange", "unreachable": "chip-red"}.get(status, "chip-blue")
        delta_sign = f"+{delta:.0f}" if delta > 0 else f"{delta:.0f}"
        st.markdown(
            f"""
            <div class="compare-banner">
                ⚡ <strong>Disaster Comparison:</strong>
                Baseline {cmp.get('baseline_length_m', 0):.0f}m →
                Modified {cmp.get('modified_length_m', 0):.0f}m
                ({delta_sign}m)
                &nbsp;<span class="status-chip {chip_cls}">{status.upper()}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Maps
    graph = st.session_state.get("graph")
    st.markdown("<br>", unsafe_allow_html=True)
    _section_header("🗺️", "Route Map")

    if cmp and st.session_state.get("route_modified_result"):
        mod_result = st.session_state["route_modified_result"]
        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown(
                '<div style="text-align:center;font-weight:700;font-size:0.85rem;margin-bottom:8px;'
                'background:#dafbe1;border:1px solid #aceebb;border-radius:8px;padding:6px;">🟢 Baseline Route</div>',
                unsafe_allow_html=True,
            )
            _render_route_map(graph, routes)
        with col_r:
            mod_graph = st.session_state["simulation_result"].modified_graph
            st.markdown(
                '<div style="text-align:center;font-weight:700;font-size:0.85rem;margin-bottom:8px;'
                'background:#fff1e5;border:1px solid #ffc680;border-radius:8px;padding:6px;">⚠️ After Disaster</div>',
                unsafe_allow_html=True,
            )
            _render_route_map(mod_graph, mod_result.routes)
    else:
        _render_route_map(graph, routes)

    # Accessibility
    acc = st.session_state.get("route_accessibility")
    if acc:
        st.markdown("<br>", unsafe_allow_html=True)
        _section_header("♿", "Accessibility")
        for origin_key, info in acc.items():
            reachable = info.get("reachable", [])
            unreachable = info.get("unreachable", [])
            cols = st.columns(3)
            cols[0].metric("Reachable", len(reachable))
            cols[1].metric("Unreachable", len(unreachable))
            cols[2].metric("Total", info.get("total", len(reachable) + len(unreachable)))

    # Route details table
    st.markdown("<br>", unsafe_allow_html=True)
    _section_header("📋", "Route Details")
    rows = []
    for i, r in enumerate(routes):
        p = r["properties"]
        rows.append({
            "Route": f"Route {i+1}",
            "Length (m)": f"{p['length_m']:.1f}",
            "Time (s)": f"{p['travel_time_s']:.1f}",
            "Speed (km/h)": f"{p.get('speed_kmh', 40):.0f}",
            "Nodes": len(p.get("nodes", [])),
        })
    import pandas as pd

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # Export button
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("💾 Export Route GeoJSON"):
        from argus.routing import export_route_geojson

        tmp = Path(tempfile.gettempdir()) / "argus_route_export.geojson"
        export_route_geojson(routes, tmp)
        st.success(f"Saved to {tmp}")


def _render_route_map(graph: Any, routes: list[dict]) -> None:
    import folium
    from streamlit_folium import st_folium

    m = _folium_base_map(graph)
    _draw_graph_edges(m, graph, color="#c9d1d9", weight=1, opacity=0.35)

    route_colors = ["#cf222e", "#2da44e", "#0969da"]
    for i, route in enumerate(routes):
        color = route_colors[i % len(route_colors)]
        coords = route["geometry"]["coordinates"]
        locations = []
        for lon, lat in coords:
            lat_scaled, lon_scaled = _get_map_coords(graph, lat, lon)
            locations.append((lat_scaled, lon_scaled))
        folium.PolyLine(
            locations=locations, color=color, weight=5, opacity=0.9,
            popup=f"Route {i+1} ({route['properties']['length_m']:.1f}m)",
        ).add_to(m)

    if routes:
        first_coords = routes[0]["geometry"]["coordinates"]
        if len(first_coords) >= 2:
            o_lon, o_lat = first_coords[0]
            d_lon, d_lat = first_coords[-1]
            o_lat_scaled, o_lon_scaled = _get_map_coords(graph, o_lat, o_lon)
            d_lat_scaled, d_lon_scaled = _get_map_coords(graph, d_lat, d_lon)
            for lat_c, lon_c, label, color in [(o_lat_scaled, o_lon_scaled, "Origin", "#2da44e"), (d_lat_scaled, d_lon_scaled, "Destination", "#cf222e")]:
                folium.CircleMarker(
                    location=[lat_c, lon_c], radius=9, color=color,
                    fill=True, fill_color=color, fill_opacity=1.0, popup=label,
                ).add_to(m)

    # Unreachable overlay
    acc = st.session_state.get("route_accessibility")
    if acc:
        for _ok, info in acc.items():
            for dest in info.get("unreachable", []):
                d_lat, d_lon = dest
                d_lat_scaled, d_lon_scaled = _get_map_coords(graph, d_lat, d_lon)
                folium.CircleMarker(
                    location=[d_lat_scaled, d_lon_scaled], radius=5, color="#cf222e",
                    fill=True, fill_color="#cf222e", fill_opacity=0.3, popup="Unreachable",
                ).add_to(m)


    st_folium(m, use_container_width=True, height=500, returned_objects=[])


def _tab_image_processor() -> None:
    _section_header("🛰️", "Road Extraction & Topological Reconstruction", "Process satellite imagery and generate continuous vector routing networks")
    
    img_bytes = st.session_state.get("uploaded_image_bytes")
    if img_bytes is None:
        st.info("👈 Upload a satellite image in the sidebar and click **Run Road Extraction** to begin.")
        
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="stat-card" style="text-align:center;height:240px;display:flex;flex-direction:column;justify-content:center;align-items:center;">'
                        '<div style="font-size:3rem;margin-bottom:12px;">🛰️</div>'
                        '<div style="font-weight:700;font-size:0.9rem;color:#24292f;">1. Input Imagery</div>'
                        '<div style="font-size:0.8rem;color:#57606a;margin-top:4px;">Upload raw or multispectral remote sensing bands (Cartosat, Resourcesat, Sentinel).</div>'
                        '</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="stat-card" style="text-align:center;height:240px;display:flex;flex-direction:column;justify-content:center;align-items:center;">'
                        '<div style="font-size:3rem;margin-bottom:12px;">🟢</div>'
                        '<div style="font-weight:700;font-size:0.9rem;color:#24292f;">2. Routable Topology</div>'
                        '<div style="font-size:0.8rem;color:#57606a;margin-top:4px;">Deep learning extracts roads and resolves vegetation occlusions into routing graphs.</div>'
                        '</div>', unsafe_allow_html=True)
        return

    col_img, col_mask = st.columns(2)
    
    with col_img:
        st.markdown('<div style="font-size:0.82rem;font-weight:700;color:#57606a;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:8px;">Input Satellite Image</div>', unsafe_allow_html=True)
        st.image(img_bytes, use_container_width=True)
        
    mask_arr = st.session_state.get("extracted_mask")
    with col_mask:
        st.markdown('<div style="font-size:0.82rem;font-weight:700;color:#57606a;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:8px;">Extracted Road Mask</div>', unsafe_allow_html=True)
        if mask_arr is not None:
            st.image(mask_arr, clamp=True, use_container_width=True)
        else:
            st.markdown('<div style="height:250px;background:#f6f8fa;border:1px dashed #d0d7de;border-radius:10px;display:flex;justify-content:center;align-items:center;color:#57606a;font-size:0.88rem;">'
                        'Click <b>Run Road Extraction</b> in the sidebar to run ML inference.'
                        '</div>', unsafe_allow_html=True)

    if mask_arr is not None:
        st.markdown("<br><hr>", unsafe_allow_html=True)
        st.markdown('<div class="section-header">⚙️ Topological Healing & Skeletonization</div>', unsafe_allow_html=True)
        st.caption("Apply morphological thinning and graph-theoretic bridging to heal occlusions and construct a NetworkX graph.")
        
        col_ctrls, col_explain = st.columns([1, 1])
        
        with col_ctrls:
            snap_dist = st.slider("Snap distance (pixels)", 1.0, 30.0, 10.0, step=1.0)
            merge_dist = st.slider("Merge distance (pixels)", 1.0, 20.0, 5.0, step=1.0)
            min_comp_size = st.slider("Min component size (nodes)", 2, 50, 10, step=1)
            simplify_tol = st.slider("Simplification tolerance (pixels)", 0.1, 10.0, 2.0, step=0.1)
            
            if st.button("🗺️ Build Routable Graph", use_container_width=True):
                with st.spinner("Extracting skeleton & healing topology..."):
                    try:
                        from argus.graph.builder import RoadGraphBuilderImpl
                        
                        graph_cfg = {
                            "cleaning": {
                                "remove_self_loops": True,
                                "remove_small_components": True,
                                "min_component_size": min_comp_size,
                                "merge_close_nodes": True,
                                "merge_distance": merge_dist,
                                "snap_endpoints": True,
                                "snap_distance": snap_dist,
                            },
                            "simplification": {
                                "enabled": True,
                                "tolerance": simplify_tol,
                            }
                        }
                        
                        builder = RoadGraphBuilderImpl(config=graph_cfg)
                        road_mask_obj = st.session_state["extracted_road_mask_obj"]
                        
                        # Reset all previous results when a new graph is created
                        st.session_state["criticality_result"] = None
                        st.session_state["simulation_result"] = None
                        st.session_state["route_result"] = None
                        st.session_state["route_comparison"] = None
                        st.session_state["route_modified_result"] = None
                        st.session_state["route_accessibility"] = None
                        
                        road_graph = builder.build(road_mask_obj)
                        st.session_state["graph"] = road_graph
                        st.session_state["graph_source"] = f"extracted_{st.session_state['uploaded_image_name']}"
                        st.success("Graph constructed successfully! Explore the other tabs to run simulation/routing.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to build graph: {e}")
                        
        with col_explain:
            st.markdown(
                """
                <div style="background:#f6f8fa;border:1px solid #d0d7de;border-radius:10px;padding:18px;height:100%;font-size:0.85rem;color:#24292f;">
                    <div style="font-weight:700;margin-bottom:8px;text-transform:uppercase;font-size:0.75rem;letter-spacing:0.04em;color:#57606a;">
                        Pipeline Explanation
                    </div>
                    <ul style="margin: 0; padding-left: 20px; line-height: 1.5;">
                        <li><b>Thinning:</b> Binary mask is thinned into a 1-pixel-wide centerline skeleton (nodes = intersections, edges = paths).</li>
                        <li><b>Snap distance:</b> Max radius to snap dangling road endpoints together. Helps bridge gaps caused by trees or shadows.</li>
                        <li><b>Merge distance:</b> Clusters nodes that are close to each other into a single junction, cleaning up topology.</li>
                        <li><b>Simplification:</b> Reduces redundant nodes along straight lines while preserving precise spatial alignment.</li>
                    </ul>
                </div>
                """,
                unsafe_allow_html=True
            )


if __name__ == "__main__":
    run_dashboard()
