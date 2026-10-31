# Copyright 2026 Cesar Marolla
# Licensed under the Apache License, Version 2.0 (see rmti_hcc.py for the full notice).
"""
rmti_hcc_cohort.py -- patient-level RMTI-HCC scoring from routine laboratory data.

Adds NO new equation. It supplies the HCC-specific inputs that rmti_hcc.py leaves to the user, and feeds the unchanged core:

    albumin, bilirubin            -> ALBI score and grade     -> V   (anchors 0.35 / 0.60 / 0.85, rmti_hcc.ALBI_V)
    age, sex, ALBI, platelets     -> aMAP score and group     -> L   (published annual incidence of the group, log-scaled)
    E, rho                        -> programme-level inputs (no patient-level source in a clinic cohort; held fixed and stated)
    R = L * E * V * (1 - rho)     -> core.score(); fixed tiers from core.TIER

Overlap rule (same principle as the lung module): no measured VARIABLE may feed two terms. aMAP contains ALBI, so L = aMAP together
with V = ALBI counts albumin and bilirubin twice. score_cohort() therefore REFUSES that pairing unless allow_overlap=True, in which case
every row is labelled status = "DIAGNOSTIC: overlap (albumin, bilirubin)" and must not be reported as the RMTI result.

The clean default is L tool "aMAP-ref": the published aMAP formula evaluated at a FIXED reference ALBI (ALBI_REF), so that L depends only on
age, sex and platelets and keeps the published scale, cut-offs (50/60) and group incidences. V then uses albumin and bilirubin alone.
Variable sets are disjoint, which is what the rule requires. The inputs stay statistically correlated (age and platelets relate to liver
function), and the group incidences are approximate for ALBI_REF patients, not validated: both are reported, not hidden.

Anchors are assigned, not estimated (see L_ANCHOR_SETS); this module is a research prototype and makes no clinical claim.
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from core.rmti_core import score  # noqa: E402
from oncology.rmti_hcc import ALBI_V, short_tier  # noqa: E402

__version__ = "2.4.0-cohort1"

# ---- Published instruments -------------------------------------------------------------------------------------------------
# ALBI: Johnson PJ et al., J Clin Oncol 2015;33:550-558. Bilirubin in umol/L, albumin in g/L.
ALBI_G1_MAX = -2.60          # grade 1 if ALBI <= -2.60
ALBI_G2_MAX = -1.39          # grade 2 if ALBI <= -1.39, else grade 3

# aMAP: Fan R et al., J Hepatol 2020;73:1368-1378.  aMAP = ((0.06*age + 0.89*male + 0.48*ALBI - 0.01*platelets) + 7.4) / 14.77 * 100
# platelets in 10^9/L, male = 1/0.  Risk groups (cut-offs 50 and 60): low < 50, medium 50-60, high > 60.
AMAP_LOW_BELOW, AMAP_HIGH_ABOVE = 50.0, 60.0

# Reference ALBI for the clean L tool: the grade 1 / grade 2 boundary (a published threshold, not tuned). Sensitivity: ALBI_REF_SENSITIVITY.
ALBI_REF = ALBI_G1_MAX
ALBI_REF_SENSITIVITY = (-2.90, -2.60, -2.30)

# Published annual HCC incidence by aMAP group (Fan 2020, graphical abstract; 5-year follow-up): low 0.0-0.2 %/yr,
# medium 0.4-1.0 %/yr, high 1.6-4.0 %/yr.  The group midpoint is used (assigned, not estimated).
AMAP_GROUP_RANGE = {1: (0.000, 0.002), 2: (0.004, 0.010), 3: (0.016, 0.040)}
AMAP_GROUP_INCIDENCE = {g: (lo + hi) / 2 for g, (lo, hi) in AMAP_GROUP_RANGE.items()}   # 0.1 %, 0.7 %, 2.8 % per year

# ---- Likelihood scale: annual incidence -> L in [0, 1] (log scale; same form as the lung module's l_from_risk) --------------
# Primary anchors are placeholders chosen so that no aMAP group maps to exactly 0; two alternatives are reported as sensitivity.
L_ANCHOR_SETS = {
    "primary": (0.0005, 0.15),      # 0.05 %/yr -> 0 ; 15 %/yr (about the untreated-HBV figure, 12.8 %/yr) -> 1
    "paper_rubric_fit": (0.00704, 0.17739),   # least-squares fit to the L values in the 2026 preprint's Tables 1-2
    "lung_style": (0.001, 0.10),    # the lung module's placeholder anchors
}


def l_from_incidence(annual_incidence: float, anchors=L_ANCHOR_SETS["primary"]) -> float:
    r_lo, r_hi = anchors
    if not 0.0 < r_lo < r_hi:
        raise ValueError("anchors must satisfy 0 < r_lo < r_hi")
    if annual_incidence <= 0:
        return 0.0
    x = (math.log10(annual_incidence) - math.log10(r_lo)) / (math.log10(r_hi) - math.log10(r_lo))
    return min(1.0, max(0.0, x))


# ---- Overlap rule ------------------------------------------------------------------------------------------------------------
L_TOOLS = ("aMAP-ref", "aMAP")
HCC_L_TOOL_VARIABLES = {
    "aMAP-ref": ["age", "sex", "platelets"],                       # clean: ALBI fixed at ALBI_REF, so albumin and bilirubin do not enter
    "aMAP": ["age", "sex", "albumin", "bilirubin", "platelets"],
    "FIB-4": ["age", "ast", "alt", "platelets"],
}
V_INSTRUMENT_VARIABLES = {
    "ALBI": ["albumin", "bilirubin"],
}


def overlap(l_tool: str, v_instrument: str) -> list:
    """Variables used by both the L tool and the V instrument (empty list = clean)."""
    return sorted(set(HCC_L_TOOL_VARIABLES[l_tool]) & set(V_INSTRUMENT_VARIABLES[v_instrument]))


# ---- Instruments (vectorised, accept scalars or arrays/Series) -------------------------------------------------------------
def albi_score(bilirubin_umol_l, albumin_g_l):
    return np.log10(bilirubin_umol_l) * 0.66 + np.asarray(albumin_g_l, dtype=float) * (-0.085)


def albi_grade(albi):
    a = np.asarray(albi, dtype=float)
    return np.where(a <= ALBI_G1_MAX, 1, np.where(a <= ALBI_G2_MAX, 2, 3))


def amap_score(age_years, male, albi, platelets_1e9_l):
    return ((0.06 * np.asarray(age_years, dtype=float) + 0.89 * np.asarray(male, dtype=float) + 0.48 * np.asarray(albi, dtype=float)
             - 0.01 * np.asarray(platelets_1e9_l, dtype=float)) + 7.4) / 14.77 * 100.0


def amap_ref_score(age_years, male, platelets_1e9_l, albi_ref=ALBI_REF):
    """aMAP evaluated at a fixed ALBI: depends on age, sex and platelets only. Same scale and cut-offs as aMAP."""
    return amap_score(age_years, male, albi_ref, platelets_1e9_l)


def amap_group(amap):
    a = np.asarray(amap, dtype=float)
    return np.where(a < AMAP_LOW_BELOW, 1, np.where(a <= AMAP_HIGH_ABOVE, 2, 3))


# ---- Cohort scoring ----------------------------------------------------------------------------------------------------------
REQUIRED = ["age_years", "male", "albumin_g_l", "bilirubin_umol_l", "platelets_1e9_l"]


def status_of(l_tool: str, v_instrument: str) -> str:
    clash = overlap(l_tool, v_instrument)
    return "CLEAN: L and V use disjoint variables" if not clash else "DIAGNOSTIC: overlap (%s)" % ", ".join(clash)


def score_cohort(df: pd.DataFrame, *, l_tool: str = "aMAP-ref", v_instrument: str = "ALBI", E: float = 0.60, rho: float = 0.20,
                 rho_after: float | None = None, C: int = 5, l_anchors=L_ANCHOR_SETS["primary"], albi_ref: float = ALBI_REF,
                 group_incidence: dict | None = None, allow_overlap: bool = False) -> pd.DataFrame:
    """Score every row. Input columns: age_years, male (0/1), albumin_g_l, bilirubin_umol_l, platelets_1e9_l (10^9/L).
    l_tool "aMAP-ref" (default, clean) or "aMAP" (overlaps ALBI; refused unless allow_overlap=True).
    group_incidence: optional {1,2,3: annual incidence} to replace the published midpoints (e.g. cross-fitted estimates).
    C is the consequence INDEX 1..5 (default 5 = worst case); EAL uses the ladder value rmti_core.C_INFRA[C], not the index.
    Returns a copy with albi, albi_grade, amap, amap_ref, amap_group, annual_incidence, L, V, R_raw, R, tier, EAL, status
    (and R_after, tier_after when rho_after is given). Tiers use unrounded R and the fixed rule R < 0.05 Low, lower bound to the higher tier."""
    if l_tool not in L_TOOLS:
        raise ValueError("l_tool must be one of %s" % (L_TOOLS,))
    clash = overlap(l_tool, v_instrument)
    if clash and not allow_overlap:
        raise ValueError("REFUSED: L tool %s and V instrument %s both use %s, so these would be counted twice. Use l_tool='aMAP-ref', or pass "
                         "allow_overlap=True only to quantify the double counting; outputs are then labelled DIAGNOSTIC." % (l_tool, v_instrument, clash))
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError("missing columns: %s" % missing)
    gi = group_incidence or AMAP_GROUP_INCIDENCE
    out = df.copy()
    out["albi"] = albi_score(out["bilirubin_umol_l"], out["albumin_g_l"])
    out["albi_grade"] = albi_grade(out["albi"])
    out["amap"] = amap_score(out["age_years"], out["male"], out["albi"], out["platelets_1e9_l"])
    out["amap_ref"] = amap_ref_score(out["age_years"], out["male"], out["platelets_1e9_l"], albi_ref)
    out["amap_group"] = amap_group(out["amap"] if l_tool == "aMAP" else out["amap_ref"])
    out["annual_incidence"] = out["amap_group"].map(gi)
    out["L"] = out["annual_incidence"].map(lambda r: l_from_incidence(r, l_anchors))
    out["V"] = out["albi_grade"].map(ALBI_V)
    res = [score(float(L), E, float(V), rho, C) for L, V in zip(out["L"], out["V"])]
    out["R_raw"] = [r["R_raw"] for r in res]
    out["R"] = [r["R"] for r in res]
    out["tier"] = [short_tier(r["R_raw"]) for r in res]
    out["EAL"] = [r["EAL"] for r in res]
    if rho_after is not None:
        aft = [score(float(L), E, float(V), rho_after, C) for L, V in zip(out["L"], out["V"])]
        out["R_after"] = [r["R"] for r in aft]
        out["tier_after"] = [short_tier(r["R_raw"]) for r in aft]
    out["status"] = status_of(l_tool, v_instrument)
    out["overlap_flag"] = bool(clash)
    return out
