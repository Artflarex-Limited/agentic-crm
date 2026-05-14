"""
Security utilities for input validation and hardening.
"""
import re
from typing import Any


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """Sanitize user input strings."""
    if not isinstance(value, str):
        return value
    # Remove null bytes
    value = value.replace("\x00", "")
    # Trim to max length
    value = value[:max_length]
    return value.strip()


def sanitize_email(email: str) -> str:
    """Sanitize email input."""
    email = sanitize_string(email, 255)
    # Basic email pattern
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if re.match(pattern, email):
        return email.lower()
    return ""


def sanitize_json_input(data: dict[str, Any]) -> dict[str, Any]:
    """Recursively sanitize dictionary input."""
    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            sanitized[key] = sanitize_string(value)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_json_input(value)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_string(v) if isinstance(v, str) else v
                for v in value
            ]
        else:
            sanitized[key] = value
    return sanitized


def validate_webhook_secret(provided: str, expected: str) -> bool:
    """Constant-time webhook secret comparison to prevent timing attacks."""
    import hmac
    if not provided or not expected:
        return False
    return hmac.compare_digest(provided, expected)