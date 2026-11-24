"""RMTI API v1 additions: POST /v1/assess (?format=json|fhir) and POST /v1/trajectory.

Mounted by api.py, so it shares the same X-API-Key auth, rate limits and error format:

    from api_v1 import build_router
    app.include_router(build_router(authenticate, ApiError))

Scoring is done by the hash-locked core (rmti_python/core, via engine.py) and the time-indexed layer
(rmti_python/dynamic/rmti_trajectory.py). Nothing here re-implements a formula.
Request bodies are never logged or stored. Research prototype, not a medical device.
"""
from __future__ import annotations

from typing import Annotated, Any, Literal, Optional, Union

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from engine import DISCLAIMER, ENGINE_VERSION, core, elas, hcc
from dynamic.rmti_trajectory import DEFAULTS, run_trajectory

Unit = Annotated[float, Field(ge=0, le=1)]
Rho = Annotated[float, Field(ge=0, lt=1)]
Drive = Annotated[float, Field(ge=0)]
HL7_RISK = {1: "low", 2: "moderate", 3: "high", 4: "high", 5: "high"}   # same mapping as /v1/risk/score/fhir


class AssessRequest(BaseModel):
    L: float = Field(..., ge=0, le=1, description="Likelihood", examples=[0.30])
    E: float = Field(..., ge=0, le=1, description="Exposure", examples=[0.60])
    V: float = Field(..., ge=0, le=1, description="Vulnerability", examples=[0.50])
    rho_now: float = Field(..., ge=0, lt=1, description="Resilience today (below 1)", examples=[0.20])
    rho_after: Optional[float] = Field(None, ge=0, lt=1, description="Resilience after an intervention")
    C: int = Field(5, ge=1, le=5, description="Consequence index 1-5")
    N: float = Field(100000, ge=1, description="Cohort size (E_log and the equity rate)")
    domain: Literal["general", "hcc"] = Field("hcc", description="'hcc' uses oncology bounds and wording")
    label: Optional[str] = Field(None, max_length=64, description="Opaque reference. Never a name or patient identifier.")


class TrajectoryRequest(BaseModel):
    y: list[Drive] = Field(..., min_length=2, max_length=120, description="Observed vulnerability drive per cycle (0..y_max)", examples=[[4, 4.4, 5.1, 5.9, 6.8]])
    rho: list[Rho] = Field(..., min_length=2, max_length=120, description="Resilience per cycle, each in [0, 1)", examples=[[.5, .5, .45, .4, .35]])
    L: Union[Unit, list[Unit]] = Field(..., description="Likelihood: one value, or one per cycle", examples=[0.25])
    E: float = Field(..., ge=0, le=1, examples=[0.60])
    C: int = Field(5, ge=1, le=5)
    alpha: float = Field(DEFAULTS["alpha"], gt=0, le=1, description="Alpha-beta filter gain, level")
    beta: float = Field(DEFAULTS["beta"], ge=0, le=2, description="Alpha-beta filter gain, slope")
    look_ahead: float = Field(DEFAULTS["look_ahead"], ge=0, le=5)
    v_lo: float = Field(DEFAULTS["v_lo"], ge=0, le=1)
    v_hi: float = Field(DEFAULTS["v_hi"], ge=0, le=1)
    y_max: float = Field(DEFAULTS["y_max"], gt=0)
    use_filter: bool = Field(True, description="False uses the observed y directly")
    cycle_months: int = Field(6, ge=1, le=60)
    label: Optional[str] = Field(None, max_length=64, description="Opaque reference. Never a patient identifier.")


