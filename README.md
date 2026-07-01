```
       .-"""""""""-.
     .'   o b s a w   '.       the Watcher
    (   (  (  o  )  )   )      every request seen, every error kept
     '.             .'         (DuckDB metrics + OTLP)
       '-.........-'
```

# obsaw

Observability for websaw_ng: a **DuckDB-backed request-metrics store + built-in
viewer**, a `Recorder` that also emits **OpenTelemetry (OTLP)**, and one-call
ombott instrumentation. The built-in viewer works with no external stack; OTLP
export is opt-in for those who have a collector.

```python
from obsaw import MetricsStore, Recorder, instrument_ombott

rec = Recorder(MetricsStore("metrics.duckdb"))
instrument_ombott(app, rec, app_name="site")     # times every request via hooks

rec.store.per_app()        # [{app, requests, avg_ms, p95_ms, errors, error_pct}, ...]
rec.store.summary("site")  # {requests, avg_ms, p50_ms, p95_ms, p99_ms, errors}
rec.store.top_routes("site")
rec.store.recent("site")
```

Add vendor-neutral export with the `otel` extra:

```python
from obsaw import OtelEmitter
rec = Recorder(store, otel=OtelEmitter(endpoint="http://collector:4318/v1/metrics"))
```

## Pieces

- **`MetricsStore`** (DuckDB) — one row per request; analytic SQL gives per-app
  throughput, latency percentiles, error rates, hot routes and a recent tail.
- **`Recorder`** — one write path → the store (+ optional OTel); `track()` context
  manager for timing a block.
- **`instrument_ombott`** — `before_request`/`after_request` hooks time every
  request; redirects keep their status, real exceptions record as 500s.
- **`OtelEmitter`** (extra `otel`) — a request counter + duration histogram
  exported over OTLP to any collector.

guardsaw's dashboard renders the store at `/admin/metrics` (per-app cards,
percentiles, hot routes, recent requests) — unified with its audit log and error
tickets.

---

*Part of the **[websaw-ng](https://github.com/KellerKev/websaw-ng)** platform &middot; forging your dreams &middot; install: `pixi add obsaw` from the `websaw-ng` conda channel.*
