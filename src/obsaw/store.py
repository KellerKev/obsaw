"""A DuckDB-backed request-metrics store — the built-in viewer's backend.

Every instrumented request becomes one row; DuckDB's analytic SQL then gives the
admin per-app throughput, latency percentiles, error rates, hot routes and a
recent-request tail without any external time-series database.
"""
from __future__ import annotations

import datetime

_SCHEMA = """CREATE TABLE IF NOT EXISTS request (
    ts TIMESTAMP, app VARCHAR, method VARCHAR, path VARCHAR, route VARCHAR,
    status INTEGER, duration_ms DOUBLE, error VARCHAR)"""


def _now():
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)


class MetricsStore:
    def __init__(self, path=":memory:"):
        import duckdb
        self.con = duckdb.connect(path)
        self.con.execute(_SCHEMA)

    def record(self, *, app, method="GET", path="", route="", status=200,
               duration_ms=0.0, error=None, ts=None):
        self.con.execute(
            "INSERT INTO request VALUES (?,?,?,?,?,?,?,?)",
            [ts or _now(), app or "", method, path, route or path, int(status),
             float(duration_ms), error])

    # --- queries (each returns a list of dicts / a dict) -------------------
    def _rows(self, sql, params=None):
        cur = self.con.execute(sql, params or [])
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]

    def _where(self, app):
        return ("WHERE app = ?", [app]) if app else ("", [])

    def apps(self):
        return [r["app"] for r in self._rows("SELECT DISTINCT app FROM request ORDER BY app")]

    def per_app(self):
        return self._rows(
            """SELECT app,
                 count(*) AS requests,
                 round(avg(duration_ms), 1) AS avg_ms,
                 round(quantile_cont(duration_ms, 0.95), 1) AS p95_ms,
                 sum(CASE WHEN status >= 400 THEN 1 ELSE 0 END) AS errors,
                 round(100.0 * sum(CASE WHEN status >= 400 THEN 1 ELSE 0 END) / count(*), 1) AS error_pct
               FROM request GROUP BY app ORDER BY requests DESC""")

    def summary(self, app=None):
        where, params = self._where(app)
        rows = self._rows(
            """SELECT count(*) AS requests,
                 round(avg(duration_ms), 1) AS avg_ms,
                 round(quantile_cont(duration_ms, 0.50), 1) AS p50_ms,
                 round(quantile_cont(duration_ms, 0.95), 1) AS p95_ms,
                 round(quantile_cont(duration_ms, 0.99), 1) AS p99_ms,
                 sum(CASE WHEN status >= 400 THEN 1 ELSE 0 END) AS errors
               FROM request %s""" % where, params)
        return rows[0] if rows else {}

    def top_routes(self, app=None, limit=10):
        where, params = self._where(app)
        return self._rows(
            """SELECT route,
                 count(*) AS requests,
                 round(avg(duration_ms), 1) AS avg_ms,
                 round(quantile_cont(duration_ms, 0.95), 1) AS p95_ms,
                 sum(CASE WHEN status >= 400 THEN 1 ELSE 0 END) AS errors
               FROM request %s GROUP BY route ORDER BY requests DESC LIMIT ?""" % where,
            params + [limit])

    def status_breakdown(self, app=None):
        where, params = self._where(app)
        return self._rows(
            "SELECT status, count(*) AS n FROM request %s GROUP BY status ORDER BY status" % where,
            params)

    def recent(self, app=None, limit=50):
        where, params = self._where(app)
        return self._rows(
            """SELECT ts, app, method, route, status, round(duration_ms, 1) AS duration_ms, error
               FROM request %s ORDER BY ts DESC LIMIT ?""" % where, params + [limit])

    def close(self):
        self.con.close()


__all__ = ["MetricsStore"]
