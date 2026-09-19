"""Download real OSM street networks and reuse a deterministic local cache."""

from __future__ import annotations

import logging
from typing import Any

import networkx as nx

from app.config import MapConfig, Settings
from app.graph.graph_cache import GraphCache
from app.graph.graph_utils import normalize_edge_attributes, validate_road_graph

LOGGER = logging.getLogger(__name__)

# Best-effort OSM tag filter, not a claim about legal motorcycle access in Vietnam.
# Explicit OSM access prohibitions are respected; missing tags remain unknown.
MOTORBIKE_CUSTOM_FILTER = (
    '["highway"]'
    '["area"!~"yes"]'
    '["access"!~"private|no"]'
    '["motor_vehicle"!~"no"]'
    '["motorcycle"!~"no"]'
    '["highway"!~"footway|pedestrian|path|steps|cycleway|bridleway|corridor|'
    'construction|proposed|platform|raceway"]'
)


class GraphDownloadError(RuntimeError):
    """Raised when no cached graph exists and OSM acquisition fails."""


def _import_osmnx() -> Any:
    try:
        import osmnx as ox
    except ImportError as exc:
        raise GraphDownloadError(
            "OSMnx is not installed. Run 'python -m pip install -r requirements.txt'."
        ) from exc
    return ox


class OSMGraphLoader:
    """Cache-first loader for car and best-effort motorbike OSM networks."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.cache = GraphCache(settings.graph_cache_dir)

    def load_or_download(self, *, force_refresh: bool = False) -> nx.MultiDiGraph:
        config = self.settings.map
        if not force_refresh and self.cache.exists(config):
            LOGGER.info("Loading cached OSM graph from %s", self.cache.graph_path(config))
            graph = self.cache.load(config)
            validate_road_graph(graph)
            return graph

        graph = self._download(config)
        validate_road_graph(graph)
        path = self.cache.save(graph, config)
        LOGGER.info("Cached OSM graph at %s", path)
        return graph

    def _download(self, config: MapConfig) -> nx.MultiDiGraph:
        ox = _import_osmnx()
        ox.settings.requests_timeout = config.request_timeout_seconds
        ox.settings.use_cache = True
        # Keep OSMnx's HTTP response cache with project data instead of polluting cwd.
        ox.settings.cache_folder = self.settings.graph_cache_dir / "http"
        ox.settings.log_console = False
        kwargs: dict[str, object] = {
            "query": config.place,
            "simplify": config.simplify,
            "retain_all": config.retain_all,
            "truncate_by_edge": config.truncate_by_edge,
        }
        if config.vehicle_profile == "car":
            kwargs["network_type"] = "drive"
        else:
            kwargs["network_type"] = "all"
            kwargs["custom_filter"] = MOTORBIKE_CUSTOM_FILTER

        LOGGER.info("Downloading %s OSM graph for %s", config.vehicle_profile, config.place)
        try:
            graph = ox.graph.graph_from_place(**kwargs)
            graph = normalize_edge_attributes(graph, ox)
        except Exception as exc:
            cache_hint = self.cache.graph_path(config)
            raise GraphDownloadError(
                f"Could not download OSM graph for {config.place!r}. Check the place name, "
                f"internet/Overpass availability, or provide cache file {cache_hint}."
            ) from exc

        graph.graph.update(
            {
                "study_area": config.place,
                "vehicle_profile": config.vehicle_profile,
                "traffic_data_kind": "none_free_flow_only",
                "motorbike_access_limitation": (
                    "OSM-tag best effort; absent motorcycle restrictions are unknown"
                    if config.vehicle_profile == "motorbike"
                    else "not_applicable"
                ),
            }
        )
        return graph
