# Copyright 2026 Cesar Marolla. Licensed under the Apache License, Version 2.0.
"""
rmti_johnson_case.py -- RMTI case study on chronic liver disease and HCC, built on two
published studies led by Dr. Philip J. Johnson (University of Liverpool).

RESEARCH PROTOTYPE. Not validated. Not a medical device. The studies' figures are quoted as
reported; every RMTI mapping and every derived number below is illustrative. Dr. Johnson and
his co-authors did not review this case study and are not responsible for the mapping.

No new model equation. It uses rmti_elasticity.py and rmti_resilience_components.py:
    R = L * E * V * (1 - rho),   rho = 1 - (1 - rho_bio)(1 - rho_care)
    eps_L = eps_E = eps_V = 1,   eps_rho_care = -rho_care / (1 - rho_care)

Derived inputs: L is the cumulative HCC risk over a horizon, 1 - exp(-rate * years), from the
published incidence per 1000 patient-years. E, V and rho_bio are user-set placeholders.
"""
import math
from typing import Dict, List, Optional, Sequence

from rmti_elasticity import elasticity_rho_component, elasticity_wrt_drive, log_decomposition
from rmti_resilience_components import combine_rho

SOURCES = {
    "johnson2024": {
        "authors": "Johnson PJ, Kalyuzhnyy A, Boswell E, Toyoda H",
        "title": "Progression of chronic liver disease to hepatocellular carcinoma: implications for surveillance and management",
        "journal": "BJC Reports (2024)",
        "doi": "10.1038/s44276-024-00050-0",
    },
    "cucchetti2023": {
        "authors": "Cucchetti A, Elshaarawy O, Han G, Chong CCN, Serra C, O'Rourke JM, Crew R, Felicani C, Ercolani G, Shah T, Vogel A, Lai PBS, Johnson PJ",
        "title": "'Potentially curative therapies' for hepatocellular carcinoma: how many patients can actually be cured?",
        "journal": "British Journal of Cancer (2023) 128:1665-1671",
        "doi": "10.1038/s41416-023-02188-z",
    },
}

# Quoted as reported in the two papers.
PUBLISHED = {
    "johnson2024": [
        ("Cohort", "2592 chronic liver disease patients without cirrhosis at entry (Ogaki, Japan); median follow-up 13.2 years"),
        ("HCC", "172 patients (7%) developed HCC; 5 cases per 1000 patient-years (cirrhosis at entry, n = 890: 31 per 1000)"),
        ("Pathways", "124 (72%) crossed the Fib-4 > 3.25 threshold before HCC, on average about 10 years before diagnosis; 48 (28%) did not"),
        ("Hepatitis B", "20 of 29 HBV-related HCC (69%) arose without passing through cirrhosis; only 31% followed the cirrhotic pathway"),
        ("Hepatitis C", "81% of HCV-related HCC passed through cirrhosis; after a sustained virological response, cirrhosis developed about 7 years before HCC"),
        ("Baseline Fib-4", "median 2.4 in patients who later developed HCC versus 1.52 in those who did not"),
        ("At diagnosis", "74.4% received potentially curative treatment; 70.9% within Milan criteria"),
    ],
    "cucchetti2023": [
        ("Cohort", "1571 patients treated with radiofrequency or microwave ablation, 5 centres, median follow-up 4.7 years"),
        ("Cure fraction", "18.3% overall; up to 39.8% (single tumour under 2 cm, ALBI grade 1, most favourable subgroup, treated from 2014)"),
        ("By ALBI grade", "grade 1: 23.8%; grade 2: 14.8%; grade 3: 12.0%"),
        ("By tumour size", "under 2 cm: 26.9%; 2-3 cm: 19.2%; 3.1-5 cm: 12.7%; over 5 cm: 4.6%"),
        ("Years of life lost", "median 17.2 years after ablation; it takes about 10 years before cure can be claimed with 90% certainty"),
        ("Comparison", "resection about 25% and transplantation over 70% cure (from the authors' earlier models)"),
    ],
}

