import pytest

from obsaw import MetricsStore, Recorder


class _FakeOtel:
    def __init__(self):
        self.calls = []

    def emit(self, **kw):
        self.calls.append(kw)


def test_record_fans_out_to_store_and_otel():
    store = MetricsStore()
    otel = _FakeOtel()
    rec = Recorder(store, otel=otel, app_default="site")
    rec.record(method="GET", route="/x", status=200, duration_ms=4.0)
    assert store.per_app()[0]["app"] == "site"
    assert otel.calls and otel.calls[0]["route"] == "/x"


def test_track_times_and_captures_errors():
    store = MetricsStore()
    rec = Recorder(store, app_default="site")
    with rec.track(method="GET", route="/ok"):
        pass
    with pytest.raises(ValueError):
        with rec.track(method="GET", route="/boom"):
            raise ValueError("nope")
    rows = {r["route"]: r for r in store.top_routes("site")}
    assert rows["/ok"]["errors"] == 0
    assert rows["/boom"]["errors"] == 1
    assert store.recent("site", limit=1)  # something recorded
    store.close()


def test_otel_failure_never_breaks_record():
    class _Boom:
        def emit(self, **kw):
            raise RuntimeError("exporter down")
    store = MetricsStore()
    rec = Recorder(store, otel=_Boom(), app_default="s")
    rec.record(route="/x", status=200, duration_ms=1.0)   # must not raise
    assert store.summary("s")["requests"] == 1
    store.close()
