"""Risk Mechanism Theory Index (RMTI) API (FastAPI). Core logic created and formulated by Dr. Cesar Marolla.
Run: uvicorn api:app --port 8000   Portal: /   Reference: /docs   Widget: /widget"""
from typing import List, Optional, Literal
import hmac, os
from fastapi import Request, FastAPI, HTTPException, Depends, Header, Security
from pydantic import BaseModel, ConfigDict, Field
import service as S
import registry as R
import portal

def require_key(request: Request, x_api_key: Optional[str] = Security(portal.api_key_header)):
    """If RMTI_API_KEYS (comma-separated) is set, every /v1 call needs a matching X-API-Key header.
    /health, the portal (/), /docs, /redoc, /openapi.json and /widget are open: they carry versions, schema and a client-side viewer only."""
    if portal.is_public(request.url.path):
        return
    keys = [k for k in os.environ.get("RMTI_API_KEYS", "").split(",") if k]
    if not keys and os.environ.get("RMTI_ENV", "").lower() == "production":
        raise HTTPException(503, "RMTI_ENV=production but RMTI_API_KEYS is not set; refusing to serve open")   # fail closed
    if keys and not (x_api_key and any(hmac.compare_digest(x_api_key, k) for k in keys)):
        raise HTTPException(401, "Missing or invalid X-API-Key")


app = FastAPI(title=portal.TITLE, version=S.ENGINE_VERSION, dependencies=[Depends(require_key)],
              summary=portal.BYLINE + " | " + portal.TAGLINE,
              description=portal.DESCRIPTION + "\n\n" + S.DISCLAIMER + " Engine: RMTI time-indexed v" + S.ENGINE_VERSION,
              openapi_tags=portal.TAGS, docs_url=None, redoc_url="/redoc",
              contact={"name": "Dr. Cesar Marolla", "url": "https://orcid.org/0000-0001-8498-7380"},
              license_info={"name": "Apache-2.0", "url": "https://www.apache.org/licenses/LICENSE-2.0.html"})
# RMTI v2.3.0 vocabulary: domain "oncoclastics" (+ site "hcc", "lung" or "breast") or "disaster_science". Internal keys hcc/lung/breast/disaster still work.
Domain = Literal["oncoclastics", "disaster_science", "hcc", "lung", "breast", "disaster"]   # CHANGED: added "breast"
Site = Literal["hcc", "lung", "breast"]                                                     # CHANGED: one place to list cancer sites
U = Field(..., ge=0, le=1)


class SnapshotIn(BaseModel):
    """Strict input: L, E and V must lie in [0, 1], rho_now and rho_after in [0, 1), C in 1..5, and unknown fields are rejected (HTTP 422)."""
    model_config = ConfigDict(extra="forbid", json_schema_extra={"examples": [
        {"domain": "oncoclastics", "site": "hcc", "N": 100000, "L": 0.30, "E": 0.65, "V": 0.55, "rho_now": 0.20, "rho_after": 0.50, "C": 5}]})
    domain: Domain = "hcc"
    site: Optional[Site] = Field(None, description="Cancer-site module when domain is oncoclastics (default hcc)")
    N: float = Field(100_000, gt=0, description="At-risk population / cohort size")
    L: float = U; E: float = U; V: float = U
    rho_now: float = Field(..., ge=0, lt=1)
    rho_after: Optional[float] = Field(None, ge=0, lt=1)
    C: int = Field(5, ge=1, le=5)


class TrajectoryIn(BaseModel):
    domain: Domain = "hcc"
    site: Optional[Site] = None
    L: float = U; E: float = U
    C: int = Field(3, ge=1, le=5)
    rho0: float = Field(..., ge=0, le=0.95)
    observations: List[Optional[float]] = Field(..., min_length=1, description="null = missed visit")
    delivery: List[Optional[float]]
    params: Optional[dict] = Field(None, description="override alpha, beta, look_ahead, lam, v_lo, v_hi, y_max, rho_ceiling")


class CohortRow(SnapshotIn):
    model_config = ConfigDict(extra="ignore")   # uploaded CSVs may carry extra columns; the five levers are still range-checked
    name: str


class CohortIn(BaseModel):
    domain: Domain = "hcc"
    site: Optional[Site] = None
    patients: List[CohortRow]


