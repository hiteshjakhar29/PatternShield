"""Rate limiting configuration using Flask-Limiter."""
from __future__ import annotations

import importlib.util
from flask import Flask

if importlib.util.find_spec("flask_limiter"):
    from flask_limiter import Limiter  # type: ignore
    from flask_limiter.util import get_remote_address  # type: ignore
else:
    class Limiter:  # type: ignore
        def __init__(self, *args, **kwargs):
            self._limit = lambda *a, **k: (lambda f: f)

        def limit(self, *args, **kwargs):
            return lambda f: f

    def get_remote_address():  # type: ignore
        return "anonymous"


def init_limiter(app: Flask, config, storage) -> Limiter:
    strategy = None
    if getattr(storage, "connection_pool", None):
        strategy = config.REDIS_URL
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=[config.API_RATE_LIMIT] if config.RATE_LIMIT_ENABLED else [],
        storage_uri=strategy or "memory://",
        headers_enabled=True,
    )
    return limiter

