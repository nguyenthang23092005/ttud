"""Deterministic, metadata-backed GraphML cache."""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from app.config import MapConfig

if TYPE_CHECKING:
    import networkx as nx


def _osmnx() -> Any:
    try:
        import osmnx as ox
    except ImportError as exc:
        raise RuntimeError(
            "OSMnx is required for graph I/O. Install dependencies with "
            "'python -m pip install -r requirements.txt'."
        ) from exc
    return ox


def cache_key(config: MapConfig) -> str:
    """Return a readable, collision-resistant key for graph-defining settings."""

    graph_parameters = asdict(config)
    # A network timeout changes acquisition behavior, not the graph requested.
    graph_parameters.pop("request_timeout_seconds")
    payload = json.dumps(graph_parameters, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]
    slug = re.sub(r"[^a-z0-9]+", "-", config.place.lower()).strip("-")[:48]
    return f"{slug}-{config.vehicle_profile}-{digest}"


class GraphCache:
    """Save/load OSMnx graphs without partially written cache files."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory

    def graph_path(self, config: MapConfig) -> Path:
        return self.directory / f"{cache_key(config)}.graphml"

    def metadata_path(self, config: MapConfig) -> Path:
        return self.directory / f"{cache_key(config)}.json"

    def exists(self, config: MapConfig) -> bool:
        return self.graph_path(config).is_file()

    def load(self, config: MapConfig) -> nx.MultiDiGraph:
        path = self.graph_path(config)
        if not path.is_file():
            raise FileNotFoundError(f"No cached graph at {path}")
        dynamic_float_fields = {
            "free_speed_kph": float,
            "estimated_speed_kph": float,
            "free_flow_travel_time_s": float,
            "predicted_travel_time_s": float,
            "traffic_level": float,
            "congestion_factor": float,
            "dynamic_cost_s": float,
        }
        graph = _osmnx().load_graphml(filepath=path, edge_dtypes=dynamic_float_fields)
        return graph

    def save(self, graph: nx.MultiDiGraph, config: MapConfig) -> Path:
        self.directory.mkdir(parents=True, exist_ok=True)
        graph_path = self.graph_path(config)
        metadata_path = self.metadata_path(config)
        temp_graph = graph_path.with_name(f".{graph_path.name}.tmp.graphml")
        temp_metadata = metadata_path.with_name(f".{metadata_path.name}.tmp")
        try:
            _osmnx().save_graphml(graph, filepath=temp_graph)
            metadata = {
                "cache_key": cache_key(config),
                "created_at_utc": datetime.now(UTC).isoformat(),
                "config": asdict(config),
                "nodes": graph.number_of_nodes(),
                "edges": graph.number_of_edges(),
            }
            temp_metadata.write_text(
                json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            os.replace(temp_graph, graph_path)
            os.replace(temp_metadata, metadata_path)
        finally:
            temp_graph.unlink(missing_ok=True)
            temp_metadata.unlink(missing_ok=True)
        return graph_path
