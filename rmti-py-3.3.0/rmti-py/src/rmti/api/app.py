# Copyright 2025-2026 Cesar Marolla. Apache-2.0.
"""RMTI REST API (v1).  Run:  uvicorn rmti.api:app   |   Developer portal at /portal/, OpenAPI at /openapi.json.

Security posture (see /v1/methodology -> data_handling for the machine-readable version):
stateless; no persistence; payloads are never logged; keys are stored hashed; protected routes fail closed when no
keys are configured; errors never echo submitted values. NOT HIPAA-attested, no BAA, no SOC 2: do not send PHI.
"""
from __future__ import annotations

import logging
import re
import time
import uuid
from pathlib import Path
from typing import Callable, Optional

import numpy as np
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, Response, Security, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import APIKeyHeader
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from .. import __version__
from ..core import TIER_NAMES, TIER_POSTURE, TIER_RANGES, TIER_THRESHOLDS
from ..optimizer import Project, optimize_portfolio
from ..stochastic import WOE_CONCENTRATION, UncertainParam, simulate_rmti
from . import fhir as fhirmod
from . import service as svc
from .config import Settings
from .schemas import (AlbiRequest, Assessment, AssessmentResponse, CohortRequest, CohortResponse, HccRequest,
                      OptimizeRequest, Problem, SimulationRequest, SimulationResponse)
from .security import ANONYMOUS, Client, RateLimiter, hash_key

log = logging.getLogger("rmti.api.access")
PORTAL_DIR = Path(__file__).resolve().parent.parent / "portal"
_RID = re.compile(r"^[A-Za-z0-9._\-]{8,64}$")

DESCRIPTION = """
Programmatic access to the **Risk Mechanism Theory Index (RMTI)**: `R = L · E · V · (1 − ρ)`, five fixed decision tiers,
expected annual loss, uncertainty propagation, portfolio optimisation, HCC-surveillance scoring and HL7 FHIR R4 output.

**Status: research prototype.** Not validated against outcomes. Not a medical device. Results are decision-support indices,
not probabilities. **Do not send protected health information**; use de-identified identifiers only. This service is not
HIPAA-attested (no BAA) and holds no SOC 2 / ISO 27001 certification.
"""
TAGS = [
    {"name": "Assessments", "description": "Score single units and cohorts."},
    {"name": "Uncertainty & planning", "description": "Monte Carlo tier probabilities and budgeted portfolio selection."},
    {"name": "HCC surveillance", "description": "Patient-level hepatocellular-carcinoma surveillance triage (research use)."},
    {"name": "FHIR R4", "description": "RiskAssessment / Bundle output. Not a FHIR server."},
    {"name": "Reference", "description": "Public metadata: health, methodology, limits."},
]
ERRORS = {401: {"model": Problem, "description": "Missing or invalid API key"}, 403: {"model": Problem, "description": "Key lacks the required scope"},
          422: {"model": Problem, "description": "Validation failed (no submitted values are echoed)"},
          429: {"model": Problem, "description": "Rate limit exceeded; see Retry-After"}}


class FhirJSONResponse(JSONResponse):
    media_type = "application/fhir+json"


def _problem(status: int, title: str, detail: Optional[str] = None, rid: Optional[str] = None, errors=None, headers=None):
    body = {"type": "about:blank", "title": title, "status": status}
    if detail:
        body["detail"] = detail
    if rid:
        body["request_id"] = rid
    if errors:
        body["errors"] = errors
    return JSONResponse(body, status_code=status, media_type="application/problem+json", headers=headers)


