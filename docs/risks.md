# Technical risks and mitigations

| Risk | Consequence | Mitigation |
|---|---|---|
| Overpass/geocoder availability and large Hanoi boundary | Slow or failed first download | Cache-first GraphML, actionable errors, configurable place; document smaller pilot areas |
| Incomplete OSM `maxspeed` and access tags | Biased time estimates or uncertain motorbike legality | Retain source tags, record imputation, disclose motorbike uncertainty |
| Parallel OSM edges | Wrong cost/path reconstruction if `(u,v)` is treated as unique | Keep `MultiDiGraph`; every algorithm will track `(u,v,key)` |
| Inadmissible A* heuristic under mixed objectives | Incorrect optimality claim | Derive lower bounds per objective; fall back to zero |
| Snapshot traffic versus truly time-dependent paths | Route may not be globally optimal over trip time | State snapshot assumption; later evaluate timestep replanning separately |
| D* Lite implementation on directed multigraph | Incorrect predecessor updates or edge-key loss | Build known-answer unit tests and compare every update with fresh Dijkstra |
| Hierarchy preprocessing cost/stale weights | Poor dynamic performance or misleading speedup | Separate topology preprocessing from snapshot costs and report both timings |
| Synthetic traffic realism | Results may not generalize to observed Hanoi traffic | Prominent provenance labels; configurable assumptions; reserve claims for validated data |
| Benchmark timing noise | Weak comparisons | Fixed OD sets/seeds, warmups, repetitions, environment metadata, robust summaries |
| Full-city UI memory/rendering | Browser becomes unreadable or slow | Simplify overlays, cap exploration traces, toggle algorithms, spatially filter layers |

