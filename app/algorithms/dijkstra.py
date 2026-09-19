"""Heap-based Dijkstra implementation for directed OSM MultiDiGraphs."""

from __future__ import annotations

import heapq
import itertools
import math
import time
from typing import Any

import networkx as nx

from app.algorithms.base import EdgeId, Node, RouteResult, RoutingAlgorithm, RoutingContext


class Dijkstra(RoutingAlgorithm):
    """Exact shortest path for finite, non-negative scalar edge costs."""

    name = "Dijkstra"

    def route(
        self,
        graph: nx.MultiDiGraph,
        source: Node,
        target: Node,
        context: RoutingContext,
    ) -> RouteResult:
        started = time.perf_counter()
        if source not in graph or target not in graph:
            return self._failure(started, "Source or destination node is not in the graph")
        if source == target:
            return RouteResult(
                algorithm=self.name,
                success=True,
                path=[source],
                computation_time_ms=self._elapsed_ms(started),
                visited_nodes=1,
            )

        distances: dict[Node, float] = {source: 0.0}
        predecessor: dict[Node, EdgeId] = {}
        discovered: set[Node] = {source}
        expanded: set[Node] = set()
        sequence = itertools.count()
        frontier: list[tuple[float, int, Node]] = [(0.0, next(sequence), source)]

        while frontier:
            current_cost, _, node = heapq.heappop(frontier)
            if current_cost > distances.get(node, math.inf):
                continue
            if node in expanded:
                continue
            expanded.add(node)
            if node == target:
                edge_path = self._reconstruct(predecessor, source, target)
                return self._success(
                    graph,
                    edge_path,
                    current_cost,
                    started,
                    len(discovered),
                    len(expanded),
                )

            for neighbor, keyed_edges in graph.adj[node].items():
                for key, edge_data in keyed_edges.items():
                    weight = self._edge_weight(edge_data, context.weight, node, neighbor, key)
                    candidate = current_cost + weight
                    if candidate < distances.get(neighbor, math.inf):
                        distances[neighbor] = candidate
                        predecessor[neighbor] = (node, neighbor, key)
                        discovered.add(neighbor)
                        heapq.heappush(frontier, (candidate, next(sequence), neighbor))

        return self._failure(
            started,
            "No directed path exists between the selected points",
            visited_nodes=len(discovered),
            expanded_nodes=len(expanded),
        )

    @staticmethod
    def _edge_weight(
        edge_data: dict[str, Any], weight_name: str, u: Node, v: Node, key: Any
    ) -> float:
        try:
            weight = float(edge_data[weight_name])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Edge {(u, v, key)!r} has no valid {weight_name!r} cost") from exc
        if not math.isfinite(weight) or weight < 0:
            raise ValueError(f"Edge {(u, v, key)!r} has a negative or non-finite cost")
        return weight

    @staticmethod
    def _reconstruct(predecessor: dict[Node, EdgeId], source: Node, target: Node) -> list[EdgeId]:
        reversed_edges: list[EdgeId] = []
        node = target
        while node != source:
            edge = predecessor[node]
            reversed_edges.append(edge)
            node = edge[0]
        reversed_edges.reverse()
        return reversed_edges

    def _success(
        self,
        graph: nx.MultiDiGraph,
        edge_path: list[EdgeId],
        total_cost: float,
        started: float,
        visited_nodes: int,
        expanded_nodes: int,
    ) -> RouteResult:
        path = [edge_path[0][0], *(edge[1] for edge in edge_path)]
        total_distance_m = 0.0
        estimated_travel_time_s = 0.0
        for u, v, key in edge_path:
            data = graph.edges[u, v, key]
            total_distance_m += float(data["length"])
            estimated_travel_time_s += float(data["predicted_travel_time_s"])
        return RouteResult(
            algorithm=self.name,
            success=True,
            path=path,
            edge_path=edge_path,
            total_distance_m=total_distance_m,
            estimated_travel_time_s=estimated_travel_time_s,
            total_cost=total_cost,
            computation_time_ms=self._elapsed_ms(started),
            visited_nodes=visited_nodes,
            expanded_nodes=expanded_nodes,
        )

    def _failure(
        self,
        started: float,
        error: str,
        *,
        visited_nodes: int = 0,
        expanded_nodes: int = 0,
    ) -> RouteResult:
        return RouteResult(
            algorithm=self.name,
            success=False,
            computation_time_ms=self._elapsed_ms(started),
            visited_nodes=visited_nodes,
            expanded_nodes=expanded_nodes,
            error=error,
        )

    @staticmethod
    def _elapsed_ms(started: float) -> float:
        return (time.perf_counter() - started) * 1000.0
