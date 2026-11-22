# Copyright 2025-2026 Cesar Marolla. Apache-2.0.
"""Request/response models. Field names are descriptive (no single-letter symbols) for non-specialist integrators."""
from __future__ import annotations

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

ID_PATTERN = r"^[A-Za-z0-9._:\-]{1,64}$"
DOMAIN_PATTERN = r"^[a-z0-9_\-]{1,48}$"
U = dict(ge=0.0, le=1.0)
Surveillance = Literal["none", "usual", "outreach", "specialist", "optimised"]
Bclc = Literal["0", "A", "early-int", "B", "C-D"]


class Problem(BaseModel):
    """RFC 7807-style error body. Never contains submitted values."""
    type: str = "about:blank"
    title: str
    status: int
    detail: Optional[str] = None
    request_id: Optional[str] = None
    errors: Optional[List[dict]] = None


class Assessment(BaseModel):
    """One assessed unit (a facility, district, asset, patient stratum). Use de-identified identifiers only."""
    record_id: Optional[str] = Field(None, pattern=ID_PATTERN, description="De-identified identifier (letters, digits, . _ : -). No names or direct identifiers.")
    domain: Optional[str] = Field(None, pattern=DOMAIN_PATTERN, description="Free label, e.g. hcc_surveillance, urban_flood.")
    likelihood: float = Field(..., **U, description="L: hazard likelihood on the rubric scale [0, 1]. A rubric value, not necessarily an annual probability.")
    exposure: float = Field(..., **U, description="E: share of the population or assets inside the hazard (or surveillance) footprint [0, 1].")
    vulnerability: float = Field(..., **U, description="V: sensitivity to disruption given the hazard [0, 1].")
    resilience: float = Field(..., **U, description="rho: fraction of inherent risk absorbed by existing protection [0, 1].")
    resilience_after: Optional[float] = Field(None, **U, description="rho after a proposed intervention (scenario assumption).")
    consequence_level: Optional[int] = Field(None, ge=1, le=5, description="C level 1-5 (Table 2); enables expected annual loss (EAL).")
    population: Optional[float] = Field(None, gt=0, description="N, for the per-capita equity rate (EAL per million).")

    model_config = ConfigDict(json_schema_extra={"examples": [{
        "record_id": "FAC-0042", "domain": "hcc_surveillance", "likelihood": 0.65, "exposure": 0.70, "vulnerability": 0.55,
        "resilience": 0.20, "resilience_after": 0.65, "consequence_level": 5, "population": 120000}]})


class Margin(BaseModel):
    lower_threshold: Optional[float] = None
    upper_threshold: Optional[float] = None
    relative_change_to_lower: Optional[float] = Field(None, description="Relative change in any ONE of L, E or V that would lower the tier.")
    relative_change_to_upper: Optional[float] = Field(None, description="Relative change in any ONE of L, E or V that would raise the tier.")


class AssessmentResult(BaseModel):
    record_id: Optional[str] = None
    domain: Optional[str] = None
    inherent_risk: float = Field(..., description="IR = L*E*V")
    residual_risk: float = Field(..., description="R = IR*(1-rho). A relative index, not a probability.")
    tier: int = Field(..., ge=1, le=5)
    tier_label: str
    posture: str
    expected_annual_loss: Optional[float] = Field(None, description="EAL = L*C*(1-rho): an index, not a monetary loss.")
    equity_rate_per_million: Optional[float] = None
    residual_risk_after: Optional[float] = None
    tier_after: Optional[int] = None
    risk_reduction_pct: Optional[float] = None
    margin: Optional[Margin] = None


class Engine(BaseModel):
    name: str = "rmti"
    version: str
    equation: str = "R = L * E * V * (1 - rho)"
    status: str = "research prototype; not validated against outcomes; not a medical device"


class AssessmentResponse(BaseModel):
    engine: Engine
    result: AssessmentResult


class CohortRequest(BaseModel):
    cohort_name: str = Field(..., pattern=r"^[A-Za-z0-9._:\- ]{1,96}$")
    include_records: bool = Field(True, description="Set false to return only the summary.")
    records: List[Assessment] = Field(..., min_length=1, max_length=10_000)


class TierBin(BaseModel):
    tier: int
    label: str
    posture: str
    range: str
    count: int
    share: float


class CohortSummary(BaseModel):
    n: int
    residual_risk_mean: float
    residual_risk_median: float
    residual_risk_p90: float
    residual_risk_max: float
    tier_distribution: List[TierBin]


class CohortResponse(BaseModel):
    engine: Engine
    cohort_name: str
    client: str
    summary: CohortSummary
    records: Optional[List[AssessmentResult]] = None


class UncertainIn(BaseModel):
    mean: float = Field(..., **U)
    evidence_grade: Literal["w_ia", "w_ib", "w_ic", "w_id", "w_ie", "w_if"] = "w_ic"
    sd: Optional[float] = Field(None, ge=0.0, description="Explicit standard deviation; overrides evidence_grade.")


class SimulationRequest(BaseModel):
    likelihood: UncertainIn
    exposure: UncertainIn
    vulnerability: UncertainIn
    resilience: UncertainIn
    resilience_after: Optional[UncertainIn] = None
    n_sims: int = Field(20_000, ge=1_000, le=200_000)
    seed: int = 42
    correlation: Optional[List[List[float]]] = Field(None, description="4x4 symmetric matrix, order L, E, V, rho (Gaussian copula).")


class SimulationResponse(BaseModel):
    engine: Engine
    summary: dict
    assumption: str = ("Tier probabilities depend on an ASSUMED mapping from evidence grade to spread "
                       "(Weight-of-Evidence grades are ordinal and carry no variances). Report it with the result.")


class ProjectIn(BaseModel):
    name: str = Field(..., max_length=96)
    cost: float = Field(..., ge=0)
    residual_risk_now: float = Field(..., **U)
    residual_risk_after: float = Field(..., **U)
    group: Optional[str] = Field(None, max_length=96, description="Projects sharing a group are mutually exclusive.")
    population: Optional[float] = Field(None, gt=0)
    eal_now: Optional[float] = None
    eal_after: Optional[float] = None


class OptimizeRequest(BaseModel):
    projects: List[ProjectIn] = Field(..., min_length=1, max_length=500)
    budget: float = Field(..., ge=0)
    objective: Literal["delta_R", "delta_EAL", "delta_equity"] = "delta_R"
    mandatory: List[str] = []
    max_projects: Optional[int] = Field(None, ge=1)


class PatientIn(BaseModel):
    record_id: Optional[str] = Field(None, pattern=ID_PATTERN)
    likelihood: float = Field(..., **U)
    exposure: float = Field(..., **U)
    albi_grade: Optional[Literal[1, 2, 3]] = None
    albumin: Optional[float] = Field(None, gt=0)
    bilirubin: Optional[float] = Field(None, gt=0)
    surveillance: Surveillance
    bclc_if_missed: Bclc
    improved_surveillance: Optional[Surveillance] = None


class HccRequest(BaseModel):
    patients: List[PatientIn] = Field(..., min_length=1, max_length=10_000)
    albumin_unit: Literal["g/L", "g/dL"] = "g/L"
    bilirubin_unit: Literal["umol/L", "mg/dL"] = "umol/L"


class AlbiRequest(BaseModel):
    albumin: float = Field(..., gt=0)
    bilirubin: float = Field(..., gt=0)
    albumin_unit: Literal["g/L", "g/dL"] = "g/L"
    bilirubin_unit: Literal["umol/L", "mg/dL"] = "umol/L"
