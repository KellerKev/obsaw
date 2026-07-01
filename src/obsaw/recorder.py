"""The Recorder — one write path that fans out to the DuckDB store and, if
configured, an OpenTelemetry emitter. ``track`` is a context manager for timing a
block manually; the ombott instrumentation calls ``record`` directly.
"""
from __future__ import annotations

import time
from contextlib import contextmanager


class Recorder:
    def __init__(self, store, *, otel=None, app_default=""):
        self.store = store
        self.otel = otel
        self.app_default = app_default

    def record(self, *, app=None, method="GET", path="", route="", status=200,
               duration_ms=0.0, error=None):
        app = app or self.app_default
        self.store.record(app=app, method=method, path=path, route=route, status=status,
                          duration_ms=duration_ms, error=error)
        if self.otel is not None:
            try:
                self.otel.emit(app=app, route=route or path, status=status,
                               duration_ms=duration_ms, error=error)
            except Exception:
                pass                       # telemetry export must never break a request

    @contextmanager
    def track(self, app=None, method="GET", path="", route=""):
        t0 = time.perf_counter()
        status, error = 200, None
        try:
            yield
        except Exception as exc:
            status, error = 500, "%s: %s" % (type(exc).__name__, exc)
            raise
        finally:
            self.record(app=app, method=method, path=path, route=route, status=status,
                        duration_ms=(time.perf_counter() - t0) * 1000.0, error=error)


__all__ = ["Recorder"]
