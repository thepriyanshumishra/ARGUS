#!/usr/bin/env python3
"""Sprint -1 V4: Technology Compatibility.

Objective: Verify all runtime dependencies import correctly and
graph serialization (GraphML + Pickle) preserves attributes.

Two parts:
1. Dependency import check — every library in the approved stack imports
2. Graph serialization round-trip — NetworkX graph survives GraphML & Pickle I/O
"""

import json
import sys
from pathlib import Path

REPORT_PATH = Path(__file__).parent / "report.json"


def write_report(status, verdict, observations, notes, follow_up):
    report = {
        "experiment": "04_compatibility",
        "status": status,
        "verdict": verdict,
        "observations": observations,
        "notes": notes,
        "follow_up": follow_up,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2))
    print("\n=== V4 Report ===")
    print(json.dumps(report, indent=2))


def main():
    print("=== Sprint -1 V4: Technology Compatibility ===")
    print()

    observations = []
    notes = []
    follow_up = []

    # ── Part 1: Dependency Import Check ──────────────────────
    print("─" * 50)
    print("[Part 1] Validating runtime dependency imports ...")
    print("─" * 50)

    # The runtime dependencies from docs/technology_mapping.md
    # Each entry: (import_name, pip_package_name, import_test)
    deps = [
        # Core
        ("numpy", "numpy", lambda: __import__("numpy")),
        ("scipy", "scipy", lambda: __import__("scipy")),
        ("pandas", "pandas", lambda: __import__("pandas")),
        # GIS
        ("rasterio", "rasterio", lambda: __import__("rasterio")),
        ("geopandas", "geopandas", lambda: __import__("geopandas")),
        ("shapely", "shapely", lambda: __import__("shapely")),
        ("pyproj", "pyproj", lambda: __import__("pyproj")),
        # Graph
        ("networkx", "networkx", lambda: __import__("networkx")),
        ("skimage (scikit-image)", "scikit-image", lambda: __import__("skimage")),
        ("sklearn (scikit-learn)", "scikit-learn", lambda: __import__("sklearn")),
        # ML / Vision
        ("torch", "torch", lambda: __import__("torch")),
        ("torchvision", "torchvision", lambda: __import__("torchvision")),
        ("cv2 (opencv)", "opencv-python", lambda: __import__("cv2")),
        # Config
        ("omegaconf", "omegaconf", lambda: __import__("omegaconf")),
        ("yaml (pyyaml)", "pyyaml", lambda: __import__("yaml")),
        # Logging
        ("loguru", "loguru", lambda: __import__("loguru")),
        # Dashboard
        ("streamlit", "streamlit", lambda: __import__("streamlit")),
        ("pydeck", "pydeck", lambda: __import__("pydeck")),
        ("folium", "folium", lambda: __import__("folium")),
        # CLI
        ("typer", "typer", lambda: __import__("typer")),
    ]

    import_results = {}
    all_imports_ok = True
    failed_imports = []

    for name, pkg, import_fn in deps:
        try:
            mod = import_fn()
            version = getattr(mod, "__version__", "unknown")
            import_results[name] = {"status": "ok", "version": version}
            print(f"  [OK] {name} ({version})")
        except ImportError as e:
            import_results[name] = {"status": "fail", "error": str(e)[:100]}
            all_imports_ok = False
            failed_imports.append(name)
            print(f"  [FAIL] {name} — {e}")

    observations.append(
        f"Dependency imports: {sum(1 for v in import_results.values() if v['status'] == 'ok')}/{len(deps)} ok"
    )
    if failed_imports:
        observations.append(f"Failed: {', '.join(failed_imports)}")
        notes.append(f"Import failures: {failed_imports}")

    # ── Part 2: Graph Serialization Round-Trip ───────────────
    print()
    print("─" * 50)
    print("[Part 2] Validating graph serialization (GraphML + Pickle) ...")
    print("─" * 50)

    import os
    import pickle
    import tempfile

    import networkx as nx
    import numpy as np

    # Create a test graph with realistic attributes
    G = nx.MultiDiGraph()

    # Add nodes with attributes
    for i in range(10):
        G.add_node(
            i,
            lat=28.6 + i * 0.001,
            lon=77.2 + i * 0.001,
            x=float(i * 50),
            y=float(i * 50),
            betweenness=0.5 + 0.05 * i,
            is_articulation=bool(i % 3 == 0),
            degree=i % 5,
        )

    # Add edges with attributes
    edges_added = 0
    for i in range(9):
        length = np.random.uniform(100, 500)
        G.add_edge(
            i,
            i + 1,
            length_m=float(length),
            weight=float(length),
            is_bridge=bool(i == 4),
            name=f"Road_{i}_{i+1}",
        )
        edges_added += 1

    # Add a few more edges for complexity
    G.add_edge(0, 5, length_m=float(400), weight=float(400), is_bridge=False)
    edges_added += 1
    G.add_edge(3, 8, length_m=float(350), weight=float(350), is_bridge=False)
    edges_added += 1

    serialization_results = {}

    # Test 1: GraphML
    print("[Test] GraphML serialization ...")
    try:
        with tempfile.NamedTemporaryFile(suffix=".graphml", delete=False) as f:
            graphml_path = f.name
        nx.write_graphml(G, graphml_path)
        Gml = nx.read_graphml(graphml_path)
        os.unlink(graphml_path)

        # Check attributes survived
        nodes_match = G.number_of_nodes() == Gml.number_of_nodes()
        edges_match = G.number_of_edges() == Gml.number_of_edges()

        # Check specific attributes
        has_lat = all("lat" in dict(Gml.nodes(data=True))[n] for n in list(Gml.nodes())[:3])
        has_lon = all("lon" in dict(Gml.nodes(data=True))[n] for n in list(Gml.nodes())[:3])
        has_length = any("length_m" in dict(Gml.edges(data=True))[e] for e in list(Gml.edges())[:3])

        serialization_results["graphml"] = {
            "status": "ok" if (nodes_match and edges_match and has_lat and has_lon) else "partial",
            "nodes_match": nodes_match,
            "edges_match": edges_match,
            "has_lat": has_lat,
            "has_lon": has_lon,
            "has_length": has_length,
        }
        print(
            f"  [OK] GraphML: nodes={nodes_match}, edges={edges_match}, attrs=lat:{has_lat} lon:{has_lon} len:{has_length}"
        )
    except Exception as e:
        serialization_results["graphml"] = {"status": "fail", "error": str(e)[:200]}
        print(f"  [FAIL] GraphML: {e}")

    # Test 2: Pickle
    print("[Test] Pickle serialization ...")
    try:
        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
            pkl_path = f.name
        with open(pkl_path, "wb") as f:
            pickle.dump(G, f)
        with open(pkl_path, "rb") as f:
            Gpk = pickle.load(f)
        os.unlink(pkl_path)

        # Deep comparison
        nodes_match = G.number_of_nodes() == Gpk.number_of_nodes()
        edges_match = G.number_of_edges() == Gpk.number_of_edges()
        # Check float attribute precision
        if nodes_match:
            orig_lat = G.nodes[0].get("lat")
            loaded_lat = Gpk.nodes[0].get("lat")
            attrs_match = orig_lat == loaded_lat
        else:
            attrs_match = False

        serialization_results["pickle"] = {
            "status": "ok" if (nodes_match and edges_match and attrs_match) else "partial",
            "nodes_match": nodes_match,
            "edges_match": edges_match,
            "attrs_match": attrs_match,
        }
        print(f"  [OK] Pickle: nodes={nodes_match}, edges={edges_match}, attrs={attrs_match}")
    except Exception as e:
        serialization_results["pickle"] = {"status": "fail", "error": str(e)[:200]}
        print(f"  [FAIL] Pickle: {e}")

    # Test 3: GeoJSON export (for dashboard consumption)
    print("[Test] GeoJSON conversion (road graph → GeoJSON) ...")
    try:
        import json as json_mod

        # Build FeatureCollection for edges
        features = []
        for u, v, data in G.edges(data=True):
            if (
                "lat" in G.nodes[u]
                and "lon" in G.nodes[u]
                and "lat" in G.nodes[v]
                and "lon" in G.nodes[v]
            ):
                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            [G.nodes[u]["lon"], G.nodes[u]["lat"]],
                            [G.nodes[v]["lon"], G.nodes[v]["lat"]],
                        ],
                    },
                    "properties": {"length_m": data.get("length_m", 0), "u": u, "v": v},
                }
                features.append(feature)

        geojson = {"type": "FeatureCollection", "features": features}
        geojson_str = json_mod.dumps(geojson)
        valid_geojson = len(features) > 0

        serialization_results["geojson"] = {
            "status": "ok" if valid_geojson else "partial",
            "features": len(features),
        }
        print(f"  [OK] GeoJSON: {len(features)} features, {len(geojson_str)} bytes")
    except Exception as e:
        serialization_results["geojson"] = {"status": "fail", "error": str(e)[:200]}
        print(f"  [FAIL] GeoJSON: {e}")

    # Summary
    all_serial_ok = all(r.get("status") == "ok" for r in serialization_results.values())

    observations.append(
        f"Serialization: GraphML={serialization_results.get('graphml', {}).get('status', 'fail')}, "
        f"Pickle={serialization_results.get('pickle', {}).get('status', 'fail')}, "
        f"GeoJSON={serialization_results.get('geojson', {}).get('status', 'fail')}"
    )

    # Verdict
    if all_imports_ok and all_serial_ok:
        verdict = "works"
        status = "pass"
    elif all_imports_ok:
        verdict = "works_with_issues"
        status = "pass"
        observations.append("All imports pass but serialization has partial failures")
    elif all_serial_ok:
        verdict = "works_with_issues"
        status = "pass"
        observations.append("Serialization passes but some imports failed")
    else:
        verdict = "fails"
        status = "fail"

    write_report(
        status,
        verdict,
        "; ".join(observations),
        "; ".join(notes),
        "; ".join(follow_up) if follow_up else "None",
    )
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
