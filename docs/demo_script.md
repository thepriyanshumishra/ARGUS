# ARGUS Demo Script

Step-by-step walkthrough for hackathon judges (~5 minutes).

## Setup
1. Open terminal, run: `uv run argus dashboard`
2. Streamlit launches at `http://localhost:8501`

## Step 1: Load Demo Data (15 sec)
- Click **"Load Demo Data"** in the sidebar
- Dashboard loads pre-computed road graph, criticality analysis, simulation results, and a sample route
- All 6 tabs now have content ready

## Step 2: Overview Tab (30 sec)
- Click **"🏠 Overview"** tab
- Unified map shows road network, critical nodes (colour gradient), and route overlay
- Toggle checkboxes to show/hide layers individually
- Pipeline Summary metrics: 32 nodes, 40 edges, criticality ✓, simulation ✓, 1 route

> **Narrate**: "ARGUS transforms satellite imagery into an intelligent urban mobility graph. The overview shows all layers — road network, critical infrastructure highlighted, simulation impact, and routes — on a single map."

## Step 3: Road Network (20 sec)
- Click **"🗺️ Road Network"** tab
- Full road graph with node colour-coding (green=junctions, yellow=simple roads, red=leaf nodes)
- Stats panel: node count, edge count, connected components

> **Narrate**: "The Vision and Graph pipelines extracted and constructed this road graph from satellite imagery. Nodes are annotated with geographic coordinates."

## Step 4: Criticality Analysis (45 sec)
- Click **"📊 Criticality"** tab
- Select metric: betweenness, closeness, or degree
- Map colours nodes by centrality (green→red gradient)
- Red-bordered nodes = articulation points (removing them disconnects the graph)
- Red edges = bridges (sole connection between sub-networks)
- Stats: articulation points, bridges, average path length, vulnerability ratio
- Scroll down to see top-N ranked nodes

> **Narrate**: "Criticality analysis identifies infrastructure whose failure would cause maximum disruption. Betweenness centrality measures how many shortest paths pass through each node — the reddest nodes are the system's chokepoints."

## Step 5: Disaster Simulation (45 sec)
- Click **"🌊 Simulation"** tab
- (Optional) Re-run from sidebar: select scenario (flood_zone_a, bridge_collapse, road_blockage), adjust severity slider
- Left map: original network (Before)
- Right map: modified network (After) — red dashed = removed edges, red circles = destroyed nodes, orange = partially damaged, shaded polygon = affected region
- Impact stats: nodes removed, edges removed, connected components before vs after, road blockage severity

> **Narrate**: "ARGUS simulates disasters — flood zones, bridge collapses, road blockages — and shows the cascading impact. Decision-makers see exactly which routes become unavailable and whether the city fragments into disconnected islands."

## Step 6: Routing & Rerouting (45 sec)
- Enter origin and destination in sidebar (e.g., `-10.0,27.0` and `-43.0,121.0` for demo data)
- Select algorithm (dijkstra/astar/k_shortest)
- Check "Compare against simulated graph" to see reroute
- Check "Show accessibility" to highlight reachable/unreachable areas
- Click **"🛣️ Find Route"**
- Map shows: thin grey background roads, coloured thick route line, green origin marker, red destination marker
- If simulation comparison enabled: side-by-side baseline vs rerouted path
- Reroute comparison table: baseline length, modified length, delta, status (detour/unreachable/unchanged)
- Route details table with length, travel time, node count per route

> **Narrate**: "After a disaster, emergency vehicles need alternative routes. ARGUS computes the shortest path using Dijkstra or A*, shows how the route changes after simulation, and identifies newly unreachable destinations."

## Step 7: Full Report & Export (20 sec)
- Click **"📋 Report"** tab to view raw JSON criticality report
- Click "📥 Download JSON Report" to save
- From sidebar **"5. Export All"**: downloads ZIP containing criticality_report.json, simulation_impact.json, routes.geojson

> **Narrate**: "All results are exportable for integration with external GIS tools and emergency response planning systems."

## Closing
Total: ~4 minutes demo flow.

**Key message**: ARGUS is not just a road extractor — it's a complete decision-support platform that answers: which roads are critical, what happens when they fail, and where should emergency vehicles go instead.

## Troubleshooting
- If blank map: run `Load Demo Data` first
- If simulation shows 0 damage: demo graph uses synthetic pixel-space coordinates; flood polygon doesn't overlap. For real demo, use geographic-coordinate graph data
- If `uv run argus dashboard` fails: check `.venv` is active, `streamlit` and `streamlit-folium` are installed