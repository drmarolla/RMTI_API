"""RMTI REST API v1.   uvicorn api:app --port 8000   (interactive docs at /docs)

Scoring runs on the hash-locked RMTI engine (rmti_python/core). Auth: X-API-Key header.
Keys: RMTI_API_KEYS="key:tier:Name,key2:tier:Name". Request bodies are never logged or stored.
"""
from __future__ import annotations

import hmac
import os
import threading
import time
import uuid
from collections import defaultdict, deque
from typing import Any, Literal, Optional

from fastapi import Depends, FastAPI, Header, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

import content
from engine import DISCLAIMER, ENGINE_VERSION, core, elas, hcc

API_VERSION = "2.0.0"
SANDBOX_KEY = "rmti_sandbox_demo"
ACCESS_TIERS = {"sandbox": {"rpm": 20, "batch": 25, "description": "Public demo key. Shared, low limits."},
                "research": {"rpm": 120, "batch": 250, "description": "Academic and research use."},
                "enterprise": {"rpm": 600, "batch": 1000, "description": "Hospital systems and integrators."}}


def _load_keys():
    keys = {}
    if os.getenv("RMTI_DISABLE_SANDBOX") != "1":
        keys[SANDBOX_KEY] = {"tier": "sandbox", "name": "Public sandbox"}
    for e in filter(None, (x.strip() for x in os.getenv("RMTI_API_KEYS", "").split(","))):
        p = e.split(":", 2)
        if len(p) >= 2 and p[0] and p[1] in ACCESS_TIERS:
            keys[p[0]] = {"tier": p[1], "name": p[2] if len(p) == 3 else p[1]}
    return keys


KEYS = _load_keys()
_hits: dict[str, deque] = defaultdict(deque)
_lock = threading.Lock()


class ApiError(Exception):
    def __init__(self, status, code, detail, headers=None):
        self.status, self.code, self.detail, self.headers = status, code, detail, headers or {}


def _problem(request, status, code, title, detail, headers=None):
    return JSONResponse({"status": status, "code": code, "title": title, "detail": detail,
                         "request_id": getattr(request.state, "request_id", None)},
                        status_code=status, headers=headers or {}, media_type="application/problem+json")


def _consume(client, response):
    limit = ACCESS_TIERS[client["tier"]]["rpm"]
    now = time.monotonic()
    with _lock:
        q = _hits[client["key"]]
        while q and now - q[0] > 60:
            q.popleft()
        reset = int(60 - (now - q[0])) + 1 if q else 60
        if len(q) >= limit:
            raise ApiError(429, "rate_limited", f"Limit of {limit} requests/minute for tier '{client['tier']}' reached.",
                           {"Retry-After": str(reset), "X-RateLimit-Limit": str(limit), "X-RateLimit-Remaining": "0"})
        q.append(now)
        remaining = limit - len(q)
    response.headers.update({"X-RateLimit-Limit": str(limit), "X-RateLimit-Remaining": str(remaining), "X-RateLimit-Reset": str(reset)})


async def authenticate(request: Request, response: Response, x_api_key: Optional[str] = Header(default=None)):
    if not x_api_key:
        raise ApiError(401, "missing_api_key", "Send your key in the X-API-Key header.")
    found = None
    for k, meta in KEYS.items():
        if hmac.compare_digest(k.encode(), x_api_key.encode()):
            found = {"key": k, **meta}
    if not found:
        raise ApiError(401, "invalid_api_key", "That API key is not recognised.")
    _consume(found, response)
    return found


class ScoreRequest(BaseModel):
    L: float = Field(..., ge=0, le=1, description="Likelihood", examples=[0.7])
    E: float = Field(..., ge=0, le=1, description="Exposure", examples=[0.6])
    V: float = Field(..., ge=0, le=1, description="Vulnerability", examples=[0.8])
    rho_now: float = Field(..., ge=0, lt=1, description="Resilience today (below 1)", examples=[0.2])
    rho_after: Optional[float] = Field(None, ge=0, lt=1, description="Resilience after an investment or treatment")
    C: int = Field(5, ge=1, le=5, description="Consequence level 1-5")
    N: float = Field(100000, ge=1, description="Population or cohort size (for E_log and the equity rate)")
    domain: Literal["general", "hcc"] = Field("general", description="'hcc' uses oncology bounds and wording")
    label: Optional[str] = Field(None, max_length=64, description="Opaque reference. Never a name or patient identifier.")


class BatchItem(ScoreRequest):
    name: str = Field(..., max_length=64)


class BatchRequest(BaseModel):
    items: list[BatchItem] = Field(..., min_length=1, max_length=1000)


class SensRequest(BaseModel):
    L: float = Field(..., ge=0, le=1)
    E: float = Field(..., ge=0, le=1)
    V: float = Field(..., ge=0, le=1)
    rho: float = Field(..., ge=0, lt=1)
    pct: float = Field(10, gt=0, le=50, description="Perturbation in percent")


