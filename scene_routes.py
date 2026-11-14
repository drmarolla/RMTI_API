"""
scene_routes.py  --  FastAPI router for time-indexed scene manifests (the live 4D cube).

Add to api.py, before the final portal.mount(...) line:
    import scene_routes
    app.include_router(scene_routes.router)

Routes (they inherit the app's X-API-Key dependency, so RMTI_API_KEYS protects them like the other /v1 routes):
    GET  /v1/scene/cases           published and illustrative cases that can be loaded
    GET  /v1/scene/{key}           manifest for one case, e.g. /v1/scene/lagos
    POST /v1/scene                 manifest for your own L, E, V, rho_now, rho_after
Research prototype. Pure arithmetic on R = L * E * V * (1 - rho). No patient data.
"""
from typing import Literal
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
import scene as SC

router = APIRouter(prefix="/v1/scene", tags=["Scene (live 4D cube)"])


class SceneIn(BaseModel):
    L: float = Field(..., ge=0, le=1)
    E: float = Field(..., ge=0, le=1)
    V: float = Field(..., ge=0, le=1)
    rho_now: float = Field(..., ge=0, lt=1)
    rho_after: float = Field(..., ge=0, lt=1)
    domain: Literal["disaster", "oncology"] = "disaster"
    label: str = Field("custom", max_length=60, description="Short label for the scene. Never a name or identifier.")
    per_leg: int = Field(12, ge=2, le=60, description="Frames per leg of the walk through the cube")


@router.get("/cases")
def scene_cases():
    return {"count": len(SC.list_cases()), "cases": SC.list_cases(), "disclaimer": SC.DISCLAIMER}


@router.get("/{key}")
def scene_case(key: str, per_leg: int = Query(12, ge=2, le=60)):
    try:
        return SC.scene_for_case(key, per_leg)
    except KeyError as e:
        raise HTTPException(404, str(e).strip("'\""))


@router.post("")
def scene_custom(b: SceneIn):
    try:
        return SC.build(b.L, b.E, b.V, b.rho_now, b.rho_after, b.label, b.domain, b.per_leg)
    except ValueError as e:
        raise HTTPException(422, str(e))
