# Copyright 2026 Cesar Marolla
# Licensed under the Apache License, Version 2.0 (see the LICENSE file in this repository).
"""
rmti_stage34.py -- Stage 2-4 oncology ADAPTER for RMTI (research prototype; not a medical device).

CORE INVARIANTS PRESERVED BY CONSTRUCTION (each is enforced by test_invariants_stage34.py):
  I1  core.rmti_core is imported unmodified (hash-locked); this module defines no score/tier/assess/EAL/e_log functions
      and no tier or consequence tables. Every R, tier, EAL, equity rate and % reduction comes from core.assess().
  I2  Eq. 1-2 are unchanged. Zero effect (hr_eff = 1, psi = 1, no excess harm) gives rho_after == rho_now,
      R_after == R_now, 0.0% reduction.
  I3  Terms stay bounded: rho_after in [0, rho_ceiling]; therapy acts ONLY through (1 - rho), as one more
      multiplicative factor, so every elasticity in rmti_elasticity.py still holds.
  I4  Fixed tiers: tier labels come from core.TIER; nothing here defines or tunes a threshold.
  I5  No double counting: Stage 4 modifiers are predictive-only (they modify the treatment effect, never baseline risk), may not
      use any variable already in L, E or V (declared in OVERLAP_BLOCKLIST), and are applied only if the registry grades the
      interaction evidence moderate or strong; otherwise psi = 1.
  I6  Values are assigned, not estimated: the harm weight is a fixed, pre-registered input; ranges are swept, not fitted.
  I7  Evidence-gated: patients outside a trial's eligibility get NO estimate for that regimen.
  I8  Honest abstention: if the uncertainty intervals of the top two regimens overlap, the output is 'no preferred therapy'.

Design choice (what the paper must defend): time-varying effects are summarised for the R layer by ONE scalar per horizon,
the ratio of cumulative hazards  hr_eff(h) = H_trt(h) / H_ctrl(h)  (= HR exactly when hazards are proportional).
Interval-wise hazard ratios are diagnostics only: they are unstable where the reconstructed curves are flat.
"""
import math
import os
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from core.rmti_core import assess  # noqa: E402  (the only core function this module calls)

__version__ = "0.1.0"
RHO_CEILING = 0.95
GRADES_APPLIED = ("moderate", "strong")
# Variables already inside L (aMAP/ALBI-based), E or V in the HCC module: Stage 3-4 may not reuse them.
OVERLAP_BLOCKLIST = frozenset({"age", "sex", "albumin", "bilirubin", "platelets", "albi", "albi_grade", "child_pugh",
                               "amap", "ast", "alt", "incidence"})


# ---- reconstructed-curve summaries -------------------------------------------------------------------------------
def _H(s):
    return -np.log(np.clip(np.asarray(s, float), 1e-9, 1.0))


def cumulative_hr(months, s_trt, s_ctrl, horizon):
    """hr_eff(h) = H_trt(h) / H_ctrl(h) from monthly survival arrays (reconstructed or published)."""
    h_c = float(np.interp(horizon, months, _H(s_ctrl)))
    h_t = float(np.interp(horizon, months, _H(s_trt)))
    if h_c <= 0:
        raise ValueError("comparator cumulative hazard is zero at the horizon; no effect can be summarised")
    return h_t / h_c


def interval_hr_diagnostic(months, s_trt, s_ctrl, window=6):
    """Windowed hazard ratio (non-overlapping windows) for DIAGNOSIS of non-proportional hazards; never fed to rho."""
    out = []
    m = np.asarray(months, float)
    Ht, Hc = _H(s_trt), _H(s_ctrl)
    for a in np.arange(m[0], m[-1] - window + 1e-9, window):
        dt = np.interp(a + window, m, Ht) - np.interp(a, m, Ht)
        dc = np.interp(a + window, m, Hc) - np.interp(a, m, Hc)
        out.append((float(a), float(a + window), float(dt / dc) if dc > 1e-9 else float("nan")))
    return out


