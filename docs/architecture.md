# Final architecture

The system uses a layered research architecture so every routing algorithm receives the
same immutable graph snapshot and objective definition.

1. **Acquisition** — OSMnx downloads a directed `MultiDiGraph`; GraphML provides a local,
   deterministic cache. Parallel edges and one-way topology are retained.
2. **Traffic** — a `TrafficProvider` creates a timestamped, immutable traffic snapshot.
   Synthetic, historical, and real adapters share one contract and explicitly identify
   provenance.
3. **Prediction** — feature builders and fitted regressors map that snapshot to predicted
   edge travel times. AI estimates weights; AI does not select paths.
4. **Cost model** — one configured objective converts edge attributes into non-negative
   scalar costs for all algorithms in a benchmark run.
5. **Routing** — algorithms implement one `RoutingAlgorithm` contract and return a common
   `RouteResult`, including instrumentation and optional exploration traces.
6. **Simulation** — a timestep engine owns vehicle state, applies traffic changes, and
   invokes repeated search or D* Lite under identical events.
7. **Experiments/UI** — reproducible runners persist tidy result tables; Streamlit/Folium
   reads the same services used by scripts and tests.

## Correctness boundaries

- Exact baselines assume finite, non-negative scalar edge costs.
- Time-dependent routing initially uses snapshot weights, not a claim of FIFO-optimal
  continuous-time routing.
- A* heuristics must be objective-specific lower bounds. A zero heuristic is the safe
  fallback for a cost function without a proven geographic lower bound.
- Backward directed searches traverse incoming edges and preserve the original edge key.
- Bidirectional A* is deferred until a valid potential transformation and stopping rule are
  proved for the chosen objective. It will not be included merely for feature count.
- Hierarchical routing is approximate unless its corridor contains the exact optimum; its
  gap is always measured against Dijkstra on the same snapshot.
- Motorbike access is best-effort from OSM tags. Missing restrictions are reported as
  unknown rather than replaced with invented rules.

## Planned dependency groups

- GIS/graph: OSMnx, NetworkX (and OSMnx's GeoPandas/Shapely dependencies).
- ML/data: NumPy, pandas, scikit-learn, joblib; XGBoost is an optional extra.
- UI/plots: Streamlit, Folium, streamlit-folium, Plotly, Matplotlib.
- Quality: pytest, pytest-cov, Ruff, mypy.

