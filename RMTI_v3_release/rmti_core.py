"""RMTI scoring core, shared by the REST API (api.py), the Streamlit portal and the SDK.

R = L * E * V * (1 - rho)

IMPORTANT: compute_core() is the single place where the math lives. If you want the API to
call the vendored rmti_engine (v2.4.0) instead, change ONLY that function.
Tier bands below are default screening bands, not clinically validated cut-offs.
"""
from __future__ import annotations

APP_TITLE = "Risk Mechanism Theory Index (RMTI)"
APP_SHORT = "RMTI"
ENGINE_VERSION = "2.4.0"
API_VERSION = "1.0.0"
FORMULA = "R = L * E * V * (1 - rho)"
DISCLAIMER = (
    "Research prototype. Not validated, not a medical device, and not for patient-care "
    "or emergency decisions. Do not send patient-identifying information."
)
LEVER_NAMES = {"L": "Likelihood", "E": "Exposure", "V": "Vulnerability", "rho": "Resilience"}
SITES = ("general", "liver", "lung", "breast")
TIER_CUTS = ((0.10, "low"), (0.30, "moderate"), (0.55, "high"))  # else "critical"
SANDBOX_KEY = "rmti_sandbox_demo"

# tier -> (requests per minute, max items per batch)
ACCESS_TIERS = {
    "sandbox": {"rpm": 20, "batch": 25, "description": "Public demo key. Shared, low limits."},
    "research": {"rpm": 120, "batch": 250, "description": "Academic and research use."},
    "enterprise": {"rpm": 600, "batch": 1000, "description": "Hospital systems and integrators."},
}


def compute_core(L: float, E: float, V: float, rho: float) -> float:
    return L * E * V * (1.0 - rho)


def classify(r: float) -> str:
    for cut, name in TIER_CUTS:
        if r < cut:
            return name
    return "critical"


def _improve(lever: str, value: float, step: float) -> float:
    return min(1.0, value + step) if lever == "rho" else max(0.0, value - step)


def score(L: float, E: float, V: float, rho: float, step: float = 0.10) -> dict:
    inputs = {"L": L, "E": E, "V": V, "rho": rho}
    r = compute_core(**inputs)
    elasticity = {
        "L": 1.0, "E": 1.0, "V": 1.0,
        "rho": None if rho >= 1.0 else round(-rho / (1.0 - rho), 6),
    }
    what_if = []
    for lever, val in inputs.items():
        new_val = _improve(lever, val, step)
        new_r = compute_core(**{**inputs, lever: new_val})
        drop = r - new_r
        what_if.append({
            "lever": lever,
            "name": LEVER_NAMES[lever],
            "from": round(val, 6),
            "to": round(new_val, 6),
            "new_risk": round(new_r, 6),
            "absolute_reduction": round(drop, 6),
            "relative_reduction": round(drop / r, 6) if r > 0 else 0.0,
        })
    what_if.sort(key=lambda w: w["absolute_reduction"], reverse=True)
    priority = what_if[0]["lever"] if what_if and what_if[0]["absolute_reduction"] > 0 else None
    return {
        "risk": round(r, 6),
        "tier": classify(r),
        "inputs": inputs,
        "elasticity": elasticity,
        "what_if": what_if,
        "priority_lever": priority,
        "engine_version": ENGINE_VERSION,
        "disclaimer": DISCLAIMER,
    }


def sweep(lever: str, base: dict, steps: int = 21) -> list[dict]:
    out = []
    for i in range(steps):
        x = i / (steps - 1)
        r = compute_core(**{**base, lever: x})
        out.append({"value": round(x, 6), "risk": round(r, 6), "tier": classify(r)})
    return out


def to_fhir_risk_assessment(result: dict, site: str = "general", label: str | None = None) -> dict:
    """FHIR R4-shaped RiskAssessment. No subject is attached on purpose (no PHI)."""
    hl7 = {"low": "low", "moderate": "moderate", "high": "high", "critical": "high"}[result["tier"]]
    res = {
        "resourceType": "RiskAssessment",
        "status": "final",
        "method": {"text": f"RMTI engine v{result['engine_version']}: {FORMULA}"},
        "code": {"text": f"RMTI systemic risk ({site})"},
        "prediction": [{
            "outcome": {"text": f"RMTI tier: {result['tier']}"},
            "qualitativeRisk": {"coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/risk-probability",
                "code": hl7,
            }]},
            "rationale": (
                f"R={result['risk']}; L={result['inputs']['L']}, E={result['inputs']['E']}, "
                f"V={result['inputs']['V']}, rho={result['inputs']['rho']}; "
                f"priority lever: {result['priority_lever']}"
            ),
        }],
        "note": [{"text": DISCLAIMER}],
    }
    if label:
        res["identifier"] = [{"value": label}]
    return res
