# Copyright 2026 Cesar Marolla
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
rmti_lung.py -- Oncoclastics site module for lung cancer (RMTI v2.4.0).

PROPOSED EXTENSION. Not validated against outcomes and not part of the published
RMTI papers. Research prototype: not a medical device, not for patient-care
decisions. Every default comes from a peer-reviewed source (lung_evidence.py);
unpublished manuscript figures are deliberately absent.

Oncoclastics (RMTI v2.3.0, oncoclastics/TERMINOLOGY_NOTE.md) applies the
hazard-exposure-vulnerability-resilience structure to cancer-related
trajectories in two named senses, biological (L, E, V, rho_bio) and
care-system (rho_care). This module supplies the lung-cancer reading of each
term. It adds NO equation: R, tier and EAL come from core.rmti_core, the
trajectory from dynamic.rmti_dynamic, and the two-sense combination from
oncoclastics/rmti_oncoclastics.py (rho_bio ladder levels are the same five
numbers, 0.10 to 0.70, as ladder A; ladder B (v2.4 draft) is shaped to Kawaguchi 2010 and runs 0.16 to 0.80. Only the descriptors are lung-specific).

    L    5-year lung-cancer risk from a VALIDATED tool, rescaled to 0-1 on a
         log scale between two placeholder anchors. We never re-implement the
         tool. A 2-year risk (e.g. the UK Biobank model) must not be entered.
    E    cumulative exposure burden (magnitude, duration, frequency) built
         from information NOT already in L.
    V    accumulated cost of prior injury (allostatic load): count of the
         items in V_ITEMS, none of which may already be in L (overlap check).
    rho_bio  biological reserve, ladder anchored to ECOG performance status
         (RHO_BIO_LUNG). PROVISIONAL: see its limitations.
    rho_care screening-pathway delivery (adherence, continuity, access).
    C    ordinal severity if the outcome occurs (LUNG_C_LADDER, placeholder).

Rules inherited from v2.3.0: values are assigned, not estimated; the tiers are
fixed and identical for every patient; no measure may feed two terms.
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from core.rmti_core import assess, rank_cohort  # noqa: E402
from dynamic.rmti_dynamic import TrajectoryParams  # noqa: E402
from oncology.rmti_hcc import short_tier  # noqa: E402  (shared label format; thresholds stay in core)
from oncology.lung_evidence import V_ITEMS, L_TOOL_VARIABLES, _load  # noqa: E402

__version__ = "2.4.0"

N_MIN_LUNG, N_MAX_LUNG = 1_000, 20_000_000     # advisory E_log bounds only
HORIZON_YEARS = 5                               # L is a 5-year risk
_PARAMS = _load("lung_parameters.json")         # registry/lung_parameters.json: versioned; locked=true after pre-registration
REGISTRY_VERSION = _PARAMS["registry_version"]
PARAMS_LOCKED = bool(_PARAMS["locked"])
L_ANCHORS = dict(_PARAMS["L_anchors"])          # PLACEHOLDERS: the fixed tiers depend on them; pre-register before validation

LUNG_PARAMS = TrajectoryParams(y_max=float(len(V_ITEMS)))   # V indicator = count of V_ITEMS (0..4); gains are the shared placeholders

LUNG_TIER_POSTURE = {
    "Tier 1 - Low":      "Routine primary-care review; screening only if eligibility criteria are met",
    "Tier 2 - Moderate": "Confirm screening eligibility, invitation and uptake",
    "Tier 3 - High":     "Prioritise for the screening pathway; review modifiable barriers with the clinical team",
    "Tier 4 - Severe":   "Structured navigation; early multidisciplinary review",
    "Tier 5 - Critical": "Immediate, resourced pathway; case management",
}

# Consequence C: stage at which a missed cancer would be found, mapped to the Table 2 integer index (core.C_INFRA).
# Ordinal placeholder. Nguyen 2025 supports only the ordering IIIA < IIIB < IIIC within stage III.
LUNG_C_LADDER = {"pre_invasive": 1, "stage_I": 2, "stage_II": 3, "stage_III": 4, "stage_IV": 5}

