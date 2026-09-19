"""Folium helpers for road-route visualization."""

from __future__ import annotations

from typing import Any

import folium
import networkx as nx

from app.algorithms.base import RouteResult

Coordinate = tuple[float, float]


def graph_center(graph: nx.MultiDiGraph) -> Coordinate:
    """Return mean latitude/longitude for the loaded study graph."""

    node_count = graph.number_of_nodes()
    latitude = sum(float(data["y"]) for _, data in graph.nodes(data=True)) / node_count
    longitude = sum(float(data["x"]) for _, data in graph.nodes(data=True)) / node_count
    return latitude, longitude


def route_coordinates(graph: nx.MultiDiGraph, result: RouteResult) -> list[Coordinate]:
    """Convert exact keyed OSM edges to a continuous Folium polyline."""

    coordinates: list[Coordinate] = []
    for u, v, key in result.edge_path:
        data = graph.edges[u, v, key]
        geometry = data.get("geometry")
        if geometry is not None:
            segment = [(float(y), float(x)) for x, y in geometry.coords]
        else:
            segment = [
                (float(graph.nodes[u]["y"]), float(graph.nodes[u]["x"])),
                (float(graph.nodes[v]["y"]), float(graph.nodes[v]["x"])),
            ]
        if coordinates and segment and coordinates[-1] == segment[0]:
            coordinates.extend(segment[1:])
        else:
            coordinates.extend(segment)
    return coordinates


def build_route_map(
    graph: nx.MultiDiGraph,
    *,
    start: Coordinate | None,
    destination: Coordinate | None,
    result: RouteResult | None,
) -> folium.Map:
    """Build a readable OSM map with selection markers and an optional route."""

    map_view = folium.Map(location=graph_center(graph), zoom_start=14, control_scale=True)
    if start is not None:
        folium.Marker(
            start,
            tooltip="Start",
            icon=folium.Icon(color="green", icon="play"),
        ).add_to(map_view)
    if destination is not None:
        folium.Marker(
            destination,
            tooltip="Destination",
            icon=folium.Icon(color="red", icon="flag"),
        ).add_to(map_view)

    if result is not None and result.success and result.edge_path:
        coordinates = route_coordinates(graph, result)
        folium.PolyLine(
            coordinates,
            color="#1677ff",
            weight=7,
            opacity=0.9,
            tooltip=f"{result.total_distance_m / 1000:.2f} km",
        ).add_to(map_view)
        map_view.fit_bounds(coordinates)
    return map_view


def nearest_node(graph: nx.MultiDiGraph, point: Coordinate) -> Any:
    """Snap a latitude/longitude point to its nearest OSM road node."""

    import osmnx as ox

    latitude, longitude = point
    return ox.distance.nearest_nodes(graph, X=longitude, Y=latitude)
