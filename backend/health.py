"""Health check endpoints."""
from __future__ import annotations

from flask import jsonify

from backend import database


def liveness_response():
    return jsonify({"status": "ok"})


def readiness_response(db_engine, cache_client, transformer_ready: bool):
    db_ok = database.health_check(db_engine)
    try:
        cache_ok = bool(cache_client and cache_client.ping())
    except Exception:
        cache_ok = False
    return (
        jsonify({"database": db_ok, "cache": cache_ok, "transformer": transformer_ready}),
        200 if db_ok and cache_ok else 503,
    )