def _assess(req: AssessRequest) -> dict:
    kw = dict(N=req.N, L=req.L, V=req.V, rho_now=req.rho_now, rho_after=req.rho_after, C=req.C)
    res = hcc.assess_patient(**kw, E=req.E) if req.domain == "hcc" else core.assess(**kw, E_sel=req.E)
    res["tier_now"] = core.tier(res["R_now"])                      # full label, e.g. "Tier 3 - High"
    if "R_after" in res:
        res["tier_after"] = core.tier(res["R_after"])
    res["elasticity"] = elas.elasticities(req.L, req.E, req.V, req.rho_now) if min(req.L, req.E, req.V) > 0 else None
    res.update(label=req.label, domain=req.domain, engine_version=ENGINE_VERSION, disclaimer=DISCLAIMER)
    return res


def _fhir(r: dict) -> dict:
    code = HL7_RISK[int(r["tier_now"].split()[1])]
    body = {"resourceType": "RiskAssessment", "status": "final",
            "method": {"text": f"RMTI engine v{ENGINE_VERSION}: R = L*E*V*(1-rho)"},
            "prediction": [{"outcome": {"text": r["tier_now"]},
                            "qualitativeRisk": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/risk-probability", "code": code}]},
                            "rationale": f"R={r['R_now']}; IR={r['IR']}; EAL={r['EAL_now']}"}],   # R is an index, not a probability
            "note": [{"text": DISCLAIMER}]}
    if "R_after" in r:
        body["prediction"].append({"outcome": {"text": r["tier_after"]},
                                   "rationale": f"After intervention: R={r['R_after']}; reduction {r['risk_reduction_pct']}%"})
    if r.get("label"):
        body["identifier"] = [{"value": r["label"]}]
    return body


def build_router(authenticate, ApiError) -> APIRouter:
    router = APIRouter(prefix="/v1")

    @router.post("/assess", tags=["Risk"], summary="Assess one patient or cohort; add ?format=fhir for a FHIR R4 RiskAssessment")
    def assess(req: AssessRequest, format: Literal["json", "fhir"] = Query("json"), client: dict = Depends(authenticate)):
        try:
            r = _assess(req)
        except ValueError as e:
            raise ApiError(422, "validation_error", str(e))
        if format == "fhir":
            return JSONResponse(_fhir(r), media_type="application/fhir+json")
        return r

    @router.post("/trajectory", tags=["Risk"], response_model=dict[str, Any],
                 summary="Time-indexed R(t) = L(t)·E·V*(t)·[1−ρ(t)] across surveillance cycles")
    def trajectory(req: TrajectoryRequest, client: dict = Depends(authenticate)):
        if len(req.rho) != len(req.y):
            raise ApiError(422, "validation_error", f"rho has {len(req.rho)} values but y has {len(req.y)}; send one per cycle.")
        if isinstance(req.L, list) and len(req.L) != len(req.y):
            raise ApiError(422, "validation_error", f"L has {len(req.L)} values but y has {len(req.y)}; send one value or one per cycle.")
        try:
            rows = run_trajectory(req.y, req.rho, req.L, req.E, C=req.C, alpha=req.alpha, beta=req.beta,
                                  look_ahead=req.look_ahead, v_lo=req.v_lo, v_hi=req.v_hi, y_max=req.y_max,
                                  use_filter=req.use_filter, cycle_months=req.cycle_months)
        except ValueError as e:
            raise ApiError(422, "validation_error", str(e))
        first, last = rows[0], rows[-1]
        out = {"cycles": len(rows), "rows": rows,
               "summary": {"R_first": first["R"], "R_last": last["R"], "tier_first": first["tier"], "tier_last": last["tier"],
                           "pct_change_R": round(100 * (last["R_raw"] / first["R_raw"] - 1), 1) if first["R_raw"] > 0 else None},
               "filter": {"on": req.use_filter, "alpha": req.alpha, "beta": req.beta, "look_ahead": req.look_ahead},
               "label": req.label, "engine_version": ENGINE_VERSION, "disclaimer": DISCLAIMER}
        if not isinstance(req.L, list) and min(req.L, req.E) > 0 and all(0 < r["V"] and r["rho"] < 1 for r in rows):
            out["decomposition"] = elas.trajectory_decomposition(rows, req.L, req.E)    # dln R by term, cycle to cycle
        return out

    return router