# ---- trial evidence --------------------------------------------------------------------------------------------
@dataclass
class TrialEvidence:
    id: str
    regimen: str
    comparator: str
    months: np.ndarray
    s_trt: np.ndarray
    s_ctrl: np.ndarray
    hr_ci_ratio: Tuple[float, float] = (1.0, 1.0)   # (lo/hr, hi/hr) from the published HR interval; widened by bootstrap in real analyses
    ae_excess: float = 0.0                           # grade 3-4 treatment-related AE proportion, treatment minus comparator
    eligibility: Optional[Dict[str, object]] = None  # None = not yet extracted from full text
    verified: str = "abstract"                       # registry rule: 'full_text' before use outside a sandbox
    source: str = ""
    data_cutoff: str = ""                            # data cut-off of the reported curves/landmarks (results change between analyses)


def gate(trial, patient):
    """I7. Returns (status, reasons): 'eligible', 'outside_evidence' or 'unknown'."""
    r = trial.eligibility
    if r is None:
        return "unknown", ["eligibility not yet extracted from the full text"]
    why = []
    if patient.get("child_pugh") not in r.get("allowed_child_pugh", ["A"]):
        why.append("Child-Pugh %s not enrolled" % patient.get("child_pugh"))
    if patient.get("ecog") not in r.get("allowed_ecog", [0, 1]):
        why.append("ECOG %s not enrolled" % patient.get("ecog"))
    if r.get("excludes_main_pvtt") and patient.get("main_pvtt", False):
        why.append("main portal vein thrombosis excluded")
    if r.get("requires_egd_clearance") and not patient.get("egd_cleared", False):
        why.append("pre-treatment variceal assessment required")
    if r.get("excludes_hbv_hcv_coinfection") and patient.get("hbv_hcv_coinfected", False):
        why.append("HBV/HCV or HBV/HDV co-infection excluded")
    if r.get("excludes_autoimmune") and patient.get("autoimmune", False):
        why.append("autoimmune disease excluded")
    return ("outside_evidence", why) if why else ("eligible", [])


# ---- Stage 4 modifier (predictive-only) -------------------------------------------------------------------------
@dataclass
class PsiModifier:
    """log psi = sum_j gamma_j * z_j over modifiers with moderate/strong registry grade. Default: no modifiers, psi = 1.
    weights: {regimen_id: {variable_name: (gamma, grade)}}. A modifier changes the TREATMENT effect only."""
    weights: Dict[str, Dict[str, Tuple[float, str]]] = field(default_factory=dict)
    extra_blocklist: frozenset = frozenset()          # e.g. set(expand_inputs("CLIP")): everything the chosen L source already uses

    def __post_init__(self):
        block = OVERLAP_BLOCKLIST | {x.lower() for x in self.extra_blocklist}
        for reg, d in self.weights.items():
            bad = [v for v in d if v.lower() in block]
            if bad:
                raise ValueError("%s: variables already in L/E/V cannot be Stage 4 modifiers: %s" % (reg, ", ".join(bad)))

    def psi(self, regimen_id, z=None):
        if not z or regimen_id not in self.weights:
            return 1.0
        s = 0.0
        for name, val in z.items():
            if name in self.weights[regimen_id]:
                gamma, grade = self.weights[regimen_id][name]
                if grade in GRADES_APPLIED:
                    s += gamma * val
        return math.exp(s)


def tipping_psi(a_interval, b_interval):
    """Smallest multiplicative modifier on regimen A's unprotected fraction that would make A's WORST case better than B's BEST
    case (R is proportional to the unprotected fraction). Intervals are (lo, hi) of R_after. Returns None if already separated
    in favour of A. A tipping-point analysis replaces choosing gamma to break a tie."""
    a_lo, a_hi = a_interval; b_lo, b_hi = b_interval
    if a_hi < b_lo:
        return None
    return b_lo / a_hi if a_hi > 0 else None


