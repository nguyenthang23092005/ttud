"""Road graph validation, normalization, and summary utilities."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import networkx as nx


class GraphValidationError(ValueError):
    """Raised when a graph cannot safely be used by routing algorithms."""


@dataclass(frozen=True, slots=True)
class GraphSummary:
    nodes: int
    directed_edges: int
    parallel_edge_pairs: int
    total_length_km: float
    strongly_connected_components: int
    weakly_connected_components: int


def validate_road_graph(graph: nx.MultiDiGraph) -> None:
    """Validate structural and numeric invariants needed by later phases."""

    if not isinstance(graph, nx.MultiDiGraph) or not graph.is_directed():
        raise GraphValidationError("Road graph must be a directed NetworkX MultiDiGraph")
    if graph.number_of_nodes() == 0:
        raise GraphValidationError("Road graph has no nodes")

    for node, data in graph.nodes(data=True):
        for coordinate in ("x", "y"):
            value = data.get(coordinate)
            if value is None or not math.isfinite(float(value)):
                raise GraphValidationError(f"Node {node!r} has invalid {coordinate} coordinate")

    for u, v, key, data in graph.edges(keys=True, data=True):
        length = data.get("length")
        if length is None or not math.isfinite(float(length)) or float(length) < 0:
            raise GraphValidationError(f"Edge {(u, v, key)!r} has invalid length")
        travel_time = data.get("free_flow_travel_time_s")
        if travel_time is None or not math.isfinite(float(travel_time)) or float(travel_time) < 0:
            raise GraphValidationError(f"Edge {(u, v, key)!r} has invalid travel time")


def normalize_edge_attributes(graph: nx.MultiDiGraph, ox: Any) -> nx.MultiDiGraph:
    """Add free-flow speed/time plus future dynamic-cost fields in SI units.

    OSMnx imputes missing speeds from highway-type aggregates. The original
    ``maxspeed`` tag remains intact, so measured and imputed information are not
    confused in later research phases.
    """

    graph = ox.routing.add_edge_speeds(graph)
    graph = ox.routing.add_edge_travel_times(graph)
    for _, _, _, data in graph.edges(keys=True, data=True):
        free_speed_kph = float(data["speed_kph"])
        free_time_s = float(data["travel_time"])
        data["free_speed_kph"] = free_speed_kph
        data["estimated_speed_kph"] = free_speed_kph
        data["free_flow_travel_time_s"] = free_time_s
        data["predicted_travel_time_s"] = free_time_s
        data["traffic_level"] = 0.0
        data["congestion_factor"] = 1.0
        data["dynamic_cost_s"] = free_time_s
    return graph


def summarize_graph(graph: nx.MultiDiGraph) -> GraphSummary:
    # Each edge in a parallel bundle appears in the iterator; count unique pairs instead.
    parallel_pairs = len({(u, v) for u, v in graph.edges() if graph.number_of_edges(u, v) > 1})
    return GraphSummary(
        nodes=graph.number_of_nodes(),
        directed_edges=graph.number_of_edges(),
        parallel_edge_pairs=parallel_pairs,
        total_length_km=sum(float(data["length"]) for *_, data in graph.edges(data=True)) / 1000.0,
        strongly_connected_components=nx.number_strongly_connected_components(graph),
        weakly_connected_components=nx.number_weakly_connected_components(graph),
    )
