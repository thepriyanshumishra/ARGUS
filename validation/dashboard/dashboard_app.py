import pydeck as pdk
import streamlit as st

EDGE_GEOJSON = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": [[77.2, 28.6], [77.205, 28.6]]},
            "properties": {"name": "Road_0_0", "length_m": 555.0},
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[77.205, 28.6], [77.21000000000001, 28.6]],
            },
            "properties": {"name": "Road_0_1", "length_m": 555.0},
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[77.21000000000001, 28.6], [77.215, 28.6]],
            },
            "properties": {"name": "Road_0_2", "length_m": 555.0},
        },
        {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": [[77.215, 28.6], [77.22, 28.6]]},
            "properties": {"name": "Road_0_3", "length_m": 555.0},
        },
        {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": [[77.2, 28.605], [77.205, 28.605]]},
            "properties": {"name": "Road_1_0", "length_m": 555.0},
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[77.205, 28.605], [77.21000000000001, 28.605]],
            },
            "properties": {"name": "Road_1_1", "length_m": 555.0},
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[77.21000000000001, 28.605], [77.215, 28.605]],
            },
            "properties": {"name": "Road_1_2", "length_m": 555.0},
        },
        {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": [[77.215, 28.605], [77.22, 28.605]]},
            "properties": {"name": "Road_1_3", "length_m": 555.0},
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[77.2, 28.610000000000003], [77.205, 28.610000000000003]],
            },
            "properties": {"name": "Road_2_0", "length_m": 555.0},
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [77.205, 28.610000000000003],
                    [77.21000000000001, 28.610000000000003],
                ],
            },
            "properties": {"name": "Road_2_1", "length_m": 555.0},
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [77.21000000000001, 28.610000000000003],
                    [77.215, 28.610000000000003],
                ],
            },
            "properties": {"name": "Road_2_2", "length_m": 555.0},
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[77.215, 28.610000000000003], [77.22, 28.610000000000003]],
            },
            "properties": {"name": "Road_2_3", "length_m": 555.0},
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[77.2, 28.615000000000002], [77.205, 28.615000000000002]],
            },
            "properties": {"name": "Road_3_0", "length_m": 555.0},
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [77.205, 28.615000000000002],
                    [77.21000000000001, 28.615000000000002],
                ],
            },
            "properties": {"name": "Road_3_1", "length_m": 555.0},
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [77.21000000000001, 28.615000000000002],
                    [77.215, 28.615000000000002],
                ],
            },
            "properties": {"name": "Road_3_2", "length_m": 555.0},
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[77.215, 28.615000000000002], [77.22, 28.615000000000002]],
            },
            "properties": {"name": "Road_3_3", "length_m": 555.0},
        },
        {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": [[77.2, 28.6], [77.2, 28.605]]},
            "properties": {"name": "Road_0_0_v", "length_m": 555.0},
        },
        {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": [[77.205, 28.6], [77.205, 28.605]]},
            "properties": {"name": "Road_0_1_v", "length_m": 555.0},
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[77.21000000000001, 28.6], [77.21000000000001, 28.605]],
            },
            "properties": {"name": "Road_0_2_v", "length_m": 555.0},
        },
        {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": [[77.215, 28.6], [77.215, 28.605]]},
            "properties": {"name": "Road_0_3_v", "length_m": 555.0},
        },
        {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": [[77.22, 28.6], [77.22, 28.605]]},
            "properties": {"name": "Road_0_4_v", "length_m": 555.0},
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[77.2, 28.605], [77.2, 28.610000000000003]],
            },
            "properties": {"name": "Road_1_0_v", "length_m": 555.0},
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[77.205, 28.605], [77.205, 28.610000000000003]],
            },
            "properties": {"name": "Road_1_1_v", "length_m": 555.0},
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [77.21000000000001, 28.605],
                    [77.21000000000001, 28.610000000000003],
                ],
            },
            "properties": {"name": "Road_1_2_v", "length_m": 555.0},
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[77.215, 28.605], [77.215, 28.610000000000003]],
            },
            "properties": {"name": "Road_1_3_v", "length_m": 555.0},
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[77.22, 28.605], [77.22, 28.610000000000003]],
            },
            "properties": {"name": "Road_1_4_v", "length_m": 555.0},
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[77.2, 28.610000000000003], [77.2, 28.615000000000002]],
            },
            "properties": {"name": "Road_2_0_v", "length_m": 555.0},
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[77.205, 28.610000000000003], [77.205, 28.615000000000002]],
            },
            "properties": {"name": "Road_2_1_v", "length_m": 555.0},
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [77.21000000000001, 28.610000000000003],
                    [77.21000000000001, 28.615000000000002],
                ],
            },
            "properties": {"name": "Road_2_2_v", "length_m": 555.0},
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[77.215, 28.610000000000003], [77.215, 28.615000000000002]],
            },
            "properties": {"name": "Road_2_3_v", "length_m": 555.0},
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[77.22, 28.610000000000003], [77.22, 28.615000000000002]],
            },
            "properties": {"name": "Road_2_4_v", "length_m": 555.0},
        },
    ],
}
NODE_DATA = [
    {"id": 0, "lat": 28.6, "lon": 77.2, "criticality": 0.5},
    {"id": 1, "lat": 28.6, "lon": 77.205, "criticality": 0.525},
    {"id": 2, "lat": 28.6, "lon": 77.21, "criticality": 0.55},
    {"id": 3, "lat": 28.6, "lon": 77.215, "criticality": 0.575},
    {"id": 4, "lat": 28.6, "lon": 77.22, "criticality": 0.6},
    {"id": 5, "lat": 28.605, "lon": 77.2, "criticality": 0.625},
    {"id": 6, "lat": 28.605, "lon": 77.205, "criticality": 0.65},
    {"id": 7, "lat": 28.605, "lon": 77.21, "criticality": 0.675},
    {"id": 8, "lat": 28.605, "lon": 77.215, "criticality": 0.7},
    {"id": 9, "lat": 28.605, "lon": 77.22, "criticality": 0.725},
    {"id": 10, "lat": 28.61, "lon": 77.2, "criticality": 0.75},
    {"id": 11, "lat": 28.61, "lon": 77.205, "criticality": 0.775},
    {"id": 12, "lat": 28.61, "lon": 77.21, "criticality": 0.8},
    {"id": 13, "lat": 28.61, "lon": 77.215, "criticality": 0.825},
    {"id": 14, "lat": 28.61, "lon": 77.22, "criticality": 0.85},
    {"id": 15, "lat": 28.615, "lon": 77.2, "criticality": 0.875},
    {"id": 16, "lat": 28.615, "lon": 77.205, "criticality": 0.9},
    {"id": 17, "lat": 28.615, "lon": 77.21, "criticality": 0.925},
    {"id": 18, "lat": 28.615, "lon": 77.215, "criticality": 0.95},
    {"id": 19, "lat": 28.615, "lon": 77.22, "criticality": 0.975},
]

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
    latitude=28.610000000000003,
    longitude=77.21000000000001,
    zoom=13,
    pitch=0,
)

deck = pdk.Deck(
    layers=[edge_layer, node_layer],
    initial_view_state=view_state,
    tooltip={"text": "Node {id}: {criticality} criticality"},
)

st.pydeck_chart(deck, use_container_width=True)
st.success("Dashboard renders successfully. Map should show road network.")
