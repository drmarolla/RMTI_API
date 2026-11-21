# Copyright 2025-2026 Cesar Marolla. Apache-2.0.
"""Urban infrastructure resilience application (Sub-Saharan Africa cohort).

Inputs reproduce Tables 4-6 of Marolla (2026), Int. J. Management and Data
Analytics 6(1):354-388, doi:10.68485/ijmada.20266156. The inputs themselves
are analyst-scored from the World Bank AFRI-RES compendium; they are *not*
empirical measurements, and rho_after values are scenario assumptions.
"""
from ..core import assess, rank_cohort

COHORT = {
    "Bamako":        dict(N=4_500_000,  L=0.800, E_sel=0.850, V=0.750, rho_now=0.20, rho_after=0.58, C=4),
    "Lagos":         dict(N=16_000_000, L=0.900, E_sel=0.650, V=0.800, rho_now=0.20, rho_after=0.55, C=5),
    "Lilongwe":      dict(N=1_100_000,  L=0.875, E_sel=0.800, V=0.800, rho_now=0.25, rho_after=0.48, C=4),
    "Nairobi":       dict(N=4_700_000,  L=0.900, E_sel=0.880, V=0.550, rho_now=0.55, C=4),
    "Dar es Salaam": dict(N=7_400_000,  L=0.850, E_sel=0.930, V=0.780, rho_now=0.55, C=4),
    "Lusaka":        dict(N=3_360_000,  L=0.800, E_sel=0.850, V=0.720, rho_now=0.45, C=3),
}
METADATA = {"Bamako": ("Mali", "Drought / Niger flood / heat"), "Lagos": ("Nigeria", "Coastal & pluvial flood"),
            "Lilongwe": ("Malawi", "Pluvial / riverine flood"), "Nairobi": ("Kenya", "Pluvial flood"),
            "Dar es Salaam": ("Tanzania", "Coastal flood"), "Lusaka": ("Zambia", "Flood / cholera")}

# (city, field, value) as printed in the paper's Tables 4-5
PAPER_VALUES = [("Bamako", "R_now", 0.408), ("Bamako", "R_after", 0.214),
                ("Lagos", "R_now", 0.374), ("Lagos", "R_after", 0.211),
                ("Lilongwe", "R_now", 0.420), ("Lilongwe", "R_after", 0.291),
                ("Nairobi", "R_now", 0.196), ("Dar es Salaam", "R_now", 0.277),
                ("Lusaka", "R_now", 0.269)]


def ranked():
    return rank_cohort(COHORT)


def selfcheck(tol=0.0005):
    by = {r["name"]: r for r in ranked()}
    rows = [(c, f, v, by[c][f], abs(by[c][f] - v) < tol) for c, f, v in PAPER_VALUES]
    return rows, all(r[-1] for r in rows)
