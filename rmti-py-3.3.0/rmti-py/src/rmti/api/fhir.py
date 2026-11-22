# Copyright 2025-2026 Cesar Marolla. Apache-2.0.
"""Emit HL7 FHIR R4 (4.0.1) ``RiskAssessment`` resources and ``Bundle``s from RMTI results.

Scope: this API PRODUCES RiskAssessment resources from posted inputs. It is NOT a FHIR server (no read/search/
capability statement, no patient store). The residual risk R is an index, not a probability, so it is carried in an
extension and NOT in ``prediction.probabilityDecimal``. The code system and extension URLs are URNs defined by this
project (urn:rmti:...); they are placeholders until a canonical URL is published.
Structure is checked in the test-suite with the ``fhir.resources`` R4B models; the resources have not been run through the
official HL7 validator or any profile.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Iterable, Optional

from .. import __version__
from ..core import TIER_NAMES, TIER_POSTURE

SYSTEM_TIER = "urn:rmti:codesystem:residual-risk-tier"
SYSTEM_ID = "urn:rmti:record-id"
EXT = "urn:rmti:fhir:extension:"
NOTE = ("Residual composite risk index R = L x E x V x (1 - rho). An index, not a probability. "
        "Research prototype; not validated against outcomes; not a medical device.")


def risk_assessment(result: dict, when: Optional[datetime] = None) -> dict:
    """``result`` is an AssessmentResult as a dict."""
    when = when or datetime.now(timezone.utc)
    t = result["tier"]
    rid = result.get("record_id") or "unspecified"
    ra = {
        "resourceType": "RiskAssessment",
        "id": str(uuid.uuid4()),
        "status": "preliminary",
        "method": {"text": "Risk Mechanism Theory Index (RMTI)"},
        "subject": {"identifier": {"system": SYSTEM_ID, "value": rid}},
        "occurrenceDateTime": when.replace(microsecond=0).isoformat(),
        "prediction": [{
            "outcome": {"text": "Residual composite risk tier"},
            "qualitativeRisk": {"coding": [{"system": SYSTEM_TIER, "code": str(t),
                                            "display": f"Tier {t} - {TIER_NAMES[t - 1]}"}]},
            "rationale": f"Decision posture: {TIER_POSTURE[t - 1]}.",
        }],
        "extension": [
            {"url": EXT + "residual-risk", "valueDecimal": result["residual_risk"]},
            {"url": EXT + "inherent-risk", "valueDecimal": result["inherent_risk"]},
            {"url": EXT + "engine-version", "valueString": __version__},
        ],
        "note": [{"text": NOTE}],
    }
    if result.get("domain"):
        ra["extension"].append({"url": EXT + "domain", "valueString": result["domain"]})
    if result.get("expected_annual_loss") is not None:
        ra["extension"].append({"url": EXT + "expected-annual-loss-index", "valueDecimal": result["expected_annual_loss"]})
    if result.get("residual_risk_after") is not None:
        ta = result["tier_after"]
        ra["prediction"].append({
            "outcome": {"text": "Residual composite risk tier after proposed intervention (scenario)"},
            "qualitativeRisk": {"coding": [{"system": SYSTEM_TIER, "code": str(ta),
                                            "display": f"Tier {ta} - {TIER_NAMES[ta - 1]}"}]}})
        ra["extension"].append({"url": EXT + "residual-risk-after-scenario", "valueDecimal": result["residual_risk_after"]})
    return ra


def bundle(resources: Iterable[dict]) -> dict:
    return {"resourceType": "Bundle", "id": str(uuid.uuid4()), "type": "collection",
            "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "entry": [{"fullUrl": "urn:uuid:" + r["id"], "resource": r} for r in resources]}
