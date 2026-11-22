# Copyright 2025-2026 Cesar Marolla
# Licensed under the Apache License, Version 2.0 (see LICENSE).
"""Domain-independent RMTI core.

    Eq. (1)  IR  = L * E_sel * V
    Eq. (2)  R   = IR * (1 - rho)
    Eq. (3/5) multi-hazard, multi-category generalisation
    Eq. (4)  advisory log-normalised exposure E_log
    Eq. (6)  EAL = L * C * (1 - rho)
    Eq. (7)  per-capita equity rate
    Table 3  fixed decision tiers

Scalar functions reproduce the validated reference implementations
(rmti_ssa.py / rmti_core.py) exactly. ``*_array`` functions are vectorised
NumPy equivalents for registry-scale use.
"""
from __future__ import annotations

import math
from decimal import ROUND_HALF_UP, Decimal
from typing import Dict, Iterable, Mapping, Optional

import numpy as np

# --- fixed, pre-registered tables (never re-derived from a sample) ----------
TIER_THRESHOLDS = (0.05, 0.15, 0.35, 0.60)
TIER_LABELS = ("Tier 1 - Low", "Tier 2 - Moderate", "Tier 3 - High",
               "Tier 4 - Severe", "Tier 5 - Critical")
TIER = [(0.05, TIER_LABELS[0]), (0.15, TIER_LABELS[1]), (0.35, TIER_LABELS[2]),
        (0.60, TIER_LABELS[3]), (1e9, TIER_LABELS[4])]       # legacy layout

TIER_NAMES = ("Low", "Moderate", "High", "Severe", "Critical")
TIER_POSTURE = ("Monitor", "Prevent", "Mitigate", "Intervene", "Emergency")      # Table 3
TIER_RANGES = ("R < 0.05", "0.05 <= R < 0.15", "0.15 <= R < 0.35", "0.35 <= R < 0.60", "R >= 0.60")

RHO_TYPOLOGY_ANCHORS = {"none": 0.10, "ad_hoc": 0.20, "monitoring_enforcement": 0.25,
                        "structured": 0.45, "structured_to_funded": 0.55,
                        "funded": 0.58, "optimised": 0.70}
C_INFRA = {1: 0.10, 2: 0.30, 3: 0.50, 4: 0.75, 5: 1.00}      # Table 2
N_MIN, N_MAX = 10, 20_000_000                                 # Sec. 3.3 anchors
CATEGORIES = ("social", "economic", "environmental")


def _unit(name: str, x: float) -> None:
    if not 0.0 <= x <= 1.0:
        raise ValueError(f"{name} must lie in [0, 1]; got {x}")


# --- Eq. (4) ----------------------------------------------------------------
def e_log(N, n_min: Optional[float] = None, n_max: Optional[float] = None):
    """Advisory log-normalised exposure baseline. Works on scalars or arrays.
    Not clipped (as in the reference code); see :func:`e_log_clipped`."""
    lo = N_MIN if n_min is None else n_min
    hi = N_MAX if n_max is None else n_max
    if np.ndim(N) == 0:
        return (math.log10(N) - math.log10(lo)) / (math.log10(hi) - math.log10(lo))
    N = np.asarray(N, dtype=float)
    return (np.log10(N) - math.log10(lo)) / (math.log10(hi) - math.log10(lo))


def e_log_clipped(N, n_min=None, n_max=None):
    """E_log clipped to [0, 1] (what the Excel calculators do)."""
    return np.clip(e_log(N, n_min, n_max), 0.0, 1.0)


# --- Table 3 ----------------------------------------------------------------
def tier(R: float) -> str:
    """Fixed Table 3 tier label for a scalar R."""
    return TIER_LABELS[int(np.searchsorted(TIER_THRESHOLDS, R, side="right"))]


def tier_index(R) -> np.ndarray:
    """Vectorised tier index 0..4 (0 = Tier 1). Boundaries are lower-inclusive:
    R == 0.35 is Tier 4, matching ``0.35 <= R < 0.60``."""
    return np.searchsorted(TIER_THRESHOLDS, np.asarray(R, dtype=float), side="right")