# ---- the bridge to core ----------------------------------------------------------------------------------------
def rho_after_from_factors(rho_now, hr_eff, psi=1.0, harm_lambda=0.0, ae_excess=0.0, ceiling=RHO_CEILING):
    """u_after = (1 - rho_now) * hr_eff * psi * (1 + lambda * max(ae_excess, 0)); rho_after = 1 - u_after, bounded [0, ceiling].
    Harm is a multiplicative factor on the unprotected fraction (keeps every elasticity), counts EXCESS toxicity only, and a
    less toxic regimen earns no bonus. Returns (rho_after rounded to 12 dp, flags)."""
    if not 0.0 <= rho_now < 1.0:
        raise ValueError("rho_now must lie in [0, 1)")
    if hr_eff <= 0 or psi <= 0:
        raise ValueError("hr_eff and psi must be positive")
    f = hr_eff * psi * (1.0 + harm_lambda * max(ae_excess, 0.0))
    u = (1.0 - rho_now) * f
    flags = []
    lo, hi = 1.0 - ceiling, 1.0
    if u > hi:
        flags.append("harm_exceeds_bound: rho_after floored at 0 (net harm not fully representable in a bounded rho)")
    if u < lo:
        flags.append("benefit_capped_at_rho_ceiling")
    u = min(max(u, lo), hi)
    return round(1.0 - u, 12), flags


def assess_regimen(core_inputs, patient, trial, horizon, psi_mod=None, z=None, harm_lambda=0.0):
    """Stage 2 gate -> Stage 3 effect -> Stage 4 modifier -> core.assess(). `core_inputs`: N, L, E_sel, V, rho_now, C (and optional
    n_min/n_max for the advisory E_log). Returns the core output untouched plus the adapter's own audit fields."""
    status, why = gate(trial, patient)
    if status != "eligible":
        return {"status": "NO_EVIDENCE_SUPPORTED_OPTION" if status == "outside_evidence" else "ELIGIBILITY_UNKNOWN",
                "regimen": trial.regimen, "reasons": why}
    hr = cumulative_hr(trial.months, trial.s_trt, trial.s_ctrl, horizon)
    psi = (psi_mod or PsiModifier()).psi(trial.id, z)
    out = {"status": "ELIGIBLE_MATCH", "regimen": trial.regimen, "horizon": horizon, "hr_eff": hr, "psi": psi,
           "verified": trial.verified}
    bounds = {}
    for k, scale in (("point", 1.0), ("best", trial.hr_ci_ratio[0]), ("worst", trial.hr_ci_ratio[1])):
        rho_a, flags = rho_after_from_factors(core_inputs["rho_now"], hr * scale, psi, harm_lambda, trial.ae_excess)
        bounds[k] = assess(rho_after=rho_a, **core_inputs)        # I1: all arithmetic is core's
        if k == "point":
            out["rho_after"], out["flags"] = rho_a, flags
    out["core"] = bounds["point"]
    out["R_after_interval"] = (bounds["best"]["R_after"], bounds["worst"]["R_after"])
    return out


def compare_regimens(core_inputs, patient, trials, horizon, psi_mod=None, z=None, harm_lambda=0.0):
    """I8. Rank eligible regimens by core R_after; abstain if the top two intervals overlap. All trials must share a comparator id,
    or the caller must accept that cross-trial comparison is weak (the check below refuses mixed comparators)."""
    comps = {t.comparator for t in trials}
    if len(comps) != 1 or any("_or_" in c for c in comps):
        raise ValueError("regimens do not share one single comparator; no indirect ranking (%s)" % sorted(comps))
    res = [assess_regimen(core_inputs, patient, t, horizon, psi_mod, z, harm_lambda) for t in trials]
    ok = sorted([r for r in res if r["status"] == "ELIGIBLE_MATCH"], key=lambda r: r["core"]["R_after"])
    out = {"results": res, "ranked": [r["regimen"] for r in ok]}
    if not ok:
        out["decision"] = "no evidence-supported option"
    elif len(ok) == 1:
        out["decision"] = ok[0]["regimen"]
    else:
        a, b = ok[0], ok[1]
        overlap = a["R_after_interval"][1] >= b["R_after_interval"][0]
        out["decision"] = "no preferred therapy (intervals overlap)" if overlap else a["regimen"]
        out["tipping_psi"] = tipping_psi(a["R_after_interval"], b["R_after_interval"]) if overlap else None
    return out


