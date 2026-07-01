import pytest

pytest.importorskip("opentelemetry")

from opentelemetry.sdk.metrics.export import InMemoryMetricReader   # noqa: E402

from obsaw.otel import OtelEmitter                                  # noqa: E402


def test_otel_emits_counter_and_histogram():
    reader = InMemoryMetricReader()
    em = OtelEmitter(service_name="test", metric_reader=reader)
    em.emit(app="site", route="/x", status=200, duration_ms=12.5)
    em.emit(app="site", route="/x", status=500, duration_ms=3.0, error="boom")

    data = reader.get_metrics_data()
    names = {m.name for rm in data.resource_metrics for sm in rm.scope_metrics for m in sm.metrics}
    assert "http.server.request.count" in names
    assert "http.server.duration" in names
    em.shutdown()
