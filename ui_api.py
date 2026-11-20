# Copyright 2026 Cesar Marolla. Licensed under the Apache License, Version 2.0.
"""Pure helpers for the Developer Portal "Try it out" sandbox: request payload, cURL / Python / JavaScript snippets,
validation that mirrors the API's Pydantic model (HTTP 422), and a response from the same engine the API runs.

No Streamlit import here, so it can be tested on its own."""
from __future__ import annotations

import json
import os

PLACEHOLDER_BASE = "https://YOUR-API-HOST"
KEY_HEADER = "X-API-Key"
ENDPOINT = "/v1/snapshot"
DOMAINS = {"Cancer: liver (HCC)": ("oncoclastics", "hcc"), "Cancer: lung": ("oncoclastics", "lung"),
           "Cancer: breast": ("oncoclastics", "breast"), "Disaster science": ("disaster_science", None)}


def base_url() -> str:
    return (os.environ.get("RMTI_API_URL") or PLACEHOLDER_BASE).rstrip("/")


def build_payload(domain: str, site, N, L, E, V, rho_now, rho_after=None, C=5) -> dict:
    p = {"domain": domain}
    if site:
        p["site"] = site
    p.update({"N": N, "L": L, "E": E, "V": V, "rho_now": rho_now})
    if rho_after is not None:
        p["rho_after"] = rho_after
    p["C"] = C
    return p


def curl_snippet(payload: dict, base: str | None = None) -> str:
    b = (base or base_url()) + ENDPOINT
    return (f"curl -X POST \"{b}\" \\\n  -H \"{KEY_HEADER}: YOUR_API_KEY\" \\\n  -H \"Content-Type: application/json\" \\\n"
            f"  -d '{json.dumps(payload)}'")


def python_snippet(payload: dict, base: str | None = None) -> str:
    b = (base or base_url()) + ENDPOINT
    body = json.dumps(payload, indent=4)
    return (f"import requests\n\nurl = \"{b}\"\nheaders = {{\"{KEY_HEADER}\": \"YOUR_API_KEY\"}}\npayload = {body}\n\n"
            "response = requests.post(url, json=payload, headers=headers, timeout=30)\n"
            "response.raise_for_status()      # 401 bad key, 422 invalid input\nprint(response.json())")


def js_snippet(payload: dict, base: str | None = None) -> str:
    b = (base or base_url()) + ENDPOINT
    body = json.dumps(payload, indent=2)
    return (f"const response = await fetch(\"{b}\", {{\n  method: \"POST\",\n  headers: {{ \"{KEY_HEADER}\": \"YOUR_API_KEY\", \"Content-Type\": \"application/json\" }},\n"
            f"  body: JSON.stringify({body}),\n}});\nif (!response.ok) throw new Error(await response.text());\nconsole.log(await response.json());")


# ------------------------------------------------------------------ validation (same rules as api.SnapshotIn)
_FIELDS = {  # name: (low, high, high_inclusive, required)
    "L": (0.0, 1.0, True, True), "E": (0.0, 1.0, True, True), "V": (0.0, 1.0, True, True),
    "rho_now": (0.0, 1.0, False, True), "rho_after": (0.0, 1.0, False, False)}
_KNOWN = {"domain", "site", "N", "L", "E", "V", "rho_now", "rho_after", "C"}
_DOMAINS = {"oncoclastics", "disaster_science", "hcc", "lung", "breast", "disaster"}


def validate(payload: dict) -> list:
    """Return a FastAPI-style 'detail' list (empty when valid)."""
    errs = []

    def err(field, msg, typ, ctx=None):
        e = {"type": typ, "loc": ["body", field], "msg": msg, "input": payload.get(field)}
        if ctx:
            e["ctx"] = ctx
        errs.append(e)

    for k in payload:
        if k not in _KNOWN:
            errs.append({"type": "extra_forbidden", "loc": ["body", k], "msg": "Extra inputs are not permitted", "input": payload[k]})
    if payload.get("domain", "hcc") not in _DOMAINS:
        err("domain", "Input should be one of: " + ", ".join(sorted(_DOMAINS)), "literal_error")
    for name, (lo, hi, hi_in, req) in _FIELDS.items():
        v = payload.get(name)
        if v is None:
            if req:
                err(name, "Field required", "missing")
            continue
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            err(name, "Input should be a valid number", "float_parsing")
        elif v < lo:
            err(name, f"Input should be greater than or equal to {lo:g}", "greater_than_equal", {"ge": lo})
        elif (v > hi) if hi_in else (v >= hi):
            err(name, f"Input should be {'less than or equal to' if hi_in else 'less than'} {hi:g}", "less_than_equal" if hi_in else "less_than",
                {"le" if hi_in else "lt": hi})
    n = payload.get("N", 100000)
    if isinstance(n, bool) or not isinstance(n, (int, float)) or n <= 0:
        err("N", "Input should be greater than 0", "greater_than", {"gt": 0})
    c = payload.get("C", 5)
    if isinstance(c, bool) or not isinstance(c, int) or not 1 <= c <= 5:
        err("C", "Input should be an integer from 1 to 5", "int_range")
    return errs


def run_snapshot(payload: dict):
    """(http_status, body). Validates like the API, then calls the same engine function the endpoint calls."""
    errs = validate(payload)
    if errs:
        return 422, {"detail": errs}
    import service as S
    try:
        out = S.snapshot(S.resolve_domain(payload.get("domain", "hcc"), payload.get("site")), payload.get("N", 100000), payload["L"], payload["E"],
                         payload["V"], payload["rho_now"], payload.get("rho_after"), payload.get("C", 5))
    except (ValueError, KeyError) as e:
        return 400, {"detail": str(e)}
    return 200, json.loads(json.dumps(out, default=str))


def pretty(obj) -> str:
    return json.dumps(obj, indent=2, default=str)
