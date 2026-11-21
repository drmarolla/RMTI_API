# Copyright 2025-2026 Cesar Marolla. Apache-2.0.
"""Hepatocellular carcinoma (HCC) surveillance application of the RMTI.

Research prototype. Not validated against incident-HCC outcomes. Not a
medical device; not for individual patient care decisions.

Anchors: ALBI grade -> V, surveillance-adequacy ladder -> rho, BCLC stage at
detection -> C. L is supplied by a validated score (aMAP, THRI, hccrisk) and
is NOT re-derived here.
"""
from __future__ import annotations

from typing import Dict, Iterable, Mapping, Sequence

import numpy as np

from ..core import assess, rank_cohort, score

N_MIN_HCC, N_MAX_HCC = 10, 650_000          # advisory E_log bounds (clinic panel .. US cirrhosis)

ALBI_V = {1: 0.35, 2: 0.60, 3: 0.85}
RHO = {"none": 0.15, "usual": 0.20, "outreach": 0.45, "specialist": 0.50, "optimised": 0.65}
C_BCLC = {"0": 0.10, "A": 0.30, "early-int": 0.50, "B": 0.75, "C-D": 1.00}
_C_TO_LEVEL = {0.10: 1, 0.30: 2, 0.50: 3, 0.75: 4, 1.00: 5}
C_LEVEL = {k: _C_TO_LEVEL[v] for k, v in C_BCLC.items()}   # BCLC label -> core C level 1..5

# ALBI (Johnson et al., J Clin Oncol 2015): 0.66*log10(bilirubin umol/L) - 0.085*albumin g/L
ALBI_CUT_1, ALBI_CUT_2 = -2.60, -1.39


def albi_score(albumin, bilirubin, albumin_unit="g/L", bilirubin_unit="umol/L"):
    """ALBI score from measured albumin and bilirubin (scalars or arrays).
    Units are explicit because deposited datasets differ: albumin 'g/L'|'g/dL',
    bilirubin 'umol/L'|'mg/dL'."""
    alb = np.asarray(albumin, dtype=float) * {"g/L": 1.0, "g/dL": 10.0}[albumin_unit]
    bil = np.asarray(bilirubin, dtype=float) * {"umol/L": 1.0, "mg/dL": 17.1}[bilirubin_unit]
    if np.any(bil <= 0):
        raise ValueError("bilirubin must be > 0")
    out = 0.66 * np.log10(bil) - 0.085 * alb
    return float(out) if out.ndim == 0 else out


def albi_grade(score_):
    """Grade 1 (<= -2.60), 2 (> -2.60 to <= -1.39), 3 (> -1.39)."""
    g = np.where(np.asarray(score_) <= ALBI_CUT_1, 1, np.where(np.asarray(score_) <= ALBI_CUT_2, 2, 3))
    return int(g) if g.ndim == 0 else g


def albi_grade_to_V(grade: int) -> float:
    return ALBI_V[int(grade)]


def cohort_albi_vulnerability(grade_counts: Mapping[int, int]) -> float:
    """Cohort-mean V = sum(p_g * anchor_g)."""
    n = sum(grade_counts.values())
    return round(sum(ALBI_V[g] * c for g, c in grade_counts.items()) / n, 4)


# --- patient-level triage ---------------------------------------------------
def score_patient(L: float, E: float, albi_grade_: int, surveillance: str,
                  bclc_if_missed: str, improved_surveillance: str = None) -> Dict:
    """One patient. ``surveillance`` is a key of RHO; ``bclc_if_missed`` a key of C_BCLC."""
    V = albi_grade_to_V(albi_grade_)
    now = score(L, E, V, RHO[surveillance], C_LEVEL[bclc_if_missed])
    out = {"V": V, "R": now["R"], "tier": now["tier"], "EAL": now["EAL"]}
    if improved_surveillance:
        aft = score(L, E, V, RHO[improved_surveillance], C_LEVEL[bclc_if_missed])
        out.update({"R_after": aft["R"], "tier_after": aft["tier"], "EAL_after": aft["EAL"]})
    return out


