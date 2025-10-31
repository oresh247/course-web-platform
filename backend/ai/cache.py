import time
import hashlib
from typing import Any, Optional, Tuple

_store: dict[str, Tuple[float, Any]] = {}


def _now() -> float:
    return time.time()


def make_cache_key(*parts: str) -> str:
    hasher = hashlib.sha256()
    for part in parts:
        hasher.update(part.encode("utf-8", errors="ignore"))
        hasher.update(b"|")
    return hasher.hexdigest()


def get(key: str) -> Optional[Any]:
    entry = _store.get(key)
    if not entry:
        return None
    expires_at, value = entry
    if _now() > expires_at:
        try:
            del _store[key]
        except Exception:
            pass
        return None
    return value


def set(key: str, value: Any, ttl_seconds: int) -> None:
    _store[key] = (_now() + ttl_seconds, value)