# ---- rho_bio, lung ladder (PROVISIONAL; consensus/Delphi still to do) -----------------------------------------------
# Same five numeric levels as oncoclastics.RHO_BIO_ANCHORS, anchored to the standard ECOG performance-status scale
# (Oken et al., Am J Clin Oncol 1982): a global measure of functional reserve.
# Limitations (carry them into any use):
#  1. ECOG partly reflects disease already counted in V (e.g. COPD). Do not score ECOG and a V item that is a component of it.
#  2. In a screening population nearly everyone is ECOG 0-1, so the ladder saturates; a discriminating measure not in L is needed.
#  3. Nguyen 2025 supports only the split PS <2 v >=2. Kawaguchi 2010 (26,957 NSCLC, adjusted HR 1.29/2.04/2.94/4.18) orders and separates all five WHO PS levels; Jang 2014 agrees (mixed cancers); Lee 2024 pools ECOG 3-4.
#     Per-step evidence grades are in RHO_BIO_LUNG_EVIDENCE. Ordering is supported; step sizes are not calibrated, and the ladder compresses the poor end (see registry ladder-check).
def _ladder(rows):
    return [(r["value"], r["label"], r["ecog"], r["descriptor"]) for r in rows]


ACTIVE_LADDER = _PARAMS.get("active_ladder", "A")
RHO_BIO_LUNG_LADDERS = {ACTIVE_LADDER: _ladder(_PARAMS["rho_bio_ladder"])}                 # every ladder is available by name,
RHO_BIO_LUNG_CEILINGS = {ACTIVE_LADDER: float(_PARAMS.get("rho_bio_ceiling", 0.70))}       # so validation can run A and B side by side
for _name, _alt in _PARAMS.get("ladder_alternatives", {}).items():
    RHO_BIO_LUNG_LADDERS[_name] = _ladder(_alt["ladder"])
    RHO_BIO_LUNG_CEILINGS[_name] = float(_alt["ceiling"])
RHO_BIO_LUNG = RHO_BIO_LUNG_LADDERS[ACTIVE_LADDER]                                        # the active ladder (registry active_ladder)
RHO_BIO_LUNG_CEILING = RHO_BIO_LUNG_CEILINGS[ACTIVE_LADDER]                               # top anchor; the sandbox slider stops here
RHO_BIO_LUNG_EVIDENCE = {r["value"]: r["evidence"] for r in _PARAMS["rho_bio_ladder"]}   # per-step evidence grade (reviewer-assigned)
RHO_BIO_LUNG_ANCHORS = [a[0] for a in RHO_BIO_LUNG]
RHO_BIO_LUNG_DESCRIPTORS = {a[0]: a[3] for a in RHO_BIO_LUNG}
_ECOG_TO_RHO = {a[2]: a[0] for a in RHO_BIO_LUNG}


def rho_bio_from_ecog(ecog, ladder=None):
    """ECOG performance status (0-4) -> provisional rho_bio level on the active ladder, or on ladder 'A' / 'B' if named.
    Advisory reference point, not a lookup of truth."""
    name = ladder or ACTIVE_LADDER
    if name not in RHO_BIO_LUNG_LADDERS:
        raise ValueError("unknown ladder %r; use one of %s" % (name, sorted(RHO_BIO_LUNG_LADDERS)))
    table = {a[2]: a[0] for a in RHO_BIO_LUNG_LADDERS[name]}
    if ecog not in table:
        raise ValueError("ECOG performance status must be an integer from 0 to 4")
    return table[ecog]


# ---- L, V helpers ---------------------------------------------------------------------------------------------------
def l_from_risk(risk, horizon_years=HORIZON_YEARS, r_lo=None, r_hi=None):
    """Rescale a validated tool's 5-year risk (fraction) to L on [0, 1], log scale between r_lo and r_hi.
    Refuses any horizon other than 5 years: converting 2-year to 5-year risk needs the source model, not an assumption."""
    if horizon_years != HORIZON_YEARS:
        raise ValueError("L is defined on a 5-year horizon; %s-year risk cannot be entered without a justified conversion"
                         % horizon_years)
    lo = L_ANCHORS["r_lo"] if r_lo is None else r_lo
    hi = L_ANCHORS["r_hi"] if r_hi is None else r_hi
    if not 0.0 <= risk <= 1.0:
        raise ValueError("risk must be a fraction between 0 and 1")
    if not 0.0 < lo < hi <= 1.0:
        raise ValueError("anchors must satisfy 0 < r_lo < r_hi <= 1")
    if risk <= lo:
        return 0.0
    return min(1.0, math.log10(risk / lo) / math.log10(hi / lo))