def create_app(settings: Optional[Settings] = None) -> FastAPI:
    st = settings or Settings.from_env()
    app = FastAPI(title="RMTI API", version=__version__, description=DESCRIPTION, openapi_tags=TAGS,
                  contact={"name": "RMTI maintainers", "email": st.contact} if "@" in st.contact else None,
                  license_info={"name": "Apache-2.0", "url": "https://www.apache.org/licenses/LICENSE-2.0"},
                  docs_url="/docs", redoc_url="/redoc")
    app.state.settings, app.state.limiter = st, RateLimiter()
    if st.auth == "disabled":
        log.warning("RMTI_AUTH=disabled: all protected routes are open. Local development only.")
    if st.cors_origins:
        from fastapi.middleware.cors import CORSMiddleware
        app.add_middleware(CORSMiddleware, allow_origins=list(st.cors_origins), allow_methods=["GET", "POST"],
                           allow_headers=["X-API-Key", "Content-Type", "X-Request-ID"],
                           expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining", "Retry-After"])

    # ------------------------------------------------------------------ middleware
    @app.middleware("http")
    async def envelope(request: Request, call_next: Callable):
        t0 = time.perf_counter()
        rid = request.headers.get("x-request-id", "")
        rid = rid if _RID.match(rid) else uuid.uuid4().hex
        request.state.request_id, request.state.client = rid, None
        limit = st.max_upload_bytes + 65_536 if request.url.path.endswith("/upload") else st.max_json_bytes
        cl = request.headers.get("content-length")
        if cl and cl.isdigit() and int(cl) > limit:
            resp = _problem(413, "Payload too large", f"limit is {limit} bytes", rid)
        else:
            resp = await call_next(request)
        resp.headers["X-Request-ID"] = rid
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["Referrer-Policy"] = "no-referrer"
        if request.url.path.startswith("/v1/"):
            resp.headers["Cache-Control"] = "no-store"
        c = request.state.client
        log.info("%s %s %s client=%s ms=%.1f rid=%s", request.method, request.url.path, resp.status_code,
                 c.name if c else "-", (time.perf_counter() - t0) * 1000, rid)          # metadata only, never bodies
        return resp

    @app.exception_handler(StarletteHTTPException)
    async def http_err(request: Request, exc: StarletteHTTPException):
        return _problem(exc.status_code, {401: "Unauthorized", 403: "Forbidden", 404: "Not found", 405: "Method not allowed",
                                          429: "Too many requests"}.get(exc.status_code, "Error"),
                        str(exc.detail) if exc.detail else None, getattr(request.state, "request_id", None),
                        headers=getattr(exc, "headers", None))

    @app.exception_handler(RequestValidationError)
    async def val_err(request: Request, exc: RequestValidationError):
        errs = [{"loc": [str(x) for x in e["loc"]], "msg": e["msg"], "type": e["type"]} for e in exc.errors()][:50]   # no 'input'
        return _problem(422, "Validation failed", "request body or parameters are invalid",
                        getattr(request.state, "request_id", None), errs)

    # ------------------------------------------------------------------ auth
    key_header = APIKeyHeader(name="X-API-Key", scheme_name="ApiKeyAuth", auto_error=False,
                              description="Institutional API key (issued out of band; stored hashed server-side).")

    def requires(scope: str):
        def dep(request: Request, response: Response, api_key: Optional[str] = Security(key_header)) -> Client:
            if st.auth == "disabled":
                client = ANONYMOUS
            else:
                if not st.clients:
                    raise HTTPException(503, "API authentication is not configured on this server")
                if not api_key:
                    raise HTTPException(401, "missing X-API-Key header", headers={"WWW-Authenticate": 'ApiKey realm="rmti"'})
                client = st.clients.get(hash_key(api_key))
                if client is None:
                    raise HTTPException(401, "invalid API key", headers={"WWW-Authenticate": 'ApiKey realm="rmti"'})
                if scope not in client.scopes:
                    raise HTTPException(403, f"key does not carry the '{scope}' scope")
            ok, remaining, retry = app.state.limiter.check(client.name, client.rate_per_min)
            if not ok:
                raise HTTPException(429, "rate limit exceeded", headers={"Retry-After": str(retry), "X-RateLimit-Remaining": "0",
                                                                        "X-RateLimit-Limit": str(client.rate_per_min)})
            response.headers["X-RateLimit-Limit"] = str(client.rate_per_min)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            request.state.client = client
            return client
        return dep

    def scope_ext(scope: str):
        return {"x-required-scope": scope}

    # ------------------------------------------------------------------ reference (public)
    @app.get("/v1/health", tags=["Reference"], summary="Service health")
    def health():
        return {"status": "ok", "version": __version__, "auth": st.auth}

    @app.get("/v1/methodology", tags=["Reference"], summary="Equation, tiers, limitations, data handling")
    def methodology():
        ex = svc.build_results([{"record_id": "EXAMPLE-001", "domain": "example", "likelihood": 0.9, "exposure": 0.65,
                                 "vulnerability": 0.8, "resilience": 0.2}],
                               svc.assess_arrays([0.9], [0.65], [0.8], [0.2], [0.55], [5], [16e6]))[0].model_dump()
        return {
            "engine": svc.engine().model_dump(),
            "equations": {"inherent_risk": "IR = L * E * V", "residual_risk": "R = IR * (1 - rho)",
                          "expected_annual_loss": "EAL = L * C * (1 - rho)  (index, not currency)",
                          "equity_rate": "EAL / N, per 1,000,000 residents"},
            "parameters": {"L": "likelihood [0,1] (rubric scale)", "E": "exposure share [0,1]", "V": "vulnerability [0,1]",
                           "rho": "resilience: fraction of inherent risk absorbed [0,1]", "C": "consequence level 1-5 -> 0.10/0.30/0.50/0.75/1.00"},
            "tiers": [{"tier": i + 1, "label": TIER_NAMES[i], "posture": TIER_POSTURE[i], "range": TIER_RANGES[i]} for i in range(5)],
            "tier_thresholds": list(TIER_THRESHOLDS),
            "evidence_grade_concentration_ASSUMED": WOE_CONCENTRATION,
            "limits": {"max_rows_per_request": st.max_rows, "max_upload_bytes": st.max_upload_bytes},
            "limitations": [
                "Research prototype; not validated against outcomes; not a medical device.",
                "R is a relative index, not a probability. EAL is an index, not a monetary loss.",
                "Inputs are analyst- or source-supplied; resilience_after values are scenario assumptions.",
                "Fixed tier thresholds were set for disaster-risk use and have not been recalibrated for clinical action.",
                "Uncertainty results rest on an assumed mapping from evidence grade to variance.",
                "Multi-asset portfolio optimisation sums relative indices, which assumes commensurability."],
            "data_handling": {
                "persistence": "none: the service is stateless and stores no request or response data",
                "payload_logging": "none: access logs hold method, path, status, client name, latency and request id only",
                "api_keys": "stored as SHA-256 digests; shown once at creation; scoped; rate limited",
                "transport_security": "TLS is provided by the deployment (reverse proxy / platform), not by this application",
                "phi": "do not send protected health information; use de-identified identifiers",
                "certifications": {"hipaa_baa_available": False, "soc2": False, "iso27001": False, "medical_device": False}},
            "fhir": {"version": "R4 (4.0.1)", "resource": "RiskAssessment", "is_fhir_server": False, "example": fhirmod.risk_assessment(ex)},
            "contact": st.contact or None,
            "citation": "Marolla, C. (2026). From Narrative to Algorithm. Int. J. Management and Data Analytics 6(1):354-388. doi:10.68485/ijmada.20266156",
        }

    # ------------------------------------------------------------------ assessments
    def _single(a: Assessment) -> dict:
        cols = svc.columns_from_models([a])
        arr = svc.assess_arrays(cols["L"], cols["E"], cols["V"], cols["rho"], cols["rho_after"], cols["C"], cols["N"])
        return svc.build_results([a.model_dump()], arr, with_margin=True)[0]

    @app.post("/v1/assessments", tags=["Assessments"], response_model=AssessmentResponse, responses=ERRORS,
              summary="Score one unit", openapi_extra=scope_ext("score"))
    def assess_one(a: Assessment, client: Client = Depends(requires("score"))):
        return {"engine": svc.engine(), "result": _single(a)}

    def _cohort(name: str, records, cols, include: bool, client: Client) -> dict:
        arr = svc.assess_arrays(cols["L"], cols["E"], cols["V"], cols["rho"], cols["rho_after"], cols["C"], cols["N"])
        return {"engine": svc.engine(), "cohort_name": name, "client": client.name,
                "summary": svc.summarize(arr["R"], arr["tier"]),
                "records": svc.build_results(records, arr) if include else None}

    @app.post("/v1/cohorts/score", tags=["Assessments"], response_model=CohortResponse, responses=ERRORS,
              summary="Score a cohort (JSON, up to 10,000 records)", openapi_extra=scope_ext("batch"))
    def cohort_json(b: CohortRequest, client: Client = Depends(requires("batch"))):
        if len(b.records) > st.max_rows:
            raise HTTPException(413, f"limit is {st.max_rows} records per request")
        return _cohort(b.cohort_name, [r.model_dump() for r in b.records], svc.columns_from_models(b.records), b.include_records, client)

    @app.post("/v1/cohorts/score/upload", tags=["Assessments"], response_model=CohortResponse, responses=ERRORS,
              summary="Score a cohort from a CSV or Parquet file", openapi_extra=scope_ext("batch"))
    async def cohort_upload(request: Request, cohort_name: str = Form(..., pattern=r"^[A-Za-z0-9._:\- ]{1,96}$"),
                            include_records: bool = Form(True), file: UploadFile = File(..., description="CSV or Parquet; columns: likelihood, exposure, vulnerability, resilience; optional record_id, resilience_after, consequence_level, population"),
                            client: Client = Depends(requires("batch"))):
        blob = await file.read(st.max_upload_bytes + 1)
        if len(blob) > st.max_upload_bytes:
            raise HTTPException(413, f"limit is {st.max_upload_bytes} bytes")
        try:
            df = svc.read_table(blob, file.filename or "", st.max_rows)
            records, cols = svc.validate_assessment_table(df)
        except svc.TableError as e:
            return _problem(e.status, "Upload rejected", str(e), request.state.request_id, e.errors)
        return _cohort(cohort_name, records, cols, include_records, client)

    # ------------------------------------------------------------------ uncertainty & planning
    @app.post("/v1/simulations", tags=["Uncertainty & planning"], response_model=SimulationResponse, responses=ERRORS,
              summary="Monte Carlo tier probabilities", openapi_extra=scope_ext("score"))
    def simulate(b: SimulationRequest, client: Client = Depends(requires("score"))):
        mk = lambda p: UncertainParam(p.mean, p.evidence_grade, p.sd)
        try:
            r = simulate_rmti(mk(b.likelihood), mk(b.exposure), mk(b.vulnerability), mk(b.resilience),
                              mk(b.resilience_after) if b.resilience_after else None, b.n_sims, b.seed, b.correlation)
        except (ValueError, np.linalg.LinAlgError) as e:
            raise HTTPException(422, str(e))
        return {"engine": svc.engine(), "summary": r.summary()}

    @app.post("/v1/portfolios/optimize", tags=["Uncertainty & planning"], responses=ERRORS, summary="Select projects under a budget",
              openapi_extra=scope_ext("batch"))
    def optimize(b: OptimizeRequest, client: Client = Depends(requires("batch"))):
        try:
            ps = [Project(p.name, p.cost, p.residual_risk_now, p.residual_risk_after, p.group, p.population, p.eal_now, p.eal_after)
                  for p in b.projects]
            r = optimize_portfolio(ps, b.budget, b.objective, b.mandatory, b.max_projects)
        except ValueError as e:
            raise HTTPException(422, str(e))
        return {"engine": svc.engine(), "selected": r.selected, "total_cost": r.total_cost, "unspent": r.unspent,
                "objective": b.objective, "objective_value": r.objective_value, "total_delta_R": r.total_delta_R,
                "greedy_value": r.greedy_value,
                "caveat": "Sums relative risk indices across assets; resilience_after values are scenario assumptions."}

    # ------------------------------------------------------------------ HCC
    def _hcc_df(df, au, bu):
        from ..domains import hcc
        df = df.rename(columns={"l": "L", "e": "E", "likelihood": "L", "exposure": "E"})
        try:
            return hcc.score_table(df, au, bu)
        except ValueError as e:
            raise HTTPException(422, str(e))

    def _hcc_payload(out):
        counts = out["tier"].value_counts()
        return {"engine": svc.engine(), "disclaimer": "Research prototype; not for individual patient care decisions.",
                "tier_counts": {k: int(counts.get(k, 0)) for k in sorted(counts.index)},
                "patients": out.astype(object).where(out.notna(), None).to_dict(orient="records")}

    @app.post("/v1/hcc/patients/score", tags=["HCC surveillance"], responses=ERRORS, summary="Triage a patient list (JSON)",
              openapi_extra=scope_ext("score"))
    def hcc_score(b: HccRequest, client: Client = Depends(requires("score"))):
        import pandas as pd
        df = pd.DataFrame([{**p.model_dump(exclude_none=True), "L": p.likelihood, "E": p.exposure,
                            **({"id": p.record_id} if p.record_id else {})} for p in b.patients]).drop(columns=["likelihood", "exposure", "record_id"], errors="ignore")
        return _hcc_payload(_hcc_df(df, b.albumin_unit, b.bilirubin_unit))

    @app.post("/v1/hcc/patients/score/upload", tags=["HCC surveillance"], responses=ERRORS, summary="Triage a patient registry file (CSV/Parquet)",
              openapi_extra=scope_ext("score"))
    async def hcc_upload(request: Request, file: UploadFile = File(..., description="Columns: L, E, surveillance, bclc_if_missed, and albi_grade or albumin+bilirubin"),
                         albumin_unit: str = Form("g/L"), bilirubin_unit: str = Form("umol/L"), client: Client = Depends(requires("score"))):
        blob = await file.read(st.max_upload_bytes + 1)
        if len(blob) > st.max_upload_bytes:
            raise HTTPException(413, f"limit is {st.max_upload_bytes} bytes")
        if albumin_unit not in ("g/L", "g/dL") or bilirubin_unit not in ("umol/L", "mg/dL"):
            raise HTTPException(422, "unit must be g/L|g/dL (albumin) and umol/L|mg/dL (bilirubin)")
        try:
            df = svc.read_table(blob, file.filename or "", st.max_rows)
        except svc.TableError as e:
            return _problem(e.status, "Upload rejected", str(e), request.state.request_id)
        return _hcc_payload(_hcc_df(df, albumin_unit, bilirubin_unit))

    @app.post("/v1/hcc/albi", tags=["HCC surveillance"], responses=ERRORS, summary="ALBI score, grade and vulnerability anchor",
              openapi_extra=scope_ext("score"))
    def albi(b: AlbiRequest, client: Client = Depends(requires("score"))):
        from ..domains import hcc
        s = hcc.albi_score(b.albumin, b.bilirubin, b.albumin_unit, b.bilirubin_unit)
        g = hcc.albi_grade(s)
        return {"albi_score": round(s, 4), "albi_grade": g, "vulnerability_anchor": hcc.albi_grade_to_V(g)}

    # ------------------------------------------------------------------ FHIR
    @app.post("/v1/fhir/RiskAssessment", tags=["FHIR R4"], responses={**ERRORS, 200: {"content": {"application/fhir+json": {}}}},
              response_class=FhirJSONResponse, summary="Score one unit and return a FHIR R4 RiskAssessment",
              openapi_extra=scope_ext("fhir"))
    def fhir_one(a: Assessment, client: Client = Depends(requires("fhir"))):
        return FhirJSONResponse(fhirmod.risk_assessment(_single(a).model_dump()))

    @app.post("/v1/fhir/RiskAssessment/_batch", tags=["FHIR R4"], responses={**ERRORS, 200: {"content": {"application/fhir+json": {}}}},
              response_class=FhirJSONResponse, summary="Score a cohort and return a FHIR R4 Bundle (collection)",
              openapi_extra=scope_ext("fhir"))
    def fhir_batch(b: CohortRequest, client: Client = Depends(requires("fhir"))):
        cols = svc.columns_from_models(b.records)
        arr = svc.assess_arrays(cols["L"], cols["E"], cols["V"], cols["rho"], cols["rho_after"], cols["C"], cols["N"])
        res = svc.build_results([r.model_dump() for r in b.records], arr)
        return FhirJSONResponse(fhirmod.bundle(fhirmod.risk_assessment(r.model_dump()) for r in res))

    # ------------------------------------------------------------------ portal
    @app.get("/", include_in_schema=False)
    def root():
        return RedirectResponse("/portal/")

    if PORTAL_DIR.exists():
        app.mount("/portal", StaticFiles(directory=str(PORTAL_DIR), html=True), name="portal")
    return app


app = create_app()