# ---- audit of candidate L sources (baseline mortality-risk models) ---------------------------------------------------
# Inputs verified against published definitions (see docs); re-verify from the original papers before pre-registration.
L_SOURCES = {
    "BALAD-2": {"inputs": ["bilirubin", "albumin", "afp", "afp_l3", "dcp"], "components": {},
                "citation": "BALAD-2: Fox et al. (Japanese/UK development); Berhane et al., Clin Gastroenterol Hepatol 2016;14:875-886",
                "practical": "needs AFP-L3 and DCP assays, which few laboratories offer"},
    "CLIP": {"inputs": ["child_pugh", "tumour_morphology", "afp", "portal_vein_thrombosis"],
             "components": {"child_pugh": ["bilirubin", "albumin", "ascites", "encephalopathy", "prothrombin_time"]},
             "citation": "CLIP Investigators, Hepatology 2000;31:840-845 (derived in Italian patients diagnosed 1990-92)",
             "practical": "all inputs routinely recorded; published medians reflect older care and need local calibration"},
    "ALBI-T": {"inputs": ["albi_grade", "tnm_stage"], "components": {"albi_grade": ["bilirubin", "albumin"]},
               "citation": "ALBI grade (Johnson 2015) combined with LCSGJ TNM stage; original ALBI-T report to be verified",
               "practical": "contains ALBI itself, so V would duplicate L"},
}
V_INPUTS = frozenset({"albumin", "bilirubin"})            # ALBI is computed from these two measures
RHO_BIO_INPUTS = frozenset({"ecog", "performance_status"})
TUMOUR_EXTENT_INPUTS = frozenset({"portal_vein_thrombosis", "tumour_morphology", "tnm_stage"})   # also used by the gate or an E reading


def expand_inputs(name):
    """All measures behind a source, including the components of composite inputs (e.g. Child-Pugh)."""
    if name not in L_SOURCES:
        raise ValueError("unknown L source %r; audited sources: %s" % (name, sorted(L_SOURCES)))
    src = L_SOURCES[name]
    out = set()
    for i in src["inputs"]:
        out.add(i)
        out.update(src["components"].get(i, []))
    return out


def audit_l_source(name, constant_inputs=()):
    """Audit a candidate L source against V (ALBI) and rho_bio (ECOG). `constant_inputs` are inputs that take one value in the
    target population (e.g. child_pugh = 'A' after the Stage 2 gate): they carry no information there, so overlap through them
    is 'formal' only. v_status: collapse (V must be set to a declared neutral value), preserved_in_gated_population_only
    (formal overlap, no varying overlap), or preserved."""
    expanded = expand_inputs(name)
    src = L_SOURCES[name]
    const = set(constant_inputs)
    varying = set()
    for i in src["inputs"]:
        if i in const:
            continue
        varying.add(i)
        varying.update(src["components"].get(i, []))
    formal_v, eff_v = sorted(expanded & V_INPUTS), sorted(varying & V_INPUTS)
    formal_r, eff_r = sorted(expanded & RHO_BIO_INPUTS), sorted(varying & RHO_BIO_INPUTS)
    status = lambda f, e: "preserved" if not f else ("preserved_in_gated_population_only" if not e else "collapse")
    return {"source": name, "inputs": list(src["inputs"]), "formal_overlap_V": formal_v, "effective_overlap_V": eff_v,
            "overlap_rho_bio": formal_r, "V_status": status(formal_v, eff_v), "rho_bio_status": status(formal_r, eff_r),
            "stage4_modifier_blocklist": sorted(expanded), "tumour_extent_inputs": sorted(set(src["inputs"]) & TUMOUR_EXTENT_INPUTS),
            "practical": src["practical"], "citation": src["citation"]}


# ---- CLIP as L: two pre-registered readings (decision recorded after the L-source audit) -------------------------
# Strict (primary):  E = 1 and V = 1 (declared neutral). A patient with diagnosed HCC is exposed by definition, and CLIP already
#                    contains the liver-function measures behind ALBI, so V may not enter a second time. rho_bio (ECOG) stays.
# Gated-effective (sensitivity): V = ALBI value retained, valid only where the Stage 2 gate makes Child-Pugh constant (class A), so
#                    CLIP's liver component carries no information (audit_l_source('CLIP', ['child_pugh'])).
# The CLIP score is an INPUT (computed in the clinical record or by the cohort pipeline); it is not re-implemented here.
NEUTRAL = 1.0
READINGS = ("strict", "gated_effective")
CLIP_MAX_CHILD_PUGH_A = 4          # liver component scores 0 for class A: morphology 2 + AFP 1 + portal vein thrombosis 1


