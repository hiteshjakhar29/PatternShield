"""
Shared authentication decorator for PatternShield API blueprints.
"""
from functools import wraps

from flask import jsonify, request


def require_api_key(f):
    """Skip auth when API_KEY_REQUIRED is False; otherwise validate X-API-Key header."""
    @wraps(f)
    def decorated(*args, **kwargs):
        from config import Config
        if not Config.API_KEY_REQUIRED:
            return f(*args, **kwargs)
        key = request.headers.get("X-API-Key")
        if not key or key != Config.API_KEY:
            return jsonify({"error": "Invalid or missing API key"}), 401
        return f(*args, **kwargs)
    return decorated
