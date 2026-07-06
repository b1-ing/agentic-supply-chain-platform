# services/cache.py
"""
A small time-based file cache for service responses.

Each entry is keyed by an arbitrary string and stored as
``<base_dir>/<sha1(key)>.json`` containing:

    {"fetched_at": <unix_ts>, "data": <payload>}

``bytes`` values are stored as base64 strings so the cache is pure JSON.
Stale entries are dropped transparently on read. The cache has no
concurrency guards — fine for a single-process dev tool. Multi-process
callers should add file locking.
"""

import base64
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Optional


def _json_default(value: Any) -> Any:
    if isinstance(value, bytes):
        return {"__bytes__": base64.b64encode(value).decode("ascii")}
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _json_object_hook(obj: dict) -> Any:
    if "__bytes__" in obj and len(obj) == 1:
        return base64.b64decode(obj["__bytes__"])
    return obj


class TTLCache:
    def __init__(self, base_dir: str, ttl_seconds: int):
        self.base_dir = Path(base_dir)
        self.ttl_seconds = ttl_seconds
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        digest = hashlib.sha1(key.encode("utf-8")).hexdigest()
        return self.base_dir / f"{digest}.json"

    def get(self, key: str) -> Optional[Any]:
        path = self._path(key)
        if not path.exists():
            return None

        try:
            with path.open("r", encoding="utf-8") as f:
                payload = json.load(f, object_hook=_json_object_hook)
        except (json.JSONDecodeError, OSError):
            # Corrupt or unreadable — treat as miss and drop the file.
            try:
                path.unlink()
            except OSError:
                pass
            return None

        fetched_at = payload.get("fetched_at", 0)
        if (time.time() - fetched_at) >= self.ttl_seconds:
            try:
                path.unlink()
            except OSError:
                pass
            return None

        return payload.get("data")

    def set(self, key: str, value: Any) -> None:
        path = self._path(key)
        tmp = path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(
                {"fetched_at": time.time(), "data": value},
                f,
                default=_json_default,
            )
        os.replace(tmp, path)

