"""FastAPI router for the cohort sandboxes. Included from api.py, so the app-level X-API-Key dependency and the registry header apply."""
from typing import List, Literal, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import sandbox as B

router = APIRouter(prefix="/v1/sandbox", tags=["sandbox"])


class SandboxIn(BaseModel):
    records: Optional[List[dict]] = Field(None, max_length=B.MAX_ROWS, description="One dict per patient, columns as in GET /v1/sandbox/templates. Pseudonymous IDs only.")
    dataset: Optional[str] = Field(None, description="Id of a cohort bundled on the server (see GET /v1/sandbox/datasets) instead of records. Patient rows are not returned unless the server allows it.")
    options: dict = Field(default_factory=dict, description="Overrides of the defaults listed in GET /v1/sandbox/templates (E, rho, rho_after, C, l_tool, anchors, bootstrap, ...)")


@router.get("/datasets")
def list_datasets():
    """Cohorts bundled on this server (cohort_data/ or RMTI_COHORT_DIR). Aggregate scoring only; no patient rows are listed."""
    return [{k: v for k, v in d.items() if k in ("id", "disease", "label", "description")} | {"has_reference": bool(d["reference"])} for d in B.datasets().values()]


@router.get("/templates")
def templates():
    """Columns, required columns, status text and default options for each sandbox."""
    return B.templates()


@router.post("/{disease}/score")
def score(disease: Literal["hcc", "lung", "breast"], b: SandboxIn):
    """Score a cohort (R, tier, EAL, rho-after) and report tier distribution and, if time/cause columns exist, descriptive outcomes.
    cause: 1 event, 2 competing event, 0 censored. Adds no equation; research use only."""
    try:
        return B.run(disease, b.records, b.dataset, b.options)
    except (ValueError, KeyError) as e:
        raise HTTPException(422, str(e))
