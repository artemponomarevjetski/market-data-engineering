"""Hash-bound local inputs and deterministic JSON serialization.

Bindings describe retained files. They do not prove who originally published a
file or when it first became available, and no function accesses the network.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
from typing import Any, TypedDict

from ._validation import canonical_data, ensure_sha256

MAX_SOURCE_BYTES = 25_000_000


class FileBinding(TypedDict):
    path: str
    sha256: str
    bytes: int


def digest(raw: bytes) -> str:
    """Return the lowercase SHA-256 digest of the exact retained bytes."""
    return hashlib.sha256(raw).hexdigest()


def json_bytes(value: Any) -> bytes:
    """Serialize supported records deterministically, including dataclasses."""
    return (json.dumps(canonical_data(value), ensure_ascii=False, sort_keys=True,
                       indent=2, allow_nan=False) + "\n").encode("utf-8")


def _read_local(path: str | Path) -> tuple[Path, bytes]:
    requested = Path(path).absolute()
    if requested.is_symlink() or requested.resolve() != requested:
        raise ValueError("input must be an original path without symlinks")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    descriptor = os.open(requested, flags)
    with os.fdopen(descriptor, "rb") as handle:
        info = os.fstat(handle.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_SOURCE_BYTES:
            raise ValueError("input must be a regular file within the byte bound")
        raw = handle.read(MAX_SOURCE_BYTES + 1)
    if len(raw) > MAX_SOURCE_BYTES:
        raise ValueError("input exceeds the byte bound")
    return requested, raw


def bind(path: str | Path) -> FileBinding:
    """Freeze a local path, digest, and byte count for subsequent verification."""
    resolved, raw = _read_local(path)
    return {"path": str(resolved), "sha256": digest(raw), "bytes": len(raw)}


def read_bound(binding: FileBinding) -> bytes:
    """Reject a file whose contents no longer match its retained binding."""
    if not isinstance(binding, dict) or set(binding) != {"path", "sha256", "bytes"}:
        raise ValueError("binding requires path, sha256, and bytes")
    if not isinstance(binding["path"], str) or not binding["path"].strip():
        raise ValueError("binding path must be nonempty text")
    ensure_sha256(binding["sha256"])
    if type(binding["bytes"]) is not int or not 0 <= binding["bytes"] <= MAX_SOURCE_BYTES:
        raise ValueError("binding byte count is invalid")
    _, raw = _read_local(binding["path"])
    if digest(raw) != binding["sha256"] or len(raw) != binding["bytes"]:
        raise ValueError("input no longer matches its frozen manifest")
    return raw