def _guard(fn, *a, **k):
    try:
        return fn(*a, **k)
    except (ValueError, KeyError) as e:      # engine validation errors -> 422, not 500
        raise HTTPException(422, str(e))


@app.middleware("http")
async def registry_header(request, call_next):
    """Stamp every response with the registry version+hash that produced it (traceability)."""
    resp = await call_next(request)
    resp.headers["X-RMTI-Registry"] = R.stamp()
    return resp


_origins = [o.strip() for o in os.environ.get("RMTI_CORS_ORIGINS", "").split(",") if o.strip()]
if _origins:                                   # off by default; list exact https origins of trusted front-ends, never "*" together with keys
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(CORSMiddleware, allow_origins=_origins, allow_methods=["GET", "POST", "OPTIONS"],
                       allow_headers=["X-API-Key", "X-Admin-Key", "Content-Type"], max_age=600)


@app.get("/health", dependencies=[])
def health():
    return {"status": "ok", "engine": S.ENGINE_VERSION, "registry": R.stamp(), "disclaimer": S.DISCLAIMER}


@app.post("/v1/snapshot")
def snapshot(b: SnapshotIn):
    return _guard(S.snapshot, S.resolve_domain(b.domain, b.site), b.N, b.L, b.E, b.V, b.rho_now, b.rho_after, b.C)


@app.post("/v1/trajectory")
def trajectory(b: TrajectoryIn):
    return _guard(S.trajectory, S.resolve_domain(b.domain, b.site), b.L, b.E, b.C, b.rho0, b.observations, b.delivery, b.params)


@app.post("/v1/cohort/rank")
def cohort(b: CohortIn):
    rows = [{k: v for k, v in p.model_dump().items() if k not in ("domain", "site") and v is not None} for p in b.patients]
    return _guard(S.cohort, S.resolve_domain(b.domain, b.site), rows)


class ValidateIn(BaseModel):
    domain: Domain = "hcc"
    site: Optional[Site] = None
    records: List[dict] = Field(..., description="Long-format serial rows: patient_id, cycle, y, [delivery, L, E, C, rho0, event, time]")
    bootstrap: int = Field(0, ge=0, le=2000, description="Bootstrap resamples for 95% CIs (0 = off)")


@app.post("/v1/validate")
def validate(b: ValidateIn):
    import pandas as pd
    v = _guard(S.validate_serial, pd.DataFrame(b.records), S.resolve_domain(b.domain, b.site))
    out = {k: x for k, x in v.items() if k not in ("patients", "by_tier", "km")}
    if "c_index_final" in v:
        out["calibration"] = S.calibration(v["patients"])["by_tier"].to_dict("records")
        out["slope_log_R"] = S.calibration(v["patients"])["slope_log_R"]
        out["km"] = v["km"]
        if b.bootstrap:
            out["bootstrap"] = S.bootstrap_ci(v["patients"], b.bootstrap)
    out["patients"] = v["patients"].to_dict("records")
    return out


class LungInputsIn(BaseModel):
    risk5: float = Field(..., ge=0, le=1, description="5-year lung-cancer risk (fraction) from a validated tool. 2-year risks are refused.")
    horizon_years: int = Field(5, description="Must be 5")
    ecog: Optional[int] = Field(None, ge=0, le=4, description="ECOG/WHO PS 0-4 -> rho_bio on the chosen ladder")
    ladder: Optional[Literal["A", "B"]] = Field(None, description="Default: the registry's active ladder")
    l_tool: str = Field("Other or custom tool (tick the variables)", description="Validated L tool, used to block overlapping V items")
    v_items: List[str] = Field(default_factory=list, description="Labels of V items present")


@app.post("/v1/lung/inputs")
def lung_inputs(b: LungInputsIn):
    """Turn raw lung inputs into the engine's L, V and rho_bio, with the registry stamp. Adds no equation."""
    return _guard(S.lung_inputs, b.risk5, b.horizon_years, b.ecog, b.ladder, b.l_tool, b.v_items)


