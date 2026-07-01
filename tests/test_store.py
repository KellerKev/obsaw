from obsaw import MetricsStore


def _seed(s):
    for i in range(10):
        s.record(app="site", method="GET", path="/p/%d" % i, route="/p/<id>",
                 status=200, duration_ms=10.0 + i)
    s.record(app="site", method="GET", path="/boom", route="/boom", status=500,
             duration_ms=99.0, error="ValueError: x")
    s.record(app="api", method="POST", path="/t", route="/t", status=201, duration_ms=5.0)


def test_per_app_and_summary():
    s = MetricsStore()
    _seed(s)
    per = {r["app"]: r for r in s.per_app()}
    assert per["site"]["requests"] == 11 and per["site"]["errors"] == 1
    assert per["site"]["error_pct"] == round(100.0 / 11, 1)
    assert per["api"]["requests"] == 1 and per["api"]["errors"] == 0

    summ = s.summary("site")
    assert summ["requests"] == 11 and summ["errors"] == 1
    assert summ["p95_ms"] >= summ["p50_ms"] and summ["p99_ms"] >= summ["p95_ms"]
    assert set(s.apps()) == {"api", "site"}
    s.close()


def test_top_routes_and_status_and_recent():
    s = MetricsStore()
    _seed(s)
    routes = {r["route"]: r for r in s.top_routes("site")}
    assert routes["/p/<id>"]["requests"] == 10          # grouped by route pattern
    assert routes["/boom"]["errors"] == 1

    statuses = {r["status"]: r["n"] for r in s.status_breakdown("site")}
    assert statuses[200] == 10 and statuses[500] == 1

    recent = s.recent("site", limit=3)
    assert len(recent) == 3 and all("duration_ms" in r for r in recent)
    s.close()