def triage(patients: Sequence[Mapping]) -> list:
    """Rank patients by tier then EAL (within-tier priority rule). Each mapping needs
    id, L, E, albi_grade, surveillance, bclc_if_missed."""
    rows = []
    for p in patients:
        s = score_patient(p["L"], p["E"], p["albi_grade"], p["surveillance"], p["bclc_if_missed"],
                          p.get("improved_surveillance"))
        s["id"] = p.get("id")
        rows.append(s)
    order = {"Tier 1 - Low": 0, "Tier 2 - Moderate": 1, "Tier 3 - High": 2, "Tier 4 - Severe": 3, "Tier 5 - Critical": 4}
    rows.sort(key=lambda r: (-order[r["tier"]], -r["EAL"]))
    return rows


# --- datasets (preprint Tables 1 and 2) -------------------------------------
PUBLISHED_COHORTS = {
    "Untreated HBV":          dict(N=100_000, L=0.90, E_sel=0.70, V=0.55, rho_now=0.10, rho_after=0.45, C=5),
    "Active viral cirrhosis": dict(N=100_000, L=0.55, E_sel=0.70, V=0.53, rho_now=0.50, rho_after=0.65, C=5),
    "Alcohol cirrhosis":      dict(N=100_000, L=0.30, E_sel=0.65, V=0.60, rho_now=0.20, rho_after=0.50, C=5),
    "Cured-HCV cirrhosis":    dict(N=100_000, L=0.25, E_sel=0.60, V=0.48, rho_now=0.20, rho_after=0.55, C=5),
    "Suppressed-HBV":         dict(N=100_000, L=0.20, E_sel=0.55, V=0.45, rho_now=0.20, rho_after=0.55, C=5),
    "NAFLD cirrhosis":        dict(N=100_000, L=0.15, E_sel=0.60, V=0.53, rho_now=0.20, rho_after=0.50, C=5),
}
PEARL_COHORTS = {
    "MASLD cirrhosis (compensated)": dict(N=100_000, L=0.15, E_sel=0.60, V=0.50, rho_now=0.20, rho_after=0.65, C=5),
    "Suppressed HBV":                dict(N=100_000, L=0.20, E_sel=0.60, V=0.50, rho_now=0.20, rho_after=0.65, C=5),
    "HCV post-SVR":                  dict(N=100_000, L=0.25, E_sel=0.60, V=0.50, rho_now=0.20, rho_after=0.65, C=5),
    "Alcohol cirrhosis (Pearl)":     dict(N=100_000, L=0.30, E_sel=0.60, V=0.50, rho_now=0.20, rho_after=0.65, C=5),
    "Active viral (Pearl)":          dict(N=100_000, L=0.55, E_sel=0.60, V=0.50, rho_now=0.20, rho_after=0.65, C=5),
    "High-burden MASLD":             dict(N=100_000, L=0.65, E_sel=0.60, V=0.50, rho_now=0.20, rho_after=0.65, C=5),
}
PAPER_TABLE1 = [("Untreated HBV", 0.312, 0.191), ("Active viral cirrhosis", 0.102, 0.071),
                ("Alcohol cirrhosis", 0.094, 0.059), ("Cured-HCV cirrhosis", 0.058, 0.032),
                ("Suppressed-HBV", 0.040, 0.022), ("NAFLD cirrhosis", 0.038, 0.024)]
PAPER_TABLE2 = [("MASLD cirrhosis (compensated)", 0.036, 0.016), ("Suppressed HBV", 0.048, 0.021),
                ("HCV post-SVR", 0.060, 0.026), ("Alcohol cirrhosis (Pearl)", 0.072, 0.032),
                ("Active viral (Pearl)", 0.132, 0.058), ("High-burden MASLD", 0.156, 0.068)]

# Preprint Table 1a: HCC 35/62/4 %, cirrhosis 48/52/0 % -> V 0.52 / 0.48.
# (10, 18, 1) of n=29 reproduces that; the earlier archive used (9, 19, 1) -> 0.53.
# VERIFY against the Harvard Dataverse file doi:10.7910/DVN/A81UVO before citing.
FARIA_ALBI_COUNTS = {"HCC": {1: 10, 2: 18, 3: 1}, "cirrhosis": {1: 12, 2: 13, 3: 0}}


