import io

from obsaw import MetricsStore, Recorder, instrument_ombott


def _call(app, path, method="GET"):
    env = {"REQUEST_METHOD": method, "PATH_INFO": path, "SERVER_NAME": "t", "SERVER_PORT": "80",
           "wsgi.input": io.BytesIO(b""), "wsgi.errors": io.StringIO(), "wsgi.url_scheme": "http"}
    box = {}

    def start(status, headers, exc_info=None):
        box["status"] = status
    b"".join(app.wsgi(env, start))
    return box.get("status", "")


def test_instrument_records_ok_error_and_redirect():
    import ombott_ng
    app = ombott_ng.Ombott()
    store = MetricsStore()
    instrument_ombott(app, Recorder(store), app_name="site")

    @app.get("/ok")
    def _ok():
        return "ok"

    @app.get("/boom")
    def _boom():
        raise ValueError("kaboom")

    @app.get("/go")
    def _go():
        ombott_ng.redirect("/ok")

    _call(app, "/ok")
    _call(app, "/boom")
    _call(app, "/go")

    rows = store.recent("site")
    by_route = {r["route"]: r for r in rows}
    assert by_route["/ok"]["status"] == 200
    assert by_route["/boom"]["status"] == 500 and by_route["/boom"]["error"]
    assert 300 <= by_route["/go"]["status"] < 400          # redirect keeps its status
    assert all(r["duration_ms"] >= 0 for r in rows)
    store.close()