class HccPatientIn(BaseModel):
    age_years: float = Field(..., ge=18, le=110)
    male: int = Field(..., ge=0, le=1, description="1 = male, 0 = female")
    albumin_g_l: float = Field(..., gt=0, le=70)
    bilirubin_umol_l: float = Field(..., gt=0, le=1000)
    platelets_1e9_l: float = Field(..., ge=0, le=2000)
    l_tool: Literal["aMAP-ref", "aMAP"] = Field("aMAP-ref", description="aMAP-ref (clean). aMAP overlaps ALBI and needs allow_overlap.")
    allow_overlap: bool = Field(False, description="Only to quantify double counting; the reply is labelled DIAGNOSTIC.")
    E: float = Field(0.60, ge=0, le=1); rho: float = Field(0.20, ge=0, lt=1); rho_after: float = Field(0.65, ge=0, lt=1)
    C: int = Field(5, ge=1, le=5)


@app.post("/v1/hcc/patient")
def hcc_patient(b: HccPatientIn):
    """Patient-level RMTI-HCC from routine labs. Adds no equation; refuses the L/V variable overlap by default."""
    return _guard(S.hcc_patient, b.age_years, b.male, b.albumin_g_l, b.bilirubin_umol_l, b.platelets_1e9_l, b.l_tool, b.E, b.rho, b.rho_after, b.C, b.allow_overlap)


class TwoSenseIn(BaseModel):
    L: float = U; E: float = U; V: float = U
    rho_bio: float = Field(0.0, ge=0, lt=1, description="Biological reserve (0 = not scored; anchors 0.10-0.70)")
    rho_care: float = Field(..., ge=0, lt=1, description="Care-system capacity (surveillance delivery)")
    rho_care_after: Optional[float] = Field(None, ge=0, lt=1, description="Optional: rho_care after a disruption of care")
    C: int = Field(3, ge=1, le=5)


@app.post("/v1/oncoclastics/two-sense")
def two_sense(b: TwoSenseIn):
    """Oncoclastics, biological sense (L, E, V, rho_bio) and care-system sense (rho_care), v2.3.0 module unchanged."""
    return _guard(S.two_sense_snapshot, b.L, b.E, b.V, b.rho_bio, b.rho_care, b.C, b.rho_care_after)


class TwoSenseTrajIn(TrajectoryIn):
    rho_bio: float = Field(0.0, ge=0, lt=1)
    v_step: float = Field(0.0, ge=0, description="Biological-sense event threshold on V*(t); uncalibrated")


@app.post("/v1/oncoclastics/trajectory")
def two_sense_traj(b: TwoSenseTrajIn):
    """Time-indexed two-sense run plus descriptive oncoclastic events (each names its sense). Flags are not alerts."""
    return _guard(S.two_sense_trajectory, S.resolve_domain(b.domain, b.site), b.L, b.E, b.C, b.rho_bio, b.rho0, b.observations, b.delivery, b.params, b.v_step)


class FhirIn(SnapshotIn):
    label: str = Field(..., min_length=1, max_length=60, description="Pseudonymous study code. Never a name.")
    rho_bio: float = Field(0.0, ge=0, lt=1)


@app.post("/v1/fhir/risk-assessment")
def fhir_risk_assessment(b: FhirIn):
    """FHIR R4 RiskAssessment, status 'preliminary', research use. R is exported as a tier plus a named extension, never as a probability."""
    from fastapi.responses import JSONResponse
    inputs = dict(N=b.N, L=b.L, E=b.E, V=b.V, rho_now=b.rho_now, rho_after=b.rho_after, C=b.C, rho_bio=b.rho_bio)
    ra = _guard(S.fhir_risk_assessment, b.label, b.domain, inputs, b.site)
    return JSONResponse(ra, media_type="application/fhir+json")


# ---- registry: evidence, parameters, cohort support, proposals ---------------------------------------------------------
def require_admin(x_admin_key: Optional[str] = Header(None)):
    """Proposals need RMTI_ADMIN_KEYS (comma-separated). If none is configured, proposing is disabled, not open."""
    keys = [k for k in os.environ.get("RMTI_ADMIN_KEYS", "").split(",") if k]
    if not keys or not (x_admin_key and any(hmac.compare_digest(x_admin_key, k) for k in keys)):
        raise HTTPException(403, "Admin key required (set RMTI_ADMIN_KEYS and send X-Admin-Key)")


