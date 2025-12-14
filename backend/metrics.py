"""Prometheus metrics integration."""

from __future__ import annotations

import importlib.util
import time
from functools import wraps

from flask import Blueprint, Response, request

if importlib.util.find_spec("prometheus_client"):
    from prometheus_client import CollectorRegistry, Counter, Histogram, generate_latest  # type: ignore

    registry = CollectorRegistry()
    REQUEST_COUNT = Counter(
        "patternshield_requests_total",
        "API request count",
        ["endpoint", "method", "status"],
        registry=registry,
    )
    REQUEST_LATENCY = Histogram(
        "patternshield_request_duration_seconds",
        "Request duration",
        ["endpoint"],
        registry=registry,
    )

    def metrics_view() -> Response:
        return Response(generate_latest(registry), mimetype="text/plain")

else:
    registry = None

    class _Counter:
        def labels(self, **kwargs):
            return self

        def inc(self):
            return None

    class _Histogram(_Counter):
        def observe(self, value):
            return None

    REQUEST_COUNT = _Counter()
    REQUEST_LATENCY = _Histogram()

    def metrics_view() -> Response:  # type: ignore[override]
        return Response("metrics disabled", mimetype="text/plain")


metrics_bp = Blueprint("metrics", __name__)
metrics_bp.add_url_rule("/metrics", view_func=metrics_view)


def init_metrics(app):
    app.register_blueprint(metrics_bp)


def track_request(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        response = func(*args, **kwargs)
        duration = time.time() - start
        endpoint = request.endpoint or "unknown"
        status = getattr(response, "status_code", None)
        if status is None and isinstance(response, tuple) and len(response) > 1:
            status = response[1]
        status = status or 200
        REQUEST_COUNT.labels(
            endpoint=endpoint, method=request.method, status=status
        ).inc()
        REQUEST_LATENCY.labels(endpoint=endpoint).observe(duration)
        return response

    return wrapper
