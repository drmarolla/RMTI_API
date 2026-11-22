# Copyright 2025-2026 Cesar Marolla. Apache-2.0.
"""Runtime settings, read from the environment (nothing secret lives in the source tree)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, Mapping, Tuple

from .security import Client, load_clients


@dataclass
class Settings:
    auth: str = "required"                     # "required" (default, fail-closed) or "disabled" (local development only)
    max_rows: int = 10_000
    max_upload_bytes: int = 10_000_000
    max_json_bytes: int = 8_000_000
    cors_origins: Tuple[str, ...] = ()
    contact: str = ""                          # shown in the portal as "request access"
    clients: Dict[str, Client] = field(default_factory=dict)

    @classmethod
    def from_env(cls, env: Mapping[str, str] = os.environ) -> "Settings":
        auth = env.get("RMTI_AUTH", "required").strip().lower()
        if auth not in ("required", "disabled"):
            raise ValueError("RMTI_AUTH must be 'required' or 'disabled'")
        return cls(
            auth=auth,
            max_rows=int(env.get("RMTI_MAX_ROWS", 10_000)),
            max_upload_bytes=int(env.get("RMTI_MAX_UPLOAD_BYTES", 10_000_000)),
            max_json_bytes=int(env.get("RMTI_MAX_JSON_BYTES", 8_000_000)),
            cors_origins=tuple(o.strip() for o in env.get("RMTI_CORS_ORIGINS", "").split(",") if o.strip()),
            contact=env.get("RMTI_CONTACT", ""),
            clients=load_clients(env),
        )
