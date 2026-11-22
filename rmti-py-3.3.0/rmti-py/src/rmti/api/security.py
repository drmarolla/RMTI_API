# Copyright 2025-2026 Cesar Marolla. Apache-2.0.
"""API-key handling. Keys are long random secrets shown ONCE at creation; only their SHA-256 digests are stored
(in the RMTI_API_CLIENTS environment variable or file), so a leaked config does not leak usable keys.
There are no built-in or default keys. With no clients configured the API refuses protected requests (fail-closed)."""
from __future__ import annotations

import hashlib
import json
import re
import secrets
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Dict, Iterable, Mapping, Optional, Tuple

SCOPES = ("score", "batch", "fhir")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class Client:
    name: str
    org: str
    scopes: frozenset
    rate_per_min: int = 60


ANONYMOUS = Client("anonymous-dev", "local development (auth disabled)", frozenset(SCOPES), 10_000)


def generate_key() -> str:
    return "rmti_" + secrets.token_urlsafe(32)


def hash_key(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def client_entry(name: str, org: str, scopes: Iterable[str], rate_per_min: int, key: str) -> dict:
    scopes = sorted(set(scopes))
    bad = set(scopes) - set(SCOPES)
    if bad:
        raise ValueError(f"unknown scopes {sorted(bad)}; allowed {SCOPES}")
    return {"name": name, "org": org, "sha256": hash_key(key), "scopes": scopes, "rate_per_min": int(rate_per_min)}


def parse_clients(entries: Iterable[Mapping]) -> Dict[str, Client]:
    out: Dict[str, Client] = {}
    for e in entries:
        h = str(e.get("sha256", "")).lower()
        if not _HEX64.match(h):
            raise ValueError(f"client {e.get('name')!r}: sha256 must be 64 hex characters (store the digest, never the key)")
        scopes = frozenset(e.get("scopes", ()))
        if not scopes or scopes - set(SCOPES):
            raise ValueError(f"client {e.get('name')!r}: scopes must be a non-empty subset of {SCOPES}")
        rate = int(e.get("rate_per_min", 60))
        if rate < 1:
            raise ValueError("rate_per_min must be >= 1")
        if h in out:
            raise ValueError("duplicate key digest")
        out[h] = Client(str(e["name"]), str(e.get("org", e["name"])), scopes, rate)
    return out


def load_clients(env: Mapping[str, str]) -> Dict[str, Client]:
    raw = env.get("RMTI_API_CLIENTS")
    path = env.get("RMTI_API_CLIENTS_FILE")
    if path:
        with open(path, encoding="utf-8") as f:
            raw = f.read()
    return parse_clients(json.loads(raw)) if raw else {}


class RateLimiter:
    """Per-client sliding 60-second window, in-process. With several workers/instances each keeps its own
    window: enforce a global limit at your gateway for production."""

    def __init__(self):
        self._hits: Dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, name: str, limit: int, now: Optional[float] = None) -> Tuple[bool, int, int]:
        """Returns (allowed, remaining, retry_after_seconds)."""
        now = time.monotonic() if now is None else now
        with self._lock:
            q = self._hits[name]
            while q and now - q[0] >= 60.0:
                q.popleft()
            if len(q) >= limit:
                return False, 0, max(1, int(60 - (now - q[0])) + 1)
            q.append(now)
            return True, limit - len(q), 0
