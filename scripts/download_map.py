"""Download and cache a real OSM road graph for the configured study area."""

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import replace
from pathlib import Path

# Keep the documented direct-script command working without requiring an editable install.
if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import SUPPORTED_VEHICLE_PROFILES, load_settings
from app.graph.graph_utils import summarize_graph
from app.graph.osm_loader import GraphDownloadError, OSMGraphLoader


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--place", help="OSM geocoding query, e.g. 'Hanoi, Vietnam'")
    parser.add_argument("--vehicle", choices=sorted(SUPPORTED_VEHICLE_PROFILES))
    parser.add_argument("--force", action="store_true", help="Ignore an existing graph cache")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    settings = load_settings()
    map_config = replace(
        settings.map,
        place=args.place or settings.map.place,
        vehicle_profile=args.vehicle or settings.map.vehicle_profile,
    )
    settings = replace(settings, map=map_config)
    settings.ensure_directories()
    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    try:
        graph = OSMGraphLoader(settings).load_or_download(force_refresh=args.force)
    except GraphDownloadError as exc:
        logging.getLogger(__name__).error("%s", exc)
        return 1

    summary = summarize_graph(graph)
    print(f"Study area: {map_config.place}")
    print(f"Vehicle profile: {map_config.vehicle_profile}")
    print(f"Nodes: {summary.nodes:,}")
    print(f"Directed edges: {summary.directed_edges:,}")
    print(f"Total directed-edge length: {summary.total_length_km:,.1f} km")
    print(f"Weakly connected components: {summary.weakly_connected_components}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
