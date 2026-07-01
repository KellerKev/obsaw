"""OpenTelemetry metrics export (OTLP) — the vendor-neutral half of Phase 4.

Records a request counter + a duration histogram (labelled by app / route /
status) through the OTel SDK, exported over OTLP to any collector
(Grafana/Jaeger/Tempo/…). Needs the ``otel`` extra. Pass ``metric_reader`` to
capture metrics in-process (tests); otherwise it exports OTLP/HTTP.
"""
from __future__ import annotations


class OtelEmitter:
    def __init__(self, *, service_name="websaw_ng", endpoint=None, metric_reader=None):
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.resources import Resource

        reader = metric_reader
        if reader is None:
            from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
            from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
            exporter = OTLPMetricExporter(endpoint=endpoint) if endpoint else OTLPMetricExporter()
            reader = PeriodicExportingMetricReader(exporter)

        self._provider = MeterProvider(
            metric_readers=[reader], resource=Resource.create({"service.name": service_name}))
        meter = self._provider.get_meter("obsaw")
        self.requests = meter.create_counter("http.server.request.count")
        self.duration = meter.create_histogram("http.server.duration", unit="ms")

    def emit(self, *, app, route, status, duration_ms, error=None):
        attrs = {"app": app or "", "http.route": route or "", "http.status_code": int(status)}
        self.requests.add(1, attrs)
        self.duration.record(float(duration_ms), attrs)

    def shutdown(self):
        try:
            self._provider.shutdown()
        except Exception:
            pass


__all__ = ["OtelEmitter"]
