"""RMTI REST API v1.   Run:  uvicorn api:app --port 8000   (docs at /docs)

Auth      : X-API-Key header. Keys come from RMTI_API_KEYS="key:tier:Name,key2:tier:Name".
            A shared sandbox key is always on unless RMTI_DISABLE_SANDBOX=1.
Privacy   : request bodies are never logged or stored. Do not send patient identifiers.
Errors    : every error is JSON {status, code, title, detail, request_id}.
"""
from __future__ import annotations

import hmac
import os
import threading
import time
import uuid
from collections import defaultdict, deque
from typing import Literal, Optional

from fastapi import Depends, FastAPI, Header, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

import rmti_core as core

# ----------------------------------------------------------------------------- keys & limits
Site = Literal["general", "liver", "lung", "breast"]


def _load_keys() -> dict[str, dict]:
    keys: dict[str, dict] = {}
    if os.getenv("RMTI_DISABLE_SANDBOX") != "1":
        keys[core.SANDBOX_KEY] = {"tier": "sandbox", "name": "Public sandbox"}
    for entry in filter(None, (e.strip() for e in os.getenv("RMTI_API_KEYS", "").split(","))):
        parts = entry.split(":", 2)
        if len(parts) >= 2 and parts[1] in core.ACCESS_TIERS and parts[0]:
            keys[parts[0]] = {"tier": parts[1], "name": parts[2] if len(parts) == 3 else parts[1]}
    return keys


KEYS = _load_keys()
_hits: dict[str, deque] = defaultdict(deque)
_lock = threading.Lock()
WINDOW = 60.0


class ApiError(Exception):
    def __init__(self, status: int, code: str, detail: str, headers: dict | None = None):
        self.status, self.code, self.detail, self.headers = status, code, detail, headers or {}


def _problem(request: Request, status: int, code: str, title: str, detail: str, headers=None):
    body = {"status": status, "code": code, "title": title, "detail": detail,
            "request_id": getattr(request.state, "request_id", None)}
    return JSONResponse(body, status_code=status, headers=headers or {},
                        media_type="application/problem+json")


def _find_key(presented: str) -> Optional[dict]:
    found = None
    for k, meta in KEYS.items():  # constant-time compare against every key
        if hmac.compare_digest(k.encode(), presented.encode()):
            found = {"key": k, **meta}
    return found


def _consume(client: dict, response: Response) -> None:
    limit = core.ACCESS_TIERS[client["tier"]]["rpm"]
    now = time.monotonic()
    with _lock:
        q = _hits[client["key"]]
        while q and now - q[0] > WINDOW:
            q.popleft()
        reset = int(WINDOW - (now - q[0])) + 1 if q else int(WINDOW)
        if len(q) >= limit:
            raise ApiError(429, "rate_limited",
                           f"Limit of {limit} requests/minute for tier '{client['tier']}' reached.",
                           {"Retry-After": str(reset), "X-RateLimit-Limit": str(limit),
                            "X-RateLimit-Remaining": "0", "X-RateLimit-Reset": str(reset)})
        q.append(now)
        remaining = limit - len(q)
    response.headers.update({"X-RateLimit-Limit": str(limit),
                             "X-RateLimit-Remaining": str(remaining),
                             "X-RateLimit-Reset": str(reset)})


async def authenticate(request: Request, response: Response,
                       x_api_key: Optional[str] = Header(default=None, description="Your API key")) -> dict:
    if not x_api_key:
        raise ApiError(401, "missing_api_key", "Send your key in the X-API-Key header.")
    client = _find_key(x_api_key)
    if not client:
        raise ApiError(401, "invalid_api_key", "That API key is not recognised.")
    _consume(client, response)
    request.state.client = client
    return client


# ----------------------------------------------------------------------------- models
class Levers(BaseModel):
    L: float = Field(..., ge=0, le=1, description="Likelihood, 0 to 1", examples=[0.7])
    E: float = Field(..., ge=0, le=1, description="Exposure, 0 to 1", examples=[0.6])
    V: float = Field(..., ge=0, le=1, description="Vulnerability, 0 to 1", examples=[0.8])
    rho: float = Field(..., ge=0, le=1, description="Resilience, 0 to 1", examples=[0.35])


class ScoreRequest(Levers):
    site: Site = Field("general", description="Clinical context label")
    label: Optional[str] = Field(None, max_length=64,
                                 description="Opaque caller reference. Never a name or patient identifier.")


class WhatIf(BaseModel):
    lever: str
    name: str
    from_: float = Field(..., alias="from")
    to: float
    new_risk: float
    absolute_reduction: float
    relative_reduction: float
    model_config = {"populate_by_name": True}


class ScoreResponse(BaseModel):
    risk: float
    tier: Literal["low", "moderate", "high", "critical"]
    inputs: Levers
    elasticity: dict[str, Optional[float]]
    what_if: list[WhatIf]
    priority_lever: Optional[str]
    site: Site
    label: Optional[str] = None
    engine_version: str
    disclaimer: str


class BatchRequest(BaseModel):
    items: list[ScoreRequest] = Field(..., min_length=1, max_length=1000)


class BatchItem(ScoreResponse):
    index: int


class BatchResponse(BaseModel):
    count: int
    tier_counts: dict[str, int]
    results: list[BatchItem]
    engine_version: str
    disclaimer: str


class SweepRequest(Levers):
    lever: Literal["L", "E", "V", "rho"] = Field(..., description="Lever to vary from 0 to 1")
    steps: int = Field(21, ge=2, le=101)


