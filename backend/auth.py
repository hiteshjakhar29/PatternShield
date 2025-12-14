"""Authentication utilities for API keys and JWT tokens."""

from __future__ import annotations

import logging
from functools import wraps
from typing import Callable, Optional

import base64
import hashlib
import hmac
import json
from flask import Response, jsonify, request

from backend.config import get_config

logger = logging.getLogger(__name__)
CONFIG = get_config()


def _unauthorized(message: str) -> Response:
    logger.warning("Auth failed: %s", message)
    return jsonify({"error": message}), 401


def require_api_key(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs):
        key = request.headers.get(CONFIG.API_KEY_HEADER)
        if not CONFIG.ALLOWED_API_KEYS:
            return _unauthorized("API keys not configured")
        if key not in CONFIG.ALLOWED_API_KEYS:
            return _unauthorized("Invalid API key")
        return func(*args, **kwargs)

    return wrapper


def _decode_jwt(token: str, secret: str) -> Optional[dict]:
    try:
        header_b64, payload_b64, signature = token.split(".")
        signing_input = f"{header_b64}.{payload_b64}".encode()
        expected = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
        actual = base64.urlsafe_b64decode(signature + "==")
        if not hmac.compare_digest(expected, actual):
            return None
        payload_json = base64.urlsafe_b64decode(payload_b64 + "==").decode()
        return json.loads(payload_json)
    except Exception:
        return None


def require_jwt(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return _unauthorized("Missing Bearer token")
        token = auth_header.split(" ", 1)[1]
        payload = _decode_jwt(token, CONFIG.JWT_SECRET)
        if not payload:
            return _unauthorized("Invalid token")
        request.user = payload  # type: ignore[attr-defined]
        return func(*args, **kwargs)

    return wrapper


def get_request_identity() -> Optional[str]:
    identity = getattr(request, "user", None)
    if isinstance(identity, dict):
        return identity.get("sub")
    return None