@dataclass(frozen=True)
class ClipCalibration:
    """Pre-registered mapping from CLIP score to absolute mortality risk at the horizon, with log-rescale anchors for L.
    No defaults on purpose: every number must come from a cited source or a calibration done in the study cohort."""
    table: Dict[int, float]
    horizon_months: int
    r_lo: float
    r_hi: float
    source: str
    verified: str = "abstract"          # 'full_text' (or a calibration report) required outside a sandbox

    def __post_init__(self):
        if not 0 < self.r_lo < self.r_hi <= 1:
            raise ValueError("anchors must satisfy 0 < r_lo < r_hi <= 1")
        ks = sorted(self.table)
        if any(k < 0 or k > 6 for k in ks) or any(not 0 < self.table[k] <= 1 for k in ks):
            raise ValueError("table keys must be CLIP scores 0-6 and values risks in (0, 1]")
        if any(self.table[a] > self.table[b] + 1e-12 for a, b in zip(ks, ks[1:])):
            raise ValueError("risk must not decrease as the CLIP score rises")


def l_from_clip(clip_score, calib, child_pugh=None, strict=True):
    """L on [0, 1]: calibrated mortality risk at the horizon, rescaled on a log scale between the pre-registered anchors
    (same form as the lung module's L). Refuses impossible inputs and unverified calibrations when strict."""
    if not isinstance(clip_score, int) or isinstance(clip_score, bool) or not 0 <= clip_score <= 6:
        raise ValueError("CLIP score must be an integer from 0 to 6")
    if child_pugh == "A" and clip_score > CLIP_MAX_CHILD_PUGH_A:
        raise ValueError("a CLIP score above 4 is impossible for Child-Pugh class A")
    if strict and calib.verified not in ("full_text", "cohort_calibration"):
        raise ValueError("calibration is verified=%r; strict mode requires 'full_text' or 'cohort_calibration'" % calib.verified)
    if clip_score not in calib.table:
        raise ValueError("calibration table has no entry for CLIP score %d" % clip_score)
    risk = calib.table[clip_score]
    if risk <= calib.r_lo:
        return 0.0
    return min(1.0, math.log10(risk / calib.r_lo) / math.log10(calib.r_hi / calib.r_lo))


def core_inputs_for_reading(reading, L, rho_now, patient, V_albi=None, C=5, N=100_000, n_min=None, n_max=None):
    """Inputs for assess_regimen under one of the two readings. All arithmetic stays in core."""
    if reading not in READINGS:
        raise ValueError("reading must be one of %s" % (READINGS,))
    if reading == "strict":
        E, V = NEUTRAL, NEUTRAL
    else:
        if patient.get("child_pugh") != "A":
            raise ValueError("gated-effective reading is valid only where Child-Pugh is constant (class A)")
        if audit_l_source("CLIP", constant_inputs=["child_pugh"])["V_status"] != "preserved_in_gated_population_only":
            raise ValueError("audit no longer supports retaining V; re-run the L-source audit")
        if V_albi is None or not 0.0 <= V_albi <= 1.0:
            raise ValueError("gated-effective reading needs V_albi in [0, 1]")
        E, V = NEUTRAL, float(V_albi)
    ci = dict(N=N, L=L, E_sel=E, V=V, rho_now=rho_now, C=C)
    if n_min is not None:
        ci["n_min"] = n_min
    if n_max is not None:
        ci["n_max"] = n_max
    return ci


def compare_readings(L, rho_now, patient, trials, horizon, V_albi, psi_mod=None, z=None, harm_lambda=0.0, **core_kw):
    """Sensitivity analysis required by the pre-registration: decisions and tiers under both readings, and whether the
    ranking/abstention decision changed (it should not: L, E, V multiply every regimen's R equally)."""
    out = {}
    for rd in READINGS:
        ci = core_inputs_for_reading(rd, L, rho_now, patient, V_albi=V_albi, **core_kw)
        res = compare_regimens(ci, patient, trials, horizon, psi_mod, z, harm_lambda)
        out[rd] = {"decision": res["decision"],
                   "tiers": {r["regimen"]: (r["core"]["tier_now"], r["core"]["tier_after"]) for r in res["results"] if r["status"] == "ELIGIBLE_MATCH"}}
    out["decision_unchanged"] = out["strict"]["decision"] == out["gated_effective"]["decision"]
    return out
