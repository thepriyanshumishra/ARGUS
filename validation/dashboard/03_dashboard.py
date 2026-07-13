#!/usr/bin/env python3
"""Sprint -1 V3: Dashboard Feasibility.

Objective: Verify Streamlit + PyDeck can render a road network graph.

Methodology:
1. Create a synthetic road graph with lat/lon coordinates
2. Convert to GeoJSON for PyDeck layers
3. Build PyDeck GeoJsonLayer (edges) + ScatterplotLayer (nodes)
4. Wrap in st.pydeck_chart()
5. Launch Streamlit, verify it starts without errors
"""

import json
import sys
import time
import signal
import subprocess
from pathlib import Path

REPORT_PATH = Path(__file__).parent / "report.json"
APP_PATH = Path(__file__).parent / "dashboard_app.py"


def write_report(status, verdict, observations, notes, follow_up):
    report = {
        "experiment": "03_dashboard",
        "status": status,
        "verdict": verdict,
        "observations": observations,
        "notes": notes,
        "follow_up": follow_up,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2))
    print(f"\n=== V3 Report ===")
    print(json.dumps(report, indent=2))


def main():
    print("=== Sprint -1 V3: Dashboard Feasibility ===")
    print()

    observations = []
    notes = []
    follow_up = ""

    # Step 1: Check imports
    print("[INFO] Checking Streamlit + PyDeck imports ...")
    try:
        import streamlit as st
        st_version = st.__version__
        print(f"[OK] streamlit {st_version}")
        observations.append(f"streamlit {st_version}")
    except ImportError as e:
        write_report("fail", "fails", f"streamlit import failed: {e}",
                     "Package not installed", "Install streamlit in validation venv")
        return 1

    try:
        import pydeck as pdk
        pdk_version = pdk.__version__
        print(f"[OK] pydeck {pdk_version}")
        observations.append(f"pydeck {pdk_version}")
    except ImportError as e:
        write_report("fail", "fails", f"pydeck import failed: {e}",
                     "Package not installed", "Install pydeck in validation venv")
        return 1

    try:
        import pandas as pd
        print(f"[OK] pandas available")
    except ImportError as e:
        write_report("fail", "fails", f"pandas import failed: {e}",
                     "Package not installed", "Install pandas in validation venv")
        return 1

    # Step 2: Create synthetic road graph data
    print("[INFO] Creating synthetic road graph data ...")

    # Create a simple grid road network
    nodes_data = []
    edges_data = []
    node_id = 0

    # Center of demo area (New Delhi area)
    base_lat, base_lon = 28.6, 77.2

    # Create a 4x5 grid of intersections
    node_ids = {}
    for row in range(4):
        for col in range(5):
            lat = base_lat + row * 0.005
            lon = base_lon + col * 0.005
            nodes_data.append({
                "id": node_id,
                "lat": lat,
                "lon": lon,
                "criticality": 0.5 + 0.5 * (row * 5 + col) / 20  # mock criticality score
            })
            node_ids[(row, col)] = node_id
            node_id += 1

    # Horizontal edges
    for row in range(4):
        for col in range(4):
            u = node_ids[(row, col)]
            v = node_ids[(row, col + 1)]
            edges_data.append({
                "u": u, "v": v,
                "lat1": nodes_data[u]["lat"], "lon1": nodes_data[u]["lon"],
                "lat2": nodes_data[v]["lat"], "lon2": nodes_data[v]["lon"],
                "length_m": 555.0,  # ~0.005 deg in meters
                "name": f"Road_{row}_{col}"
            })

    # Vertical edges
    for row in range(3):
        for col in range(5):
            u = node_ids[(row, col)]
            v = node_ids[(row + 1, col)]
            edges_data.append({
                "u": u, "v": v,
                "lat1": nodes_data[u]["lat"], "lon1": nodes_data[u]["lon"],
                "lat2": nodes_data[v]["lat"], "lon2": nodes_data[v]["lon"],
                "length_m": 555.0,
                "name": f"Road_{row}_{col}_v"
            })

    observations.append(f"Synthetic graph: {len(nodes_data)} nodes, {len(edges_data)} edges")

    # Step 3: Build GeoJSON for PyDeck
    # GeoJsonLayer expects FeatureCollection with LineString geometries for edges
    # Build edge geometries as GeoJSON FeatureCollection
    edge_features = []
    for e in edges_data:
        edge_features.append({
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[e["lon1"], e["lat1"]], [e["lon2"], e["lat2"]]]
            },
            "properties": {
                "name": e["name"],
                "length_m": e["length_m"]
            }
        })

    edge_geojson = {
        "type": "FeatureCollection",
        "features": edge_features
    }

    # Build node dataframe for ScatterplotLayer
    node_df = pd.DataFrame(nodes_data)

    observations.append("GeoJSON FeatureCollection built successfully")

    # Step 4: Build PyDeck layers
    print("[INFO] Building PyDeck layers ...")
    try:
        edge_layer = pdk.Layer(
            "GeoJsonLayer",
            data=edge_geojson,
            get_line_color=[100, 180, 255, 200],
            get_line_width=3,
            pickable=True,
            auto_highlight=True,
        )
        observations.append("GeoJsonLayer created successfully")
    except Exception as e:
        write_report("fail", "fails", f"GeoJsonLayer creation failed: {e}",
                     "PyDeck API may have changed", "Check pydeck documentation")
        return 1

    try:
        node_layer = pdk.Layer(
            "ScatterplotLayer",
            data=node_df,
            get_position=["lon", "lat"],
            get_fill_color="[255, 100, 100, 200]",
            get_radius=50,
            pickable=True,
        )
        observations.append("ScatterplotLayer created successfully")
    except Exception as e:
        write_report("fail", "fails", f"ScatterplotLayer creation failed: {e}",
                     "PyDeck API may have changed", "Check pydeck documentation")
        return 1

    # Step 5: Build PyDeck deck
    try:
        view_state = pdk.ViewState(
            latitude=base_lat + 0.01,
            longitude=base_lon + 0.01,
            zoom=13,
            pitch=0,
        )
        deck = pdk.Deck(
            layers=[edge_layer, node_layer],
            initial_view_state=view_state,
            tooltip={"text": "{name}"},
        )
        observations.append("pdk.Deck created successfully")
    except Exception as e:
        write_report("fail", "fails", f"pdk.Deck creation failed: {e}",
                     "PyDeck API may have changed", "Check pydeck documentation")
        return 1

    # Step 6: Write the Streamlit app
    print("[INFO] Writing Streamlit dashboard app ...")
    app_code = f'''
import streamlit as st
import pydeck as pdk
import json

EDGE_GEOJSON = {json.dumps(edge_geojson)}
NODE_DATA = {node_df.to_json(orient="records")}

st.set_page_config(page_title="ARGUS V3 Validation", layout="wide")
st.title("ARGUS Dashboard Feasibility Test")
st.caption("Sprint -1 V3: Streamlit + PyDeck rendering validation")

# Build layers
edge_layer = pdk.Layer(
    "GeoJsonLayer",
    data=EDGE_GEOJSON,
    get_line_color=[100, 180, 255, 200],
    get_line_width=3,
    pickable=True,
    auto_highlight=True,
)

node_layer = pdk.Layer(
    "ScatterplotLayer",
    data=NODE_DATA,
    get_position=["lon", "lat"],
    get_fill_color="[255, 100, 100, 200]",
    get_radius=50,
    pickable=True,
)

view_state = pdk.ViewState(
    latitude={base_lat + 0.01},
    longitude={base_lon + 0.01},
    zoom=13,
    pitch=0,
)

deck = pdk.Deck(
    layers=[edge_layer, node_layer],
    initial_view_state=view_state,
    tooltip={{"text": "Node {{id}}: {{criticality}} criticality"}},
)

st.pydeck_chart(deck, use_container_width=True)
st.success("Dashboard renders successfully. Map should show road network.")
    '''
    APP_PATH.write_text(app_code)
    print(f"[OK] Dashboard app written to {APP_PATH}")

    # Step 7: Launch Streamlit and verify
    print("[INFO] Launching Streamlit app (5s validation) ...")
    import os
    env = os.environ.copy()
    env["VIRTUAL_ENV"] = str(Path(__file__).parent.parent / ".venv")

    try:
        proc = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", str(APP_PATH),
             "--server.headless", "true",
             "--server.port", "8502",
             "--server.enableCORS", "false",
             "--global.developmentMode", "false"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )

        # Wait for startup (up to 15s)
        start_time = time.time()
        startup_output = ""
        startup_ok = False

        while time.time() - start_time < 15:
            line = proc.stdout.readline() if proc.stdout else ""
            startup_output += line
            if "You can now view your Streamlit app" in line or "Network URL" in line:
                startup_ok = True
                print(f"[OK] Streamlit app started: {line.strip()}")
                observations.append("Streamlit app started successfully")
                break
            if "ERROR" in line.upper() or "Traceback" in line:
                print(f"[WARN] Streamlit error: {line.strip()}")
                notes.append(f"Streamlit stderr: {line.strip()[:100]}")

        if startup_ok:
            # Give it a moment to render
            time.sleep(2)
            proc.terminate()
            proc.wait(timeout=5)
            observations.append("st.pydeck_chart render initiated (visual check needed in browser)")
            verdict = "works"
            status = "pass"
        else:
            # Check if it's still running but slow
            if proc.poll() is None:
                print("[WARN] Streamlit started but didn't print success message within timeout")
                proc.terminate()
                proc.wait(timeout=5)
                observations.append("Streamlit process launched but startup message not captured")
                verdict = "works_with_issues"
                status = "pass"
                notes.append("Streamlit launched but startup message not detected within timeout")
            else:
                stderr_output = proc.stderr.read() if proc.stderr else ""
                print(f"[FAIL] Streamlit failed to start. stderr: {stderr_output[:300]}")
                observations.append(f"Streamlit failed to start")
                notes.append(f"stderr: {stderr_output[:300]}")
                verdict = "fails"
                status = "fail"

    except Exception as e:
        print(f"[FAIL] Streamlit subprocess error: {e}")
        notes.append(f"Subprocess error: {e}")
        verdict = "fails"
        status = "fail"

    write_report(status, verdict, "; ".join(observations), "; ".join(notes), follow_up)
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
