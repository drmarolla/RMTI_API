"""
liver_routes.py  --  FastAPI router: the RMTI time-indexed HCC trajectory as animation frames (4D liver).

Add to api.py, before the final portal.mount(...) line:
    import liver_routes
    app.include_router(liver_routes.router)

    GET  /v1/liver/presets         synthetic scenarios (L, E, C, rho0, y and delivery per cycle)
    POST /v1/liver/progression     engine trajectory plus interpolated frames; engine validation errors return 422
Inherits the app's X-API-Key dependency. Pure RMTI engine output; no patient data, no imaging. Geometry is drawn in the browser.
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import liver_progression as LP

router = APIRouter(prefix="/v1/liver", tags=["Liver progression (4D)"])


class ProgressionIn(BaseModel):
    L: float = Field(..., ge=0, le=1)
    E: float = Field(..., ge=0, le=1)
    C: int = Field(5, ge=1, le=5)
    rho0: float = Field(..., ge=0, le=0.95)
    observations: List[Optional[float]] = Field(..., min_length=1, description="allostatic-load composite y per cycle (0-6); null = missed visit")
    delivery: List[Optional[float]] = Field(..., description="surveillance adherence per cycle (0-1); null = carry forward")
    params: Optional[dict] = Field(None, description="override alpha, beta, look_ahead, lam, v_lo, v_hi, y_max, rho_ceiling")
    sub: int = Field(10, ge=1, le=30, description="interpolated frames per cycle")
    turns: float = Field(1.0, ge=0, le=4, description="full 360-degree rotations across the animation (azimuth_deg in each frame)")


@router.get("/presets")
def liver_presets():
    return {"presets": LP.PRESETS, "disclaimer": LP.DISCLAIMER}


@router.post("/progression")
def liver_progression(b: ProgressionIn):
    try:
        return LP.manifest(b.L, b.E, b.C, b.rho0, b.observations, b.delivery, b.params, b.sub, b.turns)
    except (ValueError, KeyError, TypeError) as e:
        raise HTTPException(422, str(e))
