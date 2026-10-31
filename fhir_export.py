"""FHIR R4 RiskAssessment export (research use only).

Why it is built this way:
- status is always 'preliminary': the RMTI score is an unvalidated research prototype, never 'final'.
- R is a relative, rubric-based score on a fixed tier scale, NOT a probability, so prediction.probabilityDecimal is never used.
  The tier goes in qualitativeRisk (a local code system); R goes in a clearly named extension.
- subject carries only a pseudonymous display label (no identifier, no Patient reference): the label is checked for emails,
  phone and ID-like numbers. The platform does not store identifiable data.
- posture text is a 'framework reading for discussion by a clinical team', placed in note, never in mitigation.
Structural checks only (no network, no official FHIR validator was run): validate with the HL7 validator before any exchange.
"""
import datetime
import re

BASE = "https://github.com/drmarolla/RMTI-time-indexed"
CS_TIER = BASE + "/CodeSystem/rmti-tier"
CS_TAG = BASE + "/CodeSystem/rmti-status"
EXT_R = BASE + "/StructureDefinition/rmti-residual-score"
EXT_IN = BASE + "/StructureDefinition/rmti-inputs"
DISCLAIMER = ("RMTI research prototype: not validated, not a medical device, not for patient-care decisions. "
              "The score is a relative rubric-based index, not a probability.")
_BAD = [re.compile(p) for p in (r"[\w.+-]+@[\w-]+\.[\w.]+", r"\b\d{3}-\d{2}-\d{4}\b", r"\b\d{3}[-. ]\d{3}[-. ]\d{4}\b")]


def _tier_code(tier):
    m = re.search(r"(\d)", tier or "")
    if not m:
        raise ValueError("tier label has no tier number")
    return "tier-" + m.group(1)


def risk_assessment(label, result, inputs, domain="oncoclastics", site=None, version="2.4.0", when=None):
    """result: dict from service.snapshot / two_sense_snapshot (needs R_now or R_raw, tier_now or tier, posture_now optional).
    inputs: dict of the values used (L, E, V, rho_bio, rho_care, C, ...). Returns a FHIR R4 RiskAssessment as a dict."""
    label = (label or "").strip()
    if not label:
        raise ValueError("a pseudonymous label is required (a study code, not a name)")
    if any(p.search(label) for p in _BAD):
        raise ValueError("label looks like an email, phone or ID number: use a pseudonymous study code")
    R = result.get("R_now", result.get("R_raw", result.get("R")))
    tier = result.get("tier_now", result.get("tier"))
    if R is None or tier is None:
        raise ValueError("result has no R or tier")
    when = when or datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    ext_inputs = [{"url": k, "valueDecimal": float(v)} for k, v in inputs.items() if isinstance(v, (int, float)) and not isinstance(v, bool)]
    senses = ("Oncoclastics: biological sense (L, E, V, rho_bio) and care-system sense (rho_care). " if domain == "oncoclastics" else "")
    note = DISCLAIMER + " " + senses + "Posture, if any, is a framework reading for discussion by a clinical team, not a recommendation."
    if result.get("posture_now"):
        note += " Framework reading: " + result["posture_now"] + "."
    return {
        "resourceType": "RiskAssessment",
        "meta": {"tag": [{"system": CS_TAG, "code": "research-prototype", "display": "Research prototype, not validated"}]},
        "extension": [{"url": EXT_IN, "extension": ext_inputs}],
        "status": "preliminary",
        "method": {"text": "RMTI v%s (Risk Mechanism Theory Index), R = L·E·V·(1−rho)%s" % (version, (", site module " + site) if site else "")},
        "subject": {"display": label},
        "occurrenceDateTime": when,
        "prediction": [{
            "outcome": {"text": "Residual risk tier on the fixed five-tier RMTI scale (relative index, not a probability)"},
            "qualitativeRisk": {"coding": [{"system": CS_TIER, "code": _tier_code(tier), "display": str(tier)}], "text": str(tier)},
            "extension": [{"url": EXT_R, "valueDecimal": float(R)}],
        }],
        "note": [{"text": note}],
    }


def structural_problems(ra):
    """Minimal structural checks of the R4 RiskAssessment rules this export relies on. Not a substitute for the HL7 validator."""
    p = []
    if ra.get("resourceType") != "RiskAssessment":
        p.append("resourceType")
    if ra.get("status") not in ("registered", "preliminary", "final", "amended", "corrected", "cancelled", "entered-in-error", "unknown"):
        p.append("status not in R4 value set")
    if ra.get("status") != "preliminary":
        p.append("research export must stay preliminary")
    if not ra.get("subject"):
        p.append("subject is required (1..1)")
    if "identifier" in (ra.get("subject") or {}) or "reference" in (ra.get("subject") or {}):
        p.append("subject must carry only a pseudonymous display")
    for pr in ra.get("prediction", []):
        if "probabilityDecimal" in pr or "probabilityRange" in pr:
            p.append("score must not be exported as a probability")
        if "qualitativeRisk" not in pr:
            p.append("prediction needs qualitativeRisk")
    if "mitigation" in ra:
        p.append("posture must not be exported as mitigation")
    if not ra.get("note"):
        p.append("note with disclaimer required")
    return p