def _score(req: ScoreRequest) -> dict:
    fn = hcc.assess_patient if req.domain == "hcc" else core.assess
    kw = dict(N=req.N, L=req.L, V=req.V, rho_now=req.rho_now, rho_after=req.rho_after, C=req.C)
    res = fn(**kw, E=req.E) if req.domain == "hcc" else fn(**kw, E_sel=req.E)
    res["tier_now"] = core.tier(res["R_now"])
    if "R_after" in res:
        res["tier_after"] = core.tier(res["R_after"])
    res["elasticity"] = elas.elasticities(req.L, req.E, req.V, req.rho_now)
    res.update(label=req.label, domain=req.domain, engine_version=ENGINE_VERSION, disclaimer=DISCLAIMER)
    return res


app = FastAPI(title="RMTI API", version=API_VERSION, docs_url="/docs", redoc_url="/redoc",
              description=f"Deterministic Risk Mechanism Theory Index scoring: R = L·E·V·(1−ρ), five fixed tiers.\n\n**{DISCLAIMER}**")
if os.getenv("RMTI_CORS_ORIGINS"):
    app.add_middleware(CORSMiddleware, allow_origins=os.environ["RMTI_CORS_ORIGINS"].split(","), allow_methods=["GET", "POST"],
                       allow_headers=["X-API-Key", "Content-Type"], expose_headers=["X-Request-ID", "X-RateLimit-Remaining", "Retry-After"])


@app.middleware("http")
async def ctx(request: Request, call_next):
    request.state.request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:16]
    t0 = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    response.headers["X-Process-Time-ms"] = f"{(time.perf_counter() - t0) * 1000:.2f}"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.exception_handler(ApiError)
async def _e1(request, exc):
    return _problem(request, exc.status, exc.code, exc.code.replace("_", " ").capitalize(), exc.detail, exc.headers)


@app.exception_handler(RequestValidationError)
async def _e2(request, exc):
    f = exc.errors()[0] if exc.errors() else {}
    return _problem(request, 422, "validation_error", "Validation error",
                    f"{'.'.join(str(p) for p in f.get('loc', []) if p != 'body') or 'request'}: {f.get('msg', 'invalid input')}")


@app.exception_handler(Exception)
async def _e3(request, exc):
    return _problem(request, 500, "internal_error", "Internal error", "Something went wrong. Quote the request_id to support.")


@app.get("/health", tags=["System"])
def health():
    return {"status": "ok", "api_version": API_VERSION, "engine_version": ENGINE_VERSION}


@app.get("/v1/meta", tags=["System"])
def meta():
    return {"api_version": API_VERSION, "engine_version": ENGINE_VERSION, "formula": "R = L * E * V * (1 - rho)",
            "tiers": [{"tier": lbl, "below": (None if t > 1e8 else t), "posture": core.TIER_POSTURE[lbl]} for t, lbl in core.TIER],
            "consequence_scale": core.C_INFRA, "access_tiers": ACCESS_TIERS, "disclaimer": DISCLAIMER}


@app.get("/v1/usage", tags=["Account"])
def usage(client: dict = Depends(authenticate)):
    t = ACCESS_TIERS[client["tier"]]
    with _lock:
        used = len(_hits[client["key"]])
    return {"name": client["name"], "tier": client["tier"], "requests_per_minute": t["rpm"], "used_this_minute": used, "max_batch_size": t["batch"]}


@app.post("/v1/risk/score", tags=["Risk"], response_model=dict[str, Any])
def risk_score(req: ScoreRequest, client: dict = Depends(authenticate)):
    return _score(req)


@app.post("/v1/risk/score/fhir", tags=["Risk"], summary="Score and return a FHIR R4-shaped RiskAssessment")
def risk_fhir(req: ScoreRequest, client: dict = Depends(authenticate)):
    r = _score(req)
    hl7 = {1: "low", 2: "moderate", 3: "high", 4: "high", 5: "high"}[int(r["tier_now"].split()[1])]
    body = {"resourceType": "RiskAssessment", "status": "final",
            "method": {"text": f"RMTI engine v{ENGINE_VERSION}: R = L*E*V*(1-rho)"},
            "prediction": [{"outcome": {"text": r["tier_now"]},
                            "qualitativeRisk": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/risk-probability", "code": hl7}]},
                            "rationale": f"R={r['R_now']}; IR={r['IR']}; EAL={r['EAL_now']}"}],
            "note": [{"text": DISCLAIMER}]}
    if req.label:
        body["identifier"] = [{"value": req.label}]
    return JSONResponse(body, media_type="application/fhir+json")


