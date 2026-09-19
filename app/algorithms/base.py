"""Shared routing contracts and result metrics."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import networkx as nx

Node = Any
EdgeId = tuple[Node, Node, Any]


@dataclass(frozen=True, slots=True)
class RoutingContext:
    """Immutable settings shared by algorithms in one routing query."""

    weight: str = "dynamic_cost_s"


@dataclass(frozen=True, slots=True)
class RouteResult:
    """A route plus algorithm and route-quality measurements."""

    algorithm: str
    success: bool
    path: list[Node] = field(default_factory=list)
    edge_path: list[EdgeId] = field(default_factory=list)
    total_distance_m: float = 0.0
    estimated_travel_time_s: float = 0.0
    total_cost: float = 0.0
    computation_time_ms: float = 0.0
    visited_nodes: int = 0
    expanded_nodes: int = 0
    error: str | None = None


class RoutingAlgorithm(ABC):
    """Common API implemented by every routing algorithm."""

    name: str

    @abstractmethod
    def route(
        self,
        graph: nx.MultiDiGraph,
        source: Node,
        target: Node,
        context: RoutingContext,
    ) -> RouteResult:
        """Find a route on one immutable graph snapshot."""