class SweepResponse(BaseModel):
    lever: str
    base: Levers
    points: list[dict]
    engine_version: str
    disclaimer: str


def _full(req: ScoreRequest) -> dict:
    res = core.score(req.L, req.E, req.V, req.rho)
    res.update(site=req.site, label=req.label)
    return res


# ----------------------------------------------------------------------------- app
DESCRIPTION = f"""
Deterministic Risk Mechanism Theory Index scoring: **`{core.FORMULA}`**.

* Every lever is a number from 0 to 1.
* Responses include a tier, per-lever elasticity and ranked what-if reductions.
* `/v1/risk/score/fhir` returns a FHIR R4-shaped `RiskAssessment` for EHR pipelines.

**{core.DISCLAIMER}**
"""
tags = [{"name": "Risk", "description": "Scoring endpoints (API key required)"},
        {"name": "Account", "description": "Key and limit information"},
        {"name": "System", "description": "Health and metadata (public)"}]

app = FastAPI(title="RMTI API", version=core.API_VERSION, description=DESCRIPTION,
              openapi_tags=tags, docs_url="/docs", redoc_url="/redoc")

if os.getenv("RMTI_CORS_ORIGINS"):
    app.add_middleware(CORSMiddleware, allow_origins=os.environ["RMTI_CORS_ORIGINS"].split(","),
                       allow_methods=["GET", "POST"], allow_headers=["X-API-Key", "Content-Type"],
                       expose_headers=["X-Request-ID", "X-RateLimit-Remaining", "Retry-After"])


@app.middleware("http")
async def request_context(request: Request, call_next):
    request.state.request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:16]
    t0 = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    response.headers["X-Process-Time-ms"] = f"{(time.perf_counter() - t0) * 1000:.2f}"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.exception_handler(ApiError)
async def _api_error(request: Request, exc: ApiError):
    return _problem(request, exc.status, exc.code, exc.code.replace("_", " ").capitalize(),
                    exc.detail, exc.headers)


@app.exception_handler(RequestValidationError)
async def _validation(request: Request, exc: RequestValidationError):
    first = exc.errors()[0] if exc.errors() else {}
    where = ".".join(str(p) for p in first.get("loc", []) if p != "body")
    return _problem(request, 422, "validation_error", "Validation error",
                    f"{where or 'request'}: {first.get('msg', 'invalid input')}")


@app.exception_handler(Exception)
async def _unhandled(request: Request, exc: Exception):
    return _problem(request, 500, "internal_error", "Internal error",
                    "Something went wrong. Quote the request_id when contacting support.")


# ----------------------------------------------------------------------------- routes
@app.get("/health", tags=["System"])
def health():
    return {"status": "ok", "api_version": core.API_VERSION, "engine_version": core.ENGINE_VERSION}


@app.get("/v1/meta", tags=["System"])
def meta():
    return {"api_version": core.API_VERSION, "engine_version": core.ENGINE_VERSION,
            "formula": core.FORMULA, "levers": core.LEVER_NAMES, "sites": list(core.SITES),
            "tier_bands": [{"tier": n, "below": c} for c, n in core.TIER_CUTS] +
                          [{"tier": "critical", "below": None}],
            "access_tiers": core.ACCESS_TIERS, "disclaimer": core.DISCLAIMER}


@app.get("/v1/usage", tags=["Account"])
def usage(client: dict = Depends(authenticate)):
    t = core.ACCESS_TIERS[client["tier"]]
    with _lock:
        used = len(_hits[client["key"]])
    return {"name": client["name"], "tier": client["tier"], "requests_per_minute": t["rpm"],
            "used_this_minute": used, "max_batch_size": t["batch"]}


@app.post("/v1/risk/score", response_model=ScoreResponse, response_model_by_alias=True, tags=["Risk"])
def risk_score(req: ScoreRequest, client: dict = Depends(authenticate)):
    return _full(req)


@app.post("/v1/risk/score/fhir", tags=["Risk"], summary="Score and return a FHIR RiskAssessment")
def risk_score_fhir(req: ScoreRequest, client: dict = Depends(authenticate)):
    res = _full(req)
    return JSONResponse(core.to_fhir_risk_assessment(res, req.site, req.label),
                        media_type="application/fhir+json")


@app.post("/v1/risk/batch", response_model=BatchResponse, response_model_by_alias=True, tags=["Risk"])
def risk_batch(req: BatchRequest, client: dict = Depends(authenticate)):
    cap = core.ACCESS_TIERS[client["tier"]]["batch"]
    if len(req.items) > cap:
        raise ApiError(413, "batch_too_large",
                       f"Tier '{client['tier']}' allows {cap} items per batch; you sent {len(req.items)}.")
    results, counts = [], {"low": 0, "moderate": 0, "high": 0, "critical": 0}
    for i, item in enumerate(req.items):
        r = _full(item)
        counts[r["tier"]] += 1
        results.append({"index": i, **r})
    return {"count": len(results), "tier_counts": counts, "results": results,
            "engine_version": core.ENGINE_VERSION, "disclaimer": core.DISCLAIMER}


@app.post("/v1/risk/sensitivity", response_model=SweepResponse, tags=["Risk"],
          summary="Sweep one lever from 0 to 1 and return the risk curve")
def risk_sensitivity(req: SweepRequest, client: dict = Depends(authenticate)):
    base = {"L": req.L, "E": req.E, "V": req.V, "rho": req.rho}
    return {"lever": req.lever, "base": base, "points": core.sweep(req.lever, base, req.steps),
            "engine_version": core.ENGINE_VERSION, "disclaimer": core.DISCLAIMER}
