# Copyright 2025-2026 Cesar Marolla. Apache-2.0.
"""REST API.   Run:  uvicorn rmti.api:app --host 0.0.0.0 --port 8000     Docs at /docs.

Requires:  pip install "rmti-py[api]". Stateless; no data is stored. Research prototype.
"""
from __future__ import annotations

from typing import Dict, List, Literal, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from . import __version__
from .core import assess, boundary_margins, score
from .optimizer import Project, optimize_portfolio
from .stochastic import UncertainParam, simulate_rmti

app = FastAPI(title="RMTI API", version=__version__,
              description="Risk Mechanism Theory Index: scoring, uncertainty, portfolio optimisation, HCC triage. "
                          "Research prototype - not validated against outcomes; not a medical device.")
U01 = Field(..., ge=0.0, le=1.0)


class ScoreIn(BaseModel):
    L: float = U01
    E_sel: float = U01
    V: float = U01
    rho: float = U01
    rho_after: Optional[float] = Field(None, ge=0.0, le=1.0)
    C: int = Field(5, ge=1, le=5)
    N: Optional[int] = Field(None, gt=0)


@app.get("/health")
def health():
    return {"status": "ok", "version": __version__}


@app.post("/score")
def score_ep(b: ScoreIn):
    out = score(b.L, b.E_sel, b.V, b.rho, b.C)
    out.pop("EAL_raw", None)
    out.pop("R_raw", None)
    out["margins"] = boundary_margins(b.L, b.E_sel, b.V, b.rho)
    if b.rho_after is not None:
        a = score(b.L, b.E_sel, b.V, b.rho_after, b.C)
        out.update(R_after=a["R"], tier_after=a["tier"], EAL_after=a["EAL"])
    if b.N:
        out["assessment"] = assess(b.N, b.L, b.E_sel, b.V, b.rho, b.rho_after, b.C)
    return out


class ParamIn(BaseModel):
    mean: float = U01
    woe: str = "w_ic"
    sd: Optional[float] = Field(None, ge=0.0)


class SimIn(BaseModel):
    L: ParamIn
    E: ParamIn
    V: ParamIn
    rho: ParamIn
    rho_after: Optional[ParamIn] = None
    n_sims: int = Field(20_000, ge=100, le=200_000)
    seed: int = 42
    correlation: Optional[List[List[float]]] = None


@app.post("/simulate")
def simulate_ep(b: SimIn):
    try:
        mk = lambda p: UncertainParam(p.mean, p.woe, p.sd)
        r = simulate_rmti(mk(b.L), mk(b.E), mk(b.V), mk(b.rho), mk(b.rho_after) if b.rho_after else None,
                          b.n_sims, b.seed, b.correlation)
    except (ValueError, KeyError) as e:
        raise HTTPException(422, str(e))
    return {**r.summary(), "note": "Tier probabilities depend on the assumed evidence-grade -> concentration mapping."}


class ProjectIn(BaseModel):
    name: str
    cost: float = Field(..., ge=0)
    R_now: float = U01
    R_after: float = U01
    group: Optional[str] = None
    N: Optional[float] = Field(None, gt=0)
    EAL_now: Optional[float] = None
    EAL_after: Optional[float] = None


class OptIn(BaseModel):
    projects: List[ProjectIn] = Field(..., min_length=1, max_length=500)
    budget: float = Field(..., ge=0)
    objective: Literal["delta_R", "delta_EAL", "delta_equity"] = "delta_R"
    mandatory: List[str] = []
    max_projects: Optional[int] = Field(None, ge=1)


@app.post("/optimize")
def optimize_ep(b: OptIn):
    try:
        r = optimize_portfolio([Project(**p.model_dump()) for p in b.projects], b.budget, b.objective,
                               b.mandatory, b.max_projects)
    except ValueError as e:
        raise HTTPException(422, str(e))
    return {"selected": r.selected, "total_cost": r.total_cost, "unspent": r.unspent,
            "objective_value": r.objective_value, "total_delta_R": r.total_delta_R, "greedy_value": r.greedy_value}


class PatientIn(BaseModel):
    id: Optional[str] = None
    L: float = U01
    E: float = U01
    albi_grade: Optional[Literal[1, 2, 3]] = None
    albumin: Optional[float] = Field(None, gt=0)
    bilirubin: Optional[float] = Field(None, gt=0)
    surveillance: Literal["none", "usual", "outreach", "specialist", "optimised"]
    bclc_if_missed: Literal["0", "A", "early-int", "B", "C-D"]
    improved_surveillance: Optional[Literal["none", "usual", "outreach", "specialist", "optimised"]] = None


class HccIn(BaseModel):
    patients: List[PatientIn] = Field(..., min_length=1, max_length=10_000)
    albumin_unit: Literal["g/L", "g/dL"] = "g/L"
    bilirubin_unit: Literal["umol/L", "mg/dL"] = "umol/L"


@app.post("/hcc/score")
def hcc_score_ep(b: HccIn):
    import pandas as pd
    from .domains import hcc
    df = pd.DataFrame([p.model_dump(exclude_none=True) for p in b.patients])
    try:
        out = hcc.score_table(df, b.albumin_unit, b.bilirubin_unit)
    except ValueError as e:
        raise HTTPException(422, str(e))
    return {"disclaimer": "Research prototype; not for individual patient care decisions.",
            "patients": out.astype(object).where(out.notna(), None).to_dict(orient="records")}


class AlbiIn(BaseModel):
    albumin: float = Field(..., gt=0)
    bilirubin: float = Field(..., gt=0)
    albumin_unit: Literal["g/L", "g/dL"] = "g/L"
    bilirubin_unit: Literal["umol/L", "mg/dL"] = "umol/L"


@app.post("/hcc/albi")
def albi_ep(b: AlbiIn):
    from .domains import hcc
    s = hcc.albi_score(b.albumin, b.bilirubin, b.albumin_unit, b.bilirubin_unit)
    g = hcc.albi_grade(s)
    return {"albi_score": s, "albi_grade": g, "V": hcc.albi_grade_to_V(g)}
