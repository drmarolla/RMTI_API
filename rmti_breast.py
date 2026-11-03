# Copyright 2026 Cesar Marolla (Apache-2.0, as the rest of the platform)
"""
rmti_breast.py -- Oncoclastics site SCAFFOLD for female breast cancer (RMTI v2.4.0 conventions).

PROPOSED EXTENSION. Not validated, not part of the published RMTI papers. Research prototype: not a medical device, not for patient-care
decisions. It follows rmti_lung.py but is deliberately THINNER, because the breast-specific pieces have not been written or pre-registered:

    L    5-year invasive breast-cancer risk (fraction) from a VALIDATED tool, rescaled to 0-1 on a log scale between two PLACEHOLDER anchors.
         The tool is never re-implemented here. Any other horizon is refused. The two published 5-year decision cut-points are shown as
         reference markers only; they are not used as anchors.
    E    exposure, entered by the user (information NOT already in the L tool).
    V    entered by the user, or as a count of items that the user has pre-registered. NO V-item list exists in this module (lung has one).
    rho_bio  NOT defined. No breast ladder exists, and lung's ECOG ladder must not be reused (README: add a disease by writing a new module,
         not by reusing another disease's anchors). Leave it at 0 (not scored) until a breast ladder is agreed.
    rho_care screening-pathway delivery (adherence, continuity, access), entered by the user.

It adds NO equation: R, tier and EAL come from core.rmti_core. Rules inherited from v2.3.0: values are assigned, not estimated; the tiers are
fixed and identical for every patient; no measured variable may feed two terms.
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "rmti_engine"))
from core.rmti_core import assess, rank_cohort  # noqa: E402
from dynamic.rmti_dynamic import TrajectoryParams  # noqa: E402
from oncology.rmti_hcc import short_tier  # noqa: E402  (shared label format; thresholds stay in core)

__version__ = "0.1-scaffold"
HORIZON_YEARS = 5
PLACEHOLDER = True
# PLACEHOLDERS: invented only so the arithmetic runs. They are NOT from any study. The fixed tiers depend on them, so pre-register your own
# values before any validation. (Same status as the lung placeholders.)
L_ANCHORS = {"r_lo": 0.005, "r_hi": 0.10}
N_MIN_BREAST, N_MAX_BREAST = 1_000, 20_000_000     # advisory E_log bounds only (same advisory range as lung)
BREAST_PARAMS = TrajectoryParams(y_max=4.0)        # indicator count 0-4; gains are the shared placeholders; the items are still to be pre-registered

# Published reference points for a 5-year risk (markers, NOT anchors). Sources (checked): the FDA-approved threshold for tamoxifen / raloxifene
# risk reduction, a 5-year Gail-model risk of at least 1.67% (the BCPT entry level was 1.66%); and the US Preventive Services Task Force statement that
# women with a 5-year risk of at least 3% are more likely to benefit than be harmed (USPSTF, "Breast Cancer: Medication Use to Reduce Risk").
REFERENCE_POINTS = {"FDA / BCPT chemoprevention-discussion cut-point, 5-year risk": 0.0167,
                    "USPSTF chemoprevention cut-point, 5-year risk": 0.03}

# Validated tools that output a 5-YEAR risk of INVASIVE breast cancer, and the limits their own documentation states.
TOOLS = {
    "BCRAT (NCI Breast Cancer Risk Assessment Tool, Gail model)": {
        "horizons_years": (5, "lifetime"),
        "not_valid_for": "women with a history of breast cancer, DCIS or LCIS; other tools may suit known BRCA1/BRCA2 carriers"},
    "BCSC Breast Cancer Risk Calculator": {
        "horizons_years": (5, 10),
        "not_valid_for": "women younger than 35 or older than 74, or with a previous diagnosis of breast cancer or DCIS"},
    "Other validated tool (declare its variables)": {"horizons_years": (5,), "not_valid_for": "see that tool's own documentation"},
}

# DRAFT wording for review by the clinical team: prompts for discussion, not instructions.
BREAST_TIER_POSTURE = {
    "Tier 1 - Low":      "Routine participation in the population screening programme",
    "Tier 2 - Moderate": "Confirm screening invitation, uptake and recall",
    "Tier 3 - High":     "Review risk assessment and screening intensity with the clinical team",
    "Tier 4 - Severe":   "Structured navigation; specialist (family-history or genetics) review",
    "Tier 5 - Critical": "Immediate, resourced pathway; case management",
}


def l_from_risk(risk, horizon_years=HORIZON_YEARS, r_lo=None, r_hi=None):
    """Rescale a validated tool's 5-year risk (fraction) to L on [0, 1], log scale between r_lo and r_hi (placeholders unless you supply yours).
    Refuses any horizon other than 5 years: converting a 10-year or lifetime risk needs the source model, not an assumption."""
    if horizon_years != HORIZON_YEARS:
        raise ValueError("L is defined on a 5-year horizon; a %s-year risk cannot be entered without a justified conversion" % horizon_years)
    lo = L_ANCHORS["r_lo"] if r_lo is None else r_lo
    hi = L_ANCHORS["r_hi"] if r_hi is None else r_hi
    if not 0.0 <= risk <= 1.0:
        raise ValueError("risk must be a fraction between 0 and 1")
    if not 0.0 < lo < hi <= 1.0:
        raise ValueError("anchors must satisfy 0 < r_lo < r_hi <= 1")
    if risk <= lo:
        return 0.0
    return min(1.0, math.log10(risk / lo) / math.log10(hi / lo))


def reference_markers(r_lo=None, r_hi=None):
    """Where the published cut-points fall on the L scale for the anchors in use."""
    return {k: round(l_from_risk(v, r_lo=r_lo, r_hi=r_hi), 3) for k, v in REFERENCE_POINTS.items()}


def assess_patient(N, L, E, V, rho_now, rho_after=None, C=5):
    """Patient or cohort assessment, breast vocabulary. Wrapper around core.assess()."""
    out = assess(N, L, E, V, rho_now, rho_after, C, n_min=N_MIN_BREAST, n_max=N_MAX_BREAST, postures=BREAST_TIER_POSTURE)
    out["tier_now"] = short_tier(out["R_now"])
    if "R_after" in out:
        out["tier_after"] = short_tier(out["R_after"])
    return out


def rank_cohort_breast(patients):
    """Rank a cohort: tier severity, then EAL, priority reset within each tier (core.rank_cohort)."""
    clean = {}
    for name, kw in patients.items():
        row = dict(kw, n_min=N_MIN_BREAST, n_max=N_MAX_BREAST, postures=BREAST_TIER_POSTURE)
        if "E" in row:
            row["E_sel"] = row.pop("E")
        clean[name] = row
    ranked = rank_cohort(clean)
    for r in ranked:
        r["tier_now"] = short_tier(r["R_now"])
        if "R_after" in r:
            r["tier_after"] = short_tier(r["R_after"])
    return ranked
