import folium
import networkx as nx

from app.algorithms import Dijkstra, RouteResult, RoutingContext
from app.ui.map_view import build_route_map, route_coordinates


def routed_graph() -> tuple[nx.MultiDiGraph, RouteResult]:
    graph = nx.MultiDiGraph()
    graph.add_node(1, x=105.8500, y=21.0250)
    graph.add_node(2, x=105.8520, y=21.0270)
    graph.add_node(3, x=105.8550, y=21.0300)
    graph.add_edge(
        1,
        2,
        length=300.0,
        dynamic_cost_s=30.0,
        predicted_travel_time_s=30.0,
    )
    graph.add_edge(
        2,
        3,
        length=400.0,
        dynamic_cost_s=40.0,
        predicted_travel_time_s=40.0,
    )
    result = Dijkstra().route(graph, 1, 3, RoutingContext())
    return graph, result


def test_route_coordinates_follow_exact_edge_path() -> None:
    graph, result = routed_graph()

    coordinates = route_coordinates(graph, result)

    assert coordinates == [
        (21.0250, 105.8500),
        (21.0270, 105.8520),
        (21.0300, 105.8550),
    ]


def test_route_map_renders_markers_and_blue_polyline() -> None:
    graph, result = routed_graph()

    map_view = build_route_map(
        graph,
        start=(21.0250, 105.8500),
        destination=(21.0300, 105.8550),
        result=result,
    )
    html = map_view.get_root().render()

    assert isinstance(map_view, folium.Map)
    assert "Start" in html
    assert "Destination" in html
    assert "#1677ff" in html
    assert "0.70 km" in html
