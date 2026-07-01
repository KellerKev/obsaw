"""obsaw — observability for websaw_ng.

A DuckDB-backed request-metrics store + built-in viewer queries, a Recorder that
also emits OpenTelemetry (OTLP), and one-call ombott instrumentation.

    from obsaw import MetricsStore, Recorder, instrument_ombott
    rec = Recorder(MetricsStore("metrics.duckdb"))
    instrument_ombott(app, rec, app_name="site")     # times every request
    rec.store.per_app()                               # feed the admin dashboard

Add OTLP export with the ``otel`` extra:

    from obsaw import OtelEmitter
    rec = Recorder(store, otel=OtelEmitter(endpoint="http://collector:4318/v1/metrics"))
"""
from __future__ import annotations

from .instrument import instrument_ombott
from .recorder import Recorder
from .store import MetricsStore


def OtelEmitter(*args, **kwargs):
    """Lazily construct the OTel emitter (needs the ``otel`` extra)."""
    from .otel import OtelEmitter as _E
    return _E(*args, **kwargs)


__all__ = ["MetricsStore", "Recorder", "instrument_ombott", "OtelEmitter"]

__version__ = "0.1.0"