LIVERPOOL_CALCULATOR = "https://prediction-models.liverpool.ac.uk/curative"
INCIDENCE_PER_1000_PY = {"Non-cirrhotic at entry": 5.0, "Cirrhosis at entry": 31.0}


def cumulative_risk(rate_per_1000_py: float, years: float) -> float:
    """Cumulative probability 1 - exp(-rate * years) from an incidence per 1000 patient-years."""
    if rate_per_1000_py <= 0 or years <= 0:
        raise ValueError("rate and years must be positive")
    return 1.0 - math.exp(-rate_per_1000_py / 1000.0 * years)


def scenario(L: float, E: float, V: float, rho_bio: float, rho_care: float) -> Dict[str, float]:
    rho = combine_rho(rho_bio, rho_care)
    return {"L": L, "E": E, "V": V, "rho_bio": rho_bio, "rho_care": rho_care, "rho": rho,
            "R": L * E * V * (1.0 - rho), "eps_rho_care": elasticity_rho_component(rho_care)}


def case_table(E: float = 0.60, V: float = 0.50, rho_bio: float = 0.30, rho_care_low: float = 0.20,
               rho_care_high: float = 0.70, years: float = 10.0) -> List[Dict]:
    """Two pathways (incidence of Johnson et al. 2024) by two levels of care-system delivery."""
    rows = []
    for pathway, rate in INCIDENCE_PER_1000_PY.items():
        L = cumulative_risk(rate, years)
        for label, rc in (("low delivery", rho_care_low), ("high delivery", rho_care_high)):
            row = scenario(L, E, V, rho_bio, rc)
            row.update({"pathway": pathway, "care": label})
            rows.append(row)
    return rows


def pathway_comparison(rows: Sequence[Dict]) -> Dict[str, float]:
    """Log attribution from (non-cirrhotic, low delivery) to (cirrhosis, high delivery)."""
    a, b = rows[0], rows[3]
    return log_decomposition({k: a[k] for k in ("L", "E", "V", "rho")}, {k: b[k] for k in ("L", "E", "V", "rho")})


def breakeven_rho_care(L_ref: float, L_other: float, rho_care_ref: float) -> Optional[float]:
    """rho_care at which R for L_other equals R for L_ref at rho_care_ref (E, V, rho_bio equal).
    Returns None if no value in [0, 1) exists."""
    x = 1.0 - (1.0 - rho_care_ref) * L_ref / L_other
    return x if 0.0 <= x < 1.0 else None


def fib4_v_elasticity(fib4_values: Sequence[float] = (1.52, 2.4, 3.25), v_lo: float = 0.35,
                      v_hi: float = 0.85, y_max: float = 6.0) -> List[Dict[str, float]]:
    """V* = v_lo + k*clip(Fib-4, 0, y_max) with PLACEHOLDER anchors; eps_d from rmti_elasticity."""
    k = (v_hi - v_lo) / y_max
    return [{"fib4": d, "V_star": v_lo + k * min(max(d, 0.0), y_max),
             "eps_d": elasticity_wrt_drive(d, v_lo, v_hi, y_max)} for d in fib4_values]


def _demo() -> None:
    rows = case_table()
    print("rmti_johnson_case demo -- illustrative, research prototype\n")
    for r in rows:
        print(f"{r['pathway']:<24}{r['care']:<14} L={r['L']:.4f} rho={r['rho']:.3f} R={r['R']:.5f} eps_rho_care={r['eps_rho_care']:+.2f}")
    d = pathway_comparison(rows)
    print(f"\ncirrhosis + high delivery vs non-cirrhotic + low delivery: R changes {d['pct_change_R']:+.0f}%")
    be = breakeven_rho_care(rows[0]["L"], rows[2]["L"], 0.20)
    print(f"break-even rho_care for cirrhosis to match non-cirrhotic R at rho_care 0.20: {be:.2f}")


if __name__ == "__main__":
    _demo()
