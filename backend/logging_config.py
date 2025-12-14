"""Structured logging utilities."""
import json
import logging
import sys
import uuid
from datetime import datetime
from typing import Any, Dict

from flask import g, request


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        payload: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
        }
        if request:
            payload.update(
                {
                    "path": request.path,
                    "method": request.method,
                    "request_id": getattr(g, "request_id", None),
                }
            )
        return json.dumps(payload)


def configure_logging(level: str = "INFO", fmt: str = "json") -> None:
    root = logging.getLogger()
    root.setLevel(level.upper())
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level.upper())
    handler.setFormatter(JsonFormatter() if fmt == "json" else logging.Formatter("%(levelname)s: %(message)s"))
    root.handlers.clear()
    root.addHandler(handler)


def attach_request_id():
    g.request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

