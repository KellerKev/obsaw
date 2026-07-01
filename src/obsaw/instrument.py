"""Instrument an ombott app via its ``before_request`` / ``after_request`` hooks.

``after_request`` fires in a ``finally`` (even on errors), so every request is
timed. Redirects/aborts travel as ``HTTPResponse`` exceptions — those keep their
real status; a genuine ``Exception`` is recorded as a 500 with its message.
"""
from __future__ import annotations

import sys
import time


def instrument_ombott(app, recorder, *, app_name=""):
    import ombott_ng
    from ombott_ng import HTTPResponse

    def _before():
        try:
            ombott_ng.request.environ["obsaw.t0"] = time.perf_counter()
        except Exception:
            pass

    def _after():
        try:
            env = ombott_ng.request.environ
            t0 = env.get("obsaw.t0")
            if t0 is None:
                return
            dur = (time.perf_counter() - t0) * 1000.0
            status = getattr(ombott_ng.response, "_status_code", None) or 200
            error = None
            exc = sys.exc_info()[1]
            if isinstance(exc, HTTPResponse):                 # redirect / abort
                status = getattr(exc, "_status_code", None) or getattr(exc, "status_code", None) or status
            elif exc is not None:                             # a real error -> 500
                status = 500
                error = "%s: %s" % (type(exc).__name__, exc)
            route = getattr(env.get("ombott.route"), "rule", "") or env.get("PATH_INFO", "")
            recorder.record(app=app_name, method=env.get("REQUEST_METHOD", "GET"),
                            path=env.get("PATH_INFO", ""), route=route, status=status,
                            duration_ms=dur, error=error)
        except Exception:
            pass                          # instrumentation must never break a request

    app.add_hook("before_request", _before)
    app.add_hook("after_request", _after)
    return app


__all__ = ["instrument_ombott"]