def _with_bounds(cohort):
    return {k: {**v, "n_min": N_MIN_HCC, "n_max": N_MAX_HCC} for k, v in cohort.items()}


def ranked(cohort=PUBLISHED_COHORTS):
    return rank_cohort(_with_bounds(cohort))


def selfcheck(tol=0.0005):
    """Reproduce every R value in preprint Tables 1 and 2. Returns (rows, ok)."""
    rows = []
    for cohort, table in ((PUBLISHED_COHORTS, PAPER_TABLE1), (PEARL_COHORTS, PAPER_TABLE2)):
        by = {r["name"]: r for r in ranked(cohort)}
        for name, r_now, r_after in table:
            for f, v in (("R_now", r_now), ("R_after", r_after)):
                rows.append((name, f, v, by[name][f], abs(by[name][f] - v) < tol))
    return rows, all(r[-1] for r in rows)


def score_table(df, albumin_unit: str = "g/L", bilirubin_unit: str = "umol/L"):
    """Vectorised patient-level scoring for a registry (pandas DataFrame in, DataFrame out).

    Required columns: L, E, surveillance (key of RHO), bclc_if_missed (key of C_BCLC), and either
    ``albi_grade`` or both ``albumin`` and ``bilirubin`` (units set by the arguments).
    Optional: ``improved_surveillance`` (adds R_after/tier_after/EAL_after), ``id``.
    Adds V, R, tier_n (1-5), tier, EAL and ``priority`` (1 = act first: tier, then EAL).
    Research prototype: not for individual patient decisions.
    """
    from ..core import TIER_LABELS, score_array

    d = df.copy()
    for c in ("L", "E", "surveillance", "bclc_if_missed"):
        if c not in d:
            raise ValueError(f"missing column {c!r}")
    have_labs = {"albumin", "bilirubin"} <= set(d.columns)
    if "albi_grade" not in d:
        if not have_labs:
            raise ValueError("need albi_grade or both albumin and bilirubin")
        d["albi_grade"] = np.nan
    missing = d["albi_grade"].isna()
    if missing.any():
        if not have_labs or d.loc[missing, ["albumin", "bilirubin"]].isna().any().any():
            raise ValueError("every row needs albi_grade or both albumin and bilirubin")
        sc = albi_score(d.loc[missing, "albumin"].to_numpy(float), d.loc[missing, "bilirubin"].to_numpy(float),
                        albumin_unit, bilirubin_unit)
        d.loc[missing, "albi_score"] = sc
        d.loc[missing, "albi_grade"] = albi_grade(sc)
    if not d["albi_grade"].astype(int).isin(ALBI_V).all():
        raise ValueError("albi_grade must be 1, 2 or 3")
    for name, col, table in (("surveillance", "surveillance", RHO), ("bclc_if_missed", "bclc_if_missed", C_BCLC)):
        bad = sorted(set(d[col]) - set(table))
        if bad:
            raise ValueError(f"unknown {name} values {bad}; allowed: {sorted(table)}")
    for c in ("L", "E"):
        if d[c].isna().any() or not d[c].between(0, 1).all():
            raise ValueError(f"{c} must be present and within [0, 1]")
    d["V"] = d["albi_grade"].astype(int).map(ALBI_V)
    d["rho"] = d["surveillance"].map(RHO)
    c_level = d["bclc_if_missed"].map(C_LEVEL).to_numpy()
    s = score_array(d["L"], d["E"], d["V"], d["rho"], C=c_level)
    d["R"], d["EAL"], d["tier_n"] = s["R"], s["EAL"], s["tier_index"] + 1
    d["tier"] = [TIER_LABELS[i - 1] for i in d["tier_n"]]
    if "improved_surveillance" in d:
        s2 = score_array(d["L"], d["E"], d["V"], d["improved_surveillance"].map(RHO), C=c_level)
        d["R_after"], d["EAL_after"] = s2["R"], s2["EAL"]
        d["tier_after"] = [TIER_LABELS[i] for i in s2["tier_index"]]
    d = d.sort_values(["tier_n", "EAL"], ascending=[False, False], kind="stable")
    d["priority"] = np.arange(1, len(d) + 1)
    return d
