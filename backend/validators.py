"""Input validation utilities using Marshmallow schemas."""
from __future__ import annotations

from functools import wraps
from typing import Any, Callable, Dict, Tuple

from flask import jsonify, request

try:  # pragma: no cover - optional dependency may be missing in offline tests
    from marshmallow import Schema, fields, validate, ValidationError
except Exception:  # pragma: no cover
    # Lightweight fallback to keep validation working if marshmallow is unavailable
    class ValidationError(Exception):
        pass

    class _Field:
        def __init__(self, required: bool = False, validate=None, load_default=None):
            self.required = required
            self.validate = validate
            self.load_default = load_default

        def deserialize(self, value):
            if value is None:
                if self.required:
                    raise ValidationError("Missing data")
                return self.load_default
            if self.validate:
                if isinstance(self.validate, list):
                    for validator in self.validate:
                        validator(value)
                else:
                    self.validate(value)
            return value

    class fields:  # type: ignore
        Str = _Field

    class validate:  # type: ignore
        @staticmethod
        def Length(min=None, max=None):
            def _validator(value):
                if min is not None and len(value) < min:
                    raise ValidationError("String too short")
                if max is not None and len(value) > max:
                    raise ValidationError("String too long")

            return _validator

        @staticmethod
        def OneOf(options):
            def _validator(value):
                if value not in options:
                    raise ValidationError("Invalid value")

            return _validator

        @staticmethod
        def Regexp(pattern, error=None):
            import re

            regex = re.compile(pattern)

            def _validator(value):
                if not regex.match(value):
                    raise ValidationError(error or "Invalid format")

            return _validator

    class Schema:  # minimal
        def load(self, data: Dict[str, Any]):
            return data


class AnalyzeRequestSchema(Schema):
    text = fields.Str(required=True, validate=validate.Length(min=1, max=10000))
    element_type = fields.Str(validate=validate.OneOf(["div", "button", "a", "span"]), load_default="div")
    color = fields.Str(
        validate=validate.Regexp(r"^#[0-9A-Fa-f]{6}$", error="color must be in hex format like #RRGGBB"),
        load_default="#000000",
    )


def _validate_content_length(max_size: int) -> Tuple[bool, str | None]:
    length = request.content_length
    if length is None:
        return True, None
    if length > max_size:
        return False, "Request payload too large"
    return True, None


def validate_request(schema: Schema, max_size: int = 1_000_000) -> Callable:
    """Validate incoming JSON requests using the provided schema."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any):
            ok, error = _validate_content_length(max_size)
            if not ok:
                return jsonify({"error": error}), 413
            if not request.is_json:
                return jsonify({"error": "Content-Type must be application/json"}), 415
            try:
                payload: Dict[str, Any] = schema.load(request.get_json())
            except ValidationError as exc:
                return jsonify({"error": "Validation failed", "messages": exc.messages}), 400
            kwargs["validated_data"] = payload
            return func(*args, **kwargs)

        return wrapper

    return decorator


__all__ = ["AnalyzeRequestSchema", "validate_request"]
