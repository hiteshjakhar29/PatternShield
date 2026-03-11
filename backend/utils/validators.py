"""
PatternShield — Request Validation Utilities

Centralised validation helpers so route handlers stay clean.
Each function returns (value, error_message). If error_message is not None,
the caller should return a 400 response with that message.
"""
from typing import Any, List, Optional, Tuple


def validate_text(
    text: Any,
    max_length: int = 2000,
    field_name: str = "text",
) -> Tuple[Optional[str], Optional[str]]:
    """
    Validate a text field.
    Returns (cleaned_text, None) on success or (None, error_msg) on failure.
    """
    if text is None:
        return None, f"Missing required field: {field_name}"
    if not isinstance(text, str):
        text = str(text)
    text = text.strip()
    if not text:
        return None, f"'{field_name}' must not be empty"
    if len(text) > max_length:
        return None, f"'{field_name}' too long (max {max_length} chars)"
    return text, None


def validate_elements_list(
    elements: Any,
    max_batch: int = 100,
) -> Tuple[Optional[List], Optional[str]]:
    """
    Validate the elements list for /batch/analyze.
    Returns (elements, None) on success or (None, error_msg) on failure.
    """
    if not isinstance(elements, list):
        return None, "'elements' must be an array"
    if len(elements) == 0:
        return None, "'elements' must not be empty"
    if len(elements) > max_batch:
        return None, f"Batch limited to {max_batch} elements"
    return elements, None


def validate_domain(domain: Any) -> Tuple[Optional[str], Optional[str]]:
    """Validate and normalise a domain string."""
    if not domain:
        return None, "Missing 'domain'"
    domain = str(domain).strip().lower()
    # Strip scheme/path if accidentally included
    for prefix in ("https://", "http://"):
        if domain.startswith(prefix):
            domain = domain[len(prefix):]
    domain = domain.split("/")[0]  # drop path
    if not domain:
        return None, "Invalid domain"
    return domain, None


def validate_boolean(value: Any, field_name: str = "field") -> Tuple[bool, Optional[str]]:
    """Coerce common truthy values to bool."""
    if isinstance(value, bool):
        return value, None
    if isinstance(value, str):
        if value.lower() in ("true", "1", "yes"):
            return True, None
        if value.lower() in ("false", "0", "no"):
            return False, None
        return False, f"'{field_name}' must be a boolean"
    return bool(value), None
