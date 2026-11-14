"""Typed access to environment variables.

A variable that is unset or empty falls back to its default. Without a default it is required and a missing value
raises immediately, so a misconfigured production process fails at start-up and not on the first request.
"""

import os


class MissingEnvironmentVariableError(RuntimeError):
    """A required environment variable is unset or empty."""


def _raw(name: str) -> str | None:
    value = os.environ.get(name, "").strip()
    return value or None


def get_str(name: str, default: str | None = None) -> str:
    value = _raw(name)
    if value is not None:
        return value
    if default is not None:
        return default
    raise MissingEnvironmentVariableError(f"Environment variable {name} is required")


def get_bool(name: str, default: bool | None = None) -> bool:
    value = _raw(name)
    if value is None:
        if default is None:
            raise MissingEnvironmentVariableError(f"Environment variable {name} is required")
        return default
    lowered = value.lower()
    if lowered in {"1", "true", "yes", "on"}:
        return True
    if lowered in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"Environment variable {name} must be a boolean, got {value!r}")


def get_int(name: str, default: int | None = None) -> int:
    value = _raw(name)
    if value is None:
        if default is None:
            raise MissingEnvironmentVariableError(f"Environment variable {name} is required")
        return default
    try:
        return int(value)
    except ValueError:
        raise ValueError(f"Environment variable {name} must be an integer, got {value!r}") from None


def get_list(name: str, default: list[str] | None = None) -> list[str]:
    """Comma-separated list; surrounding whitespace and empty items are dropped."""
    value = _raw(name)
    if value is None:
        if default is None:
            raise MissingEnvironmentVariableError(f"Environment variable {name} is required")
        return default
    return [item.strip() for item in value.split(",") if item.strip()]
