# Dynamic Vietnam Routing

Research-oriented route planning on real Vietnamese OpenStreetMap networks. The project is
being delivered in correctness-gated phases. Phase 1 provides centralized config, real OSM
graph acquisition, validation, and deterministic caching. A working vertical slice now adds
an exact Dijkstra implementation plus a Streamlit/Folium click-to-route map. Traffic AI,
dynamic simulation, comparative algorithms, and experiments remain subsequent phases.

The design and mathematical correctness boundaries are in
[`docs/architecture.md`](docs/architecture.md), with engineering risks in
[`docs/risks.md`](docs/risks.md).

Hướng dẫn từng bước bằng tiếng Việt: [`HUONG_DAN_CHAY.md`](HUONG_DAN_CHAY.md).

## Phase 1 setup

Use Python 3.11–3.14. OSMnx's compiled transitive dependencies are usually easiest through
Conda; pip is supported when wheels exist for the platform.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pip install -e . --no-deps
```

Copy `.env.example` to `.env` if defaults need changing. Secrets must stay in `.env`.

Download the default real Hanoi car network (the first call requires internet and may take
several minutes; later calls use local GraphML):

```bash
python scripts/download_map.py
```

Choose another supported profile/place or force a refresh:

```bash
python scripts/download_map.py --vehicle motorbike
python scripts/download_map.py --place "Da Nang, Vietnam" --vehicle car
python scripts/download_map.py --force
```

Motorbike filtering respects explicit OSM access prohibitions on a best-effort basis. OSM
coverage is incomplete, so the graph is not a legal-navigation guarantee.

Run Phase 1 checks:

```bash
python -m pytest
python -m ruff check app scripts tests
```

Run the interactive route map:

```bash
streamlit run app/main.py
```

Click once in `Start` mode and once in `Destination` mode. The selected coordinates are
snapped to OSM road nodes, then the exact keyed route edges are drawn on the map.

## Repository layout

```text
app/
  config.py
  graph/                 # Phase 1: OSM loading, GraphML cache, validation
  algorithms/            # Shared API and Dijkstra vertical slice
  traffic/               # Phase 5 onward
  ai/                    # Phase 7 onward
  simulation/            # Phase 8 onward
  benchmark/             # Phase 10 onward
  ui/                    # Folium route rendering vertical slice
data/{graph,traffic,benchmark}/
docs/
models/
notebooks/
scripts/download_map.py
tests/
```

## Roadmap and commands

Commands are documented only when their scripts exist. Planned work follows the requested
phase order: routing contract and static algorithms; bidirectional/hierarchical search;
traffic snapshots; dynamic algorithms and D* Lite; ML prediction; vehicle simulation; UI;
experiments; final validation/reporting.

## Current limitations

- No traffic values in Phase 1: initialized edge attributes are explicitly free-flow only.
- OSM data quality and completeness vary; inferred speeds are not measured traffic speeds.
- Large administrative boundaries can stress Overpass. A smaller district/place query is a
  valid development fallback, while final experiments should pin and report the graph cache.
- Only Dijkstra is connected to the current UI; comparative and dynamic algorithms follow.
