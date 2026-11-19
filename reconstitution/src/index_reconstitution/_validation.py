"""Deterministic serialization and input validation shared by the local adapters."""

from __future__ import annotations
from dataclasses import fields, is_dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
import hashlib
import json
import math
from typing import Any

def require_nonempty(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a nonempty string")


def ensure_aware(value: datetime, field_name: str = "timestamp") -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be a timezone-aware datetime")


def ensure_date(value: date, field_name: str) -> None:
    if not isinstance(value, date) or isinstance(value, datetime):
        raise ValueError(f"{field_name} must be a calendar date")


def ensure_tuple(value: tuple[Any, ...], field_name: str) -> None:
    if not isinstance(value, tuple):
        raise ValueError(f"{field_name} must be an immutable tuple")


def ensure_sha256(value: str, field_name: str = "content_sha256") -> None:
    if not isinstance(value, str) or len(value) != 64 or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise ValueError(f"{field_name} must be a lowercase SHA-256 hex digest")


def normalize_cik(value: str | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.isascii() or not value.isdigit():
        raise ValueError("cik must contain ASCII digits only")
    if not 1 <= len(value) <= 10:
        raise ValueError("cik must contain between one and ten digits")
    return value.zfill(10)


def ensure_methodology_match(version_id: str, cutoff_version_id: str) -> None:
    require_nonempty(version_id, "methodology_version_id")
    if version_id != cutoff_version_id:
        raise ValueError("methodology version must match the review cutoff")


def canonical_data(value: Any) -> Any:
    """Represent decision records deterministically, including nested evidence."""
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: canonical_data(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        ensure_aware(value)
        return value.astimezone(timezone.utc).isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("non-finite Decimal cannot be hashed")
        rendered = format(value, "f")
        return rendered.rstrip("0").rstrip(".") if "." in rendered else rendered
    if isinstance(value, (tuple, list)):
        return [canonical_data(item) for item in value]
    if isinstance(value, dict):
        return {str(key): canonical_data(item) for key, item in value.items()}
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("non-finite float cannot be hashed")
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    raise ValueError(f"unsupported canonical value: {type(value).__name__}")


def canonical_hash(value: Any) -> str:
    payload = json.dumps(canonical_data(value), sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
