"""Redis caching helpers."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from typing import Any, Dict, Tuple

from flask import jsonify


class _InMemoryCache:
    def __init__(self):
        self.store: dict[str, Any] = {}

    def get(self, key: str):
        return self.store.get(key)

    def setex(self, key: str, ttl: int, value: str):
        self.store[key] = value

    def ping(self) -> bool:  # pragma: no cover - trivial
        return True


def get_client(url: str):
    if importlib.util.find_spec("redis"):
        import redis  # type: ignore

        return redis.Redis.from_url(url, decode_responses=True)
    return _InMemoryCache()


def _hash_payload(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True).encode()
    return hashlib.sha256(raw).hexdigest()


def build_cache_key(endpoint: str, payload: Dict[str, Any]) -> str:
    return f"prediction:{endpoint}:{_hash_payload(payload)}"


def get_cached_response(client, cache_key: str) -> Tuple[bool, Any]:
    if not client:
        return False, None
    cached = client.get(cache_key)
    if cached:
        return True, json.loads(cached)
    return False, None


def set_cached_response(client, cache_key: str, data: Dict[str, Any], ttl: int) -> None:
    if not client:
        return
    client.setex(cache_key, ttl, json.dumps(data))


def cached_json_response(data: Dict[str, Any], status: int = 200):
    return jsonify(data), status
