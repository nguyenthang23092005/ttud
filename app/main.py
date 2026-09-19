"""Interactive route map for the current end-to-end Phase 1/2 slice."""

from __future__ import annotations

import logging
from dataclasses import replace

import networkx as nx
import streamlit as st
from streamlit_folium import st_folium

from app.algorithms import Dijkstra, RouteResult, RoutingContext
from app.config import SUPPORTED_VEHICLE_PROFILES, load_settings
from app.graph.osm_loader import GraphDownloadError, OSMGraphLoader
from app.ui.map_view import Coordinate, build_route_map, nearest_node

logging.basicConfig(level=logging.INFO)
st.set_page_config(page_title="Vietnam Dynamic Routing", page_icon="🗺️", layout="wide")


@st.cache_resource(show_spinner=False)
def load_graph(place: str, vehicle_profile: str) -> nx.MultiDiGraph:
    """Load one cached/downloaded OSM graph per Streamlit process."""

    settings = load_settings()
    settings = replace(
        settings,
        map=replace(settings.map, place=place, vehicle_profile=vehicle_profile),
    )
    settings.ensure_directories()
    return OSMGraphLoader(settings).load_or_download()


def calculate_route(
    graph: nx.MultiDiGraph, start: Coordinate, destination: Coordinate
) -> RouteResult:
    source = nearest_node(graph, start)
    target = nearest_node(graph, destination)
    return Dijkstra().route(graph, source, target, RoutingContext())


def reset_points() -> None:
    st.session_state.start_point = None
    st.session_state.destination_point = None
    st.session_state.processed_click = None
    st.session_state.map_version = st.session_state.get("map_version", 0) + 1


def initialize_state() -> None:
    defaults = {
        "active_graph": None,
        "start_point": None,
        "destination_point": None,
        "processed_click": None,
        "map_version": 0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def main() -> None:
    initialize_state()
    settings = load_settings()
    st.title("🗺️ AI-Based Dynamic Routing – Vietnam")
    st.caption(
        "Click hai điểm trên bản đồ để chạy Dijkstra trên mạng đường OSM có hướng. "
        "Hiện tại edge cost là thời gian free-flow; traffic AI sẽ được nối ở phase sau."
    )

    with st.sidebar:
        st.header("Khu vực và phương tiện")
        place = st.text_input("OSM place", value=settings.map.place)
        vehicle = st.selectbox(
            "Vehicle profile",
            options=sorted(SUPPORTED_VEHICLE_PROFILES),
            index=sorted(SUPPORTED_VEHICLE_PROFILES).index(settings.map.vehicle_profile),
        )
        if st.button("Tải / mở graph", type="primary", use_container_width=True):
            st.session_state.active_graph = (place.strip(), vehicle)
            reset_points()
        st.divider()
        selection_mode = st.radio(
            "Click tiếp theo dùng làm",
            options=("Start", "Destination"),
            horizontal=True,
        )
        if st.button("Xóa hai điểm", use_container_width=True):
            reset_points()
            st.rerun()

    active_graph = st.session_state.active_graph
    if active_graph is None:
        st.info(
            "Chọn khu vực rồi nhấn **Tải / mở graph**. Để demo nhanh, dùng "
            "`Hoan Kiem District, Hanoi, Vietnam` (đã có cache trong workspace hiện tại)."
        )
        return

    try:
        with st.spinner("Đang mở graph OSM…"):
            graph = load_graph(*active_graph)
    except GraphDownloadError as exc:
        st.error(str(exc))
        return

    start = st.session_state.start_point
    destination = st.session_state.destination_point
    result: RouteResult | None = None
    if start is not None and destination is not None:
        try:
            result = calculate_route(graph, start, destination)
        except ValueError as exc:
            st.error(f"Dữ liệu edge không hợp lệ: {exc}")

    map_view = build_route_map(
        graph,
        start=start,
        destination=destination,
        result=result,
    )
    map_data = st_folium(
        map_view,
        height=650,
        use_container_width=True,
        returned_objects=["last_clicked"],
        key=f"route-map-{st.session_state.map_version}-{active_graph[0]}-{active_graph[1]}",
    )

    clicked = map_data.get("last_clicked")
    if clicked:
        click_token = (float(clicked["lat"]), float(clicked["lng"]))
        if click_token != st.session_state.processed_click:
            st.session_state.processed_click = click_token
            if selection_mode == "Start":
                st.session_state.start_point = click_token
            else:
                st.session_state.destination_point = click_token
            st.rerun()

    if result is not None:
        if not result.success:
            st.warning(result.error or "Không tìm thấy đường đi.")
        else:
            distance, eta, runtime, expanded = st.columns(4)
            distance.metric("Quãng đường", f"{result.total_distance_m / 1000:.2f} km")
            eta.metric("ETA free-flow", f"{result.estimated_travel_time_s / 60:.1f} phút")
            runtime.metric("Dijkstra runtime", f"{result.computation_time_ms:.2f} ms")
            expanded.metric("Expanded nodes", f"{result.expanded_nodes:,}")


if __name__ == "__main__":
    main()