@app.get("/v1/registry")
def registry_status():
    """Registry version and hash, lock state, counts, and any consistency problems."""
    r = R.load()
    return {"stamp": R.stamp(), "version": r["evidence"]["registry_version"], "engine": S.ENGINE_VERSION,
            "parameters_locked": r["parameters"]["locked"], "parameters_sha256": R.params_hash(),
            "counts": {"evidence": len(r["evidence"]["evidence"]), "supplementary": len(r["evidence"]["supplementary"]),
                       "cohorts": len(r["cohorts"].get("cohorts", []))},
            "problems": R.validate(r)}


@app.get("/v1/registry/evidence")
def registry_evidence(scope: Optional[str] = None, include_supplementary: bool = True):
    r = R.load()["evidence"]
    rows = list(r["evidence"]) + (list(r["supplementary"]) if include_supplementary else [])
    if scope:
        rows = [e for e in rows if scope in str(e.get("cancer_scope", ""))]
    return {"version": r["registry_version"], "count": len(rows), "evidence": rows}


@app.get("/v1/registry/parameters")
def registry_parameters():
    p = R.load()["parameters"]
    return dict(p, parameters_sha256=R.params_hash(),
                note="Provisional unless locked. Evidence grades are reviewer-assigned. Constants are changed only by a reviewed release, never by uploaded data.")


@app.get("/v1/registry/ladder-check")
def registry_ladder_check(source: Optional[str] = None, ladder: Optional[str] = None):
    """Face-validity check: ladder-implied risk multipliers versus published adjusted hazard ratios (not calibration). ladder= A or B (default: the active ladder)."""
    return {"stamp": R.stamp(), "checks": _guard(R.ladder_face_validity, source, ladder),
            "note": "Care capacity held fixed, so R scales with (1 - rho_bio). R is not a hazard and rho_bio values are assigned, not estimated."}


@app.get("/v1/registry/cohorts")
def registry_cohorts():
    return R.load()["cohorts"]


class LadderSupportIn(BaseModel):
    records: List[dict] = Field(..., description="Rows with ecog (0-4), time (>0) and event (0/1). Pseudonymous only.")
    ecog_col: str = "ecog"
    time_col: str = "time"
    event_col: str = "event"
    min_events: int = Field(10, ge=1, le=1000)


@app.post("/v1/registry/ladder-support")
def ladder_support(b: LadderSupportIn):
    """Does this dataset separate each adjacent ECOG step? Descriptive report; stores nothing; changes no constant."""
    import pandas as pd
    df = _guard(S.privacy_check, pd.DataFrame(b.records))
    return _guard(R.ladder_support, df, b.ecog_col, b.time_col, b.event_col, b.min_events)


class CohortMetaIn(BaseModel):
    id: str; source_evidence_id: str; centre: str; period: str; n: int = Field(..., ge=1)
    cancer_scope: str; ecog_levels_reported: str; ecog_pooling: str


@app.post("/v1/registry/cohorts/check", description="Preview overlap with registered cohorts. Writes nothing.")
def cohort_overlap(b: CohortMetaIn):
    return {"overlap_flags": R.overlap_flags(b.model_dump(), R.load()["cohorts"].get("cohorts", []))}


class ProposalIn(BaseModel):
    target: str = Field(..., description="e.g. 'rho_bio_ladder', 'L_anchors', 'evidence:add'")
    reason: str = Field(..., min_length=20)
    payload: dict = {}
    author: str = Field(..., min_length=2, max_length=60, description="Pseudonymous reviewer code")


@app.post("/v1/registry/proposals", dependencies=[Depends(require_admin)])
def registry_propose(b: ProposalIn):
    """Queue a change for human review. The active registry is NOT modified."""
    return {"proposal_id": _guard(R.propose, {"target": b.target, "reason": b.reason, "payload": b.payload}, b.author),
            "status": "pending-review"}


@app.get("/v1/registry/proposals", dependencies=[Depends(require_admin)])
def registry_proposals():
    return R.list_proposals()


# ---- developer portal (/), themed reference (/docs), embeddable widget (/widget); also groups the routes above into tags
portal.mount(app, S.ENGINE_VERSION)