@app.post("/v1/risk/batch", tags=["Risk"], summary="Rank many cases by tier, then EAL")
def risk_batch(req: BatchRequest, client: dict = Depends(authenticate)):
    cap = ACCESS_TIERS[client["tier"]]["batch"]
    if len(req.items) > cap:
        raise ApiError(413, "batch_too_large", f"Tier '{client['tier']}' allows {cap} items per batch; you sent {len(req.items)}.")
    rows = {}
    for it in req.items:
        kw = dict(N=it.N, L=it.L, E_sel=it.E, V=it.V, rho_now=it.rho_now, C=it.C)
        if it.rho_after is not None:
            kw["rho_after"] = it.rho_after
        rows[it.name] = kw
    if len(rows) != len(req.items):
        raise ApiError(422, "duplicate_names", "Each item needs a unique name.")
    ranked = core.rank_cohort(rows)
    counts = {lbl: 0 for _, lbl in core.TIER}
    for r in ranked:
        r["tier_now"] = core.tier(r["R_now"])
        counts[r["tier_now"]] += 1
    return {"count": len(ranked), "tier_counts": counts, "ranked": ranked, "engine_version": ENGINE_VERSION, "disclaimer": DISCLAIMER}


@app.post("/v1/risk/sensitivity", tags=["Risk"], summary="One-way ±pct sensitivity with tier-flip detection")
def risk_sens(req: SensRequest, client: dict = Depends(authenticate)):
    base = core.score(req.L, req.E, req.V, req.rho)
    out = []
    f = req.pct / 100
    for lever in ("L", "E", "V", "rho"):
        row = {"lever": lever}
        for tag, k in (("minus", 1 - f), ("plus", 1 + f)):
            vals = dict(L=req.L, E=req.E, V=req.V, rho=req.rho)
            vals[lever] = min(vals[lever] * k, 0.999 if lever == "rho" else 1.0)
            s = core.score(vals["L"], vals["E"], vals["V"], vals["rho"])
            row[tag] = {"R": s["R"], "tier": s["tier"], "flips_tier": s["tier"] != base["tier"]}
        out.append(row)
    return {"baseline": {"R": base["R"], "tier": base["tier"]}, "pct": req.pct, "elasticity": elas.elasticities(req.L, req.E, req.V, req.rho),
            "one_way": out, "engine_version": ENGINE_VERSION, "disclaimer": DISCLAIMER}


# ----------------------------------------------------------------------------- case studies
def _case(slug: str) -> dict:
    if slug in content.CASES:
        c = content.CASES[slug]
        vid = content.find_media(slug)
        return {"slug": slug, "type": "cancer-case-study", "title": c["title"], "published_study": c["study"], "finding": c["finding"],
                "stages": [{"stage": n, "description": t} for n, t in c["stages"]],
                "lever_mapping": [{"lever": a, "published_data": b} for a, b in c["mapping"]],
                "rmti": {"r_before": c["r_before"], "tier_before": core.tier(c["r_before"]), "r_after": c["r_after"], "tier_after": core.tier(c["r_after"]),
                         "note": f"Synthetic illustration, R falls {c['change']}. Not a prediction."},
                "references": [{"citation": a, "url": b, "type": k} for a, b, k in c["refs"]],
                "video": {"available": bool(vid), "file": vid and __import__("os").path.basename(vid), "captions": bool(vid and content.find_captions(vid))},
                "disclaimer": DISCLAIMER}
    if slug == "six-cities":
        ranked = core.rank_cohort({k: {x: v[x] for x in ("N", "L", "E_sel", "V", "rho_now", "C", *(["rho_after"] if "rho_after" in v else []))} for k, v in content.SIX_CITIES.items()})
        return {"slug": slug, "type": "infrastructure-case-study", "title": "Six Sub-Saharan African cities", "published_study": content.IJMADA[0],
                "ranked": ranked, "references": [{"citation": content.IJMADA[0], "url": content.IJMADA[1], "type": content.IJMADA[2]}], "disclaimer": DISCLAIMER}
    if slug == "hcc-surveillance-cohorts":
        ranked = hcc.rank_cohort_hcc(hcc._scoreable(hcc.PUBLISHED_COHORTS))
        return {"slug": slug, "type": "hcc-cohorts", "title": "Six published HCC surveillance cohorts", "ranked": ranked, "disclaimer": DISCLAIMER}
    raise ApiError(404, "case_not_found", f"No case study called '{slug}'. See GET /v1/cases.")


CASE_SLUGS = ["liver", "lung", "breast", "six-cities", "hcc-surveillance-cohorts"]


@app.get("/v1/cases", tags=["Case studies"], summary="List every case study")
def cases_list(client: dict = Depends(authenticate)):
    out = []
    for s in CASE_SLUGS:
        c = _case(s)
        out.append({"slug": s, "type": c["type"], "title": c["title"], "href": f"/v1/cases/{s}"})
    return {"count": len(out), "cases": out}


@app.get("/v1/cases/{slug}", tags=["Case studies"], summary="One case study with stages, mapping, trajectory and references")
def case_detail(slug: str, client: dict = Depends(authenticate)):
    return _case(slug)