def overlap(l_tool_variables, items=None):
    """Labels of V items whose variable the chosen L tool already contains (they must not be reused)."""
    taken = set(l_tool_variables)
    return [i["label"] for i in (V_ITEMS if items is None else items) if i["variable"] in taken]


def v_indicator(ticked_labels, l_tool_variables):
    """Count of V items present, refusing any item already contained in the L tool."""
    clash = [lab for lab in ticked_labels if lab in overlap(l_tool_variables)]
    if clash:
        raise ValueError("already contained in the L tool, so not usable for V: " + "; ".join(clash))
    return len(ticked_labels)


def v_from_indicator(y, params=LUNG_PARAMS):
    """Snapshot V from the indicator count, with the same mapping the trajectory uses (filter off):
    V = v_lo + (v_hi - v_lo) * clip(y, 0, y_max) / y_max. v_lo and v_hi are inherited placeholders (no lung anchor exists)."""
    y = max(0.0, min(params.y_max, float(y)))
    return params.v_lo + (params.v_hi - params.v_lo) * y / params.y_max


# ---- scoring wrappers (thin; no new equations) ----------------------------------------------------------------------
def assess_patient(N, L, E, V, rho_now, rho_after=None, C=5):
    """Patient or cohort assessment, lung vocabulary. Wrapper around core.assess()."""
    out = assess(N, L, E, V, rho_now, rho_after, C, n_min=N_MIN_LUNG, n_max=N_MAX_LUNG, postures=LUNG_TIER_POSTURE)
    out["tier_now"] = short_tier(out["R_now"])
    if "R_after" in out:
        out["tier_after"] = short_tier(out["R_after"])
    return out


def rank_cohort_lung(patients):
    """Rank a cohort: tier severity, then EAL, priority reset within each tier (core.rank_cohort)."""
    clean = {}
    for name, kw in patients.items():
        row = dict(kw, n_min=N_MIN_LUNG, n_max=N_MAX_LUNG, postures=LUNG_TIER_POSTURE)
        if "E" in row:
            row["E_sel"] = row.pop("E")
        clean[name] = row
    ranked = rank_cohort(clean)
    for r in ranked:
        r["tier_now"] = short_tier(r["R_now"])
        if "R_after" in r:
            r["tier_after"] = short_tier(r["R_after"])
    return ranked


# ---- risk versus treatment and prognosis (RTP): a METHOD; anchors must be supplied by the user ----------------------
def _interp(points, x):
    pts = sorted(points)
    if x < pts[0][0] - 1e-12 or x > pts[-1][0] + 1e-12:
        return None                                   # never extrapolate beyond the anchors
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 - 1e-12 <= x <= x1 + 1e-12:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return pts[-1][1]


def rtp_point(risk, anchors, ref_risk=None):
    """Illustrative arithmetic: occurrence risk x P(resection | early detection) x survival, against a 'risk
    magnification' reference that holds the downstream terms at their value at ref_risk. NOT a benefit estimate
    (ignores stage shift, lead time, overdiagnosis, harms). `anchors` = {"p_resection": [(risk, value), ...],
    "s5_resection": [...]}; this module ships none, so no unpublished figure can leak into a release."""
    p, s = _interp(anchors["p_resection"], risk), _interp(anchors["s5_resection"], risk)
    if p is None or s is None:
        return None
    ref = min(x for x, _ in anchors["p_resection"]) if ref_risk is None else ref_risk
    p0, s0 = _interp(anchors["p_resection"], ref), _interp(anchors["s5_resection"], ref)
    idx, lin = risk * p * s, risk * p0 * s0
    return {"risk": risk, "p_resection": p, "s5_resection": s, "index": idx,
            "linear_reference": lin, "ratio_to_linear": idx / lin if lin else None}