def pct_reduction(rho_now: float, rho_after: float) -> float:
    """Percent cut in R when only rho changes, Excel-style rounding."""
    a, b = Decimal(str(rho_now)), Decimal(str(rho_after))
    pct = (1 - (1 - b) / (1 - a)) * 100
    return float(pct.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


# --- Eq. (1), (2), (6) ------------------------------------------------------
def score(L, E_sel, V, rho, C=5) -> Dict[str, float]:
    """Two-stage computation for one resilience state (display rounding to
    3 dp uses Decimal so 0.0585 -> 0.059 as in Excel; tier uses the float R)."""
    for n, x in (("L", L), ("E_sel", E_sel), ("V", V), ("rho", rho)):
        _unit(n, x)
    if C not in C_INFRA:
        raise ValueError(f"C must be one of {sorted(C_INFRA)}; got {C}")
    R = L * E_sel * V * (1 - rho)
    EAL = L * C_INFRA[C] * (1 - rho)
    q = Decimal("0.001")
    d = [Decimal(str(x)) for x in (L, E_sel, V, rho)]
    IR_d = d[0] * d[1] * d[2]
    R_d = IR_d * (1 - d[3])
    EAL_d = d[0] * Decimal(str(C_INFRA[C])) * (1 - d[3])
    r3 = lambda x: float(x.quantize(q, rounding=ROUND_HALF_UP))
    return {"IR": r3(IR_d), "R": r3(R_d), "tier": tier(R), "EAL": r3(EAL_d),
            "EAL_raw": EAL, "R_raw": R}


def score_array(L, E_sel, V, rho, C=None):
    """Vectorised Eq. (1)/(2)/(6) on arrays; no rounding. Returns dict of arrays."""
    L, E_sel, V, rho = (np.asarray(x, dtype=float) for x in (L, E_sel, V, rho))
    IR = L * E_sel * V
    out = {"IR": IR, "R": IR * (1 - rho), "tier_index": None}
    out["tier_index"] = tier_index(out["R"])
    if C is not None:
        c = np.vectorize(C_INFRA.__getitem__)(np.asarray(C))
        out["EAL"] = L * c * (1 - rho)
    return out


def assess(N, L, E_sel, V, rho_now, rho_after=None, C=5, n_min=None, n_max=None) -> Dict:
    """Asset/patient assessment: baseline + optional post-investment state,
    risk reduction and per-capita equity rate (Eq. 7)."""
    now = score(L, E_sel, V, rho_now, C)
    out = {"N": N, "E_log": round(float(e_log(N, n_min, n_max)), 3), "rho_now": rho_now,
           "IR": now["IR"], "R_now": now["R"], "tier_now": now["tier"],
           "EAL_now": now["EAL"],
           "equity_now_per_1M": round(now["EAL_raw"] / (N / 1e6), 4)}
    if rho_after is not None:
        after = score(L, E_sel, V, rho_after, C)
        out.update({"rho_after": rho_after, "R_after": after["R"],
                    "tier_after": after["tier"], "EAL_after": after["EAL"],
                    "equity_after_per_1M": round(after["EAL_raw"] / (N / 1e6), 4),
                    "risk_reduction_pct": pct_reduction(rho_now, rho_after)})
    return out


def rank_cohort(rows: Mapping[str, Mapping]) -> list:
    """Rank by tier severity, then EAL_now descending (the calculators' 'Priority')."""
    results = []
    for name, kw in rows.items():
        r = assess(**kw)
        r["name"] = name
        results.append(r)
    rank = {lbl: i for i, lbl in enumerate(TIER_LABELS)}
    results.sort(key=lambda r: (-rank[r["tier_now"]], -r["EAL_now"]))
    return results


# --- tier-boundary margins (automates paper Table 8) ------------------------
def boundary_margins(L, E_sel, V, rho) -> Dict[str, float]:
    """How far is this score from flipping tier?

    Returns the nearest lower/upper thresholds, the relative error in any one
    of L, E or V that would cross each (R scales 1:1 with them), and the
    absolute change in rho that would cross each. ``None`` where no such
    boundary exists (below Tier 1 / above Tier 5) or rho would leave [0, 1).
    """
    IR = L * E_sel * V
    R = IR * (1 - rho)
    i = int(tier_index(R))
    lo = TIER_THRESHOLDS[i - 1] if i > 0 else None
    hi = TIER_THRESHOLDS[i] if i < len(TIER_THRESHOLDS) else None

    def rho_for(thr):
        if thr is None or IR <= 0:
            return None
        r = 1 - thr / IR
        return r - rho if 0.0 <= r <= 1.0 else None

    return {"R": R, "tier": TIER_LABELS[i], "lower_threshold": lo, "upper_threshold": hi,
            "rel_change_LEV_to_lower": None if lo is None else lo / R - 1,
            "rel_change_LEV_to_upper": None if hi is None else hi / R - 1,
            "delta_rho_to_lower": rho_for(lo), "delta_rho_to_upper": rho_for(hi)}


# --- Eq. (3)/(5) generalised form -------------------------------------------
def check_weights(weights: Mapping[str, float], categories=CATEGORIES) -> None:
    total = sum(weights.get(c, 0.0) for c in categories)
    if abs(total - 1.0) > 1e-6:
        raise ValueError(f"Category weights must sum to 1 (Table 1, w_c); got {total:.4f}")


def score_multi(hazards: Iterable[Mapping], weights: Mapping[str, float], categories=CATEGORIES) -> Dict:
    """Eq. (3)/(5). NOTE: R may exceed 1 with several severe hazards (paper
    Sec. 3.2); this implementation does not clip and is not field-validated."""
    check_weights(weights, categories)
    R_tot = EAL_tot = 0.0
    breakdown = []
    for h in hazards:
        for c in categories:
            cat = h["categories"][c]
            term = weights[c] * h["L"] * cat["E"] * cat["V"] * (1 - cat["rho"])
            R_tot += term
            breakdown.append({"hazard": h["name"], "category": c, "w_c": weights[c],
                              "L": h["L"], "E": cat["E"], "V": cat["V"], "rho": cat["rho"],
                              "term": round(term, 4)})
        EAL_tot += h["L"] * C_INFRA[h["C"]] * (1 - h["rho_hazard"])
    return {"R": round(R_tot, 3), "tier": tier(R_tot), "EAL": round(EAL_tot, 3),
            "breakdown": breakdown}


def assess_multi(N, hazards, weights, categories=CATEGORIES) -> Dict:
    res = score_multi(hazards, weights, categories)
    res.update({"N": N, "E_log_advisory": round(float(e_log(N)), 3),
                "equity_per_1M": round(res["EAL"] / (N / 1e6), 4)})
    return res
