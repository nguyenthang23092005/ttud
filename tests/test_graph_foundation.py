from pathlib import Path

import networkx as nx
import pytest

from app.config import MapConfig
from app.graph.graph_cache import GraphCache, cache_key
from app.graph.graph_utils import (
    GraphValidationError,
    normalize_edge_attributes,
    summarize_graph,
    validate_road_graph,
)


def valid_graph() -> nx.MultiDiGraph:
    graph = nx.MultiDiGraph()
    graph.add_node(1, x=105.8, y=21.0)
    graph.add_node(2, x=105.9, y=21.1)
    graph.add_edge(1, 2, length=100.0, free_flow_travel_time_s=10.0)
    graph.add_edge(1, 2, length=120.0, free_flow_travel_time_s=12.0)
    return graph


def test_cache_key_changes_with_vehicle_profile() -> None:
    car = cache_key(MapConfig(vehicle_profile="car"))
    motorbike = cache_key(MapConfig(vehicle_profile="motorbike"))

    assert car != motorbike
    assert "hanoi-vietnam" in car


def test_cache_key_ignores_download_timeout() -> None:
    assert cache_key(MapConfig(request_timeout_seconds=60)) == cache_key(
        MapConfig(request_timeout_seconds=300)
    )


def test_graph_cache_path_is_inside_configured_directory() -> None:
    cache_directory = Path("data/graph")
    path = GraphCache(cache_directory).graph_path(MapConfig())

    assert path.parent == cache_directory
    assert path.suffix == ".graphml"


def test_validates_and_summarizes_directed_parallel_edges() -> None:
    graph = valid_graph()

    validate_road_graph(graph)
    summary = summarize_graph(graph)

    assert summary.nodes == 2
    assert summary.directed_edges == 2
    assert summary.parallel_edge_pairs == 1
    assert summary.total_length_km == pytest.approx(0.22)


def test_rejects_graph_without_coordinates() -> None:
    graph = valid_graph()
    del graph.nodes[1]["x"]

    with pytest.raises(GraphValidationError, match="coordinate"):
        validate_road_graph(graph)


def test_rejects_negative_edge_length() -> None:
    graph = valid_graph()
    graph.edges[1, 2, 0]["length"] = -1

    with pytest.raises(GraphValidationError, match="invalid length"):
        validate_road_graph(graph)


def test_normalization_initializes_dynamic_fields_from_free_flow() -> None:
    graph = nx.MultiDiGraph()
    graph.add_node(1, x=105.8, y=21.0)
    graph.add_node(2, x=105.9, y=21.1)
    graph.add_edge(1, 2, length=100.0)

    class FakeRouting:
        @staticmethod
        def add_edge_speeds(target: nx.MultiDiGraph) -> nx.MultiDiGraph:
            target.edges[1, 2, 0]["speed_kph"] = 36.0
            return target

        @staticmethod
        def add_edge_travel_times(target: nx.MultiDiGraph) -> nx.MultiDiGraph:
            target.edges[1, 2, 0]["travel_time"] = 10.0
            return target

    class FakeOsmnx:
        routing = FakeRouting()

    normalized = normalize_edge_attributes(graph, FakeOsmnx())
    edge = normalized.edges[1, 2, 0]

    assert edge["free_speed_kph"] == 36.0
    assert edge["predicted_travel_time_s"] == 10.0
    assert edge["dynamic_cost_s"] == 10.0
    assert edge["congestion_factor"] == 1.0
