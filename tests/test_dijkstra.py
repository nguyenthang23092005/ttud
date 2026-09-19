import networkx as nx
import pytest

from app.algorithms import Dijkstra, RoutingContext


def add_edge(
    graph: nx.MultiDiGraph,
    u: int,
    v: int,
    *,
    cost: float,
    length: float | None = None,
) -> int:
    return graph.add_edge(
        u,
        v,
        dynamic_cost_s=cost,
        predicted_travel_time_s=cost,
        length=cost if length is None else length,
    )


def test_dijkstra_finds_exact_directed_shortest_path() -> None:
    graph = nx.MultiDiGraph()
    add_edge(graph, 1, 2, cost=2)
    add_edge(graph, 2, 4, cost=2)
    add_edge(graph, 1, 3, cost=1)
    add_edge(graph, 3, 4, cost=10)

    result = Dijkstra().route(graph, 1, 4, RoutingContext())

    assert result.success
    assert result.path == [1, 2, 4]
    assert result.total_cost == pytest.approx(4)


def test_dijkstra_preserves_best_parallel_edge_key() -> None:
    graph = nx.MultiDiGraph()
    slow_key = add_edge(graph, 1, 2, cost=20, length=50)
    fast_key = add_edge(graph, 1, 2, cost=5, length=100)
    add_edge(graph, 2, 3, cost=2, length=25)

    result = Dijkstra().route(graph, 1, 3, RoutingContext())

    assert result.success
    assert result.edge_path[0] == (1, 2, fast_key)
    assert result.edge_path[0] != (1, 2, slow_key)
    assert result.total_distance_m == pytest.approx(125)


def test_dijkstra_respects_one_way_edges_and_reports_no_path() -> None:
    graph = nx.MultiDiGraph()
    add_edge(graph, 1, 2, cost=1)

    result = Dijkstra().route(graph, 2, 1, RoutingContext())

    assert not result.success
    assert result.error is not None


def test_dijkstra_source_equals_target() -> None:
    graph = nx.MultiDiGraph()
    graph.add_node(1)

    result = Dijkstra().route(graph, 1, 1, RoutingContext())

    assert result.success
    assert result.path == [1]
    assert result.total_cost == 0


def test_dijkstra_rejects_negative_cost() -> None:
    graph = nx.MultiDiGraph()
    add_edge(graph, 1, 2, cost=-1)

    with pytest.raises(ValueError, match="negative"):
        Dijkstra().route(graph, 1, 2, RoutingContext())
