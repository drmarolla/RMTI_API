"""
rmti_cases.py  --  published / illustrative case-study inputs shared by the demo pages and the video renderer.

SAFETY: this file contains NO patient-level data. Oncology uses only aggregate ALBI-grade COUNTS per group
(Faria et al. cohort, Harvard Dataverse doi:10.7910/DVN/A81UVO); disaster cases are the published rubric values
in the RMTI disaster calculator (v2.3.0). Values were checked against RMTI_HCC_Calculator_v2_3_0.xlsx and
RMTI_Calculator_Disaster_v2_3_0.xlsx (see tests/test_cases.py).

R = L * E * V * (1 - rho). R is a relative rubric index, not a probability, forecast or loss estimate.
"""

TIERS = [(0.05, "1 Low"), (0.15, "2 Moderate"), (0.35, "3 High"), (0.60, "4 Severe"), (float("inf"), "5 Critical")]
ALBI_ANCHORS = {1: 0.35, 2: 0.60, 3: 0.85}          # ALBI grade -> V anchor (workbook, sheet 'ALBI to Vulnerability')


def tier(R):
    for upper, name in TIERS:
        if R < upper:
            return name


def r_score(L, E, V, rho):
    return L * E * V * (1 - rho)


def v_from_counts(n1, n2, n3):
    n = n1 + n2 + n3
    return (n1 * ALBI_ANCHORS[1] + n2 * ALBI_ANCHORS[2] + n3 * ALBI_ANCHORS[3]) / n


def evaluate(c):
    r0 = c["L"] * c["E"] * c["V"]
    rn = r_score(c["L"], c["E"], c["V"], c["rho_now"])
    ra = r_score(c["L"], c["E"], c["V"], c["rho_after"])
    return dict(R0=r0, R_now=rn, R_after=ra, tier_now=tier(rn), tier_after=tier(ra))


# ---------------------------------------------------------------- oncology: HCC, Faria et al. (V only is data-anchored)
FARIA_DOI = "10.7910/DVN/A81UVO"
FARIA_COUNTS = {"HCC cohort": (10, 18, 1), "Cirrhosis cohort": (12, 13, 0)}      # ALBI grade 1/2/3 counts (n=29, n=25)
_ILLUSTRATIVE = dict(L=0.30, E=0.60, rho_now=0.20, rho_after=0.65, C=5)          # Patient A L,E,rho; Table-3 rho-after

ONCOLOGY_CASES = [
    dict(key="faria_hcc", label="HCC cohort", name="Faria et al., HCC cohort (n=29)",
         V=v_from_counts(*FARIA_COUNTS["HCC cohort"]), N=29, domain="oncology", **_ILLUSTRATIVE,
         source="V from published ALBI grade counts 10/18/1 (Faria et al., doi:%s); L, E, rho illustrative" % FARIA_DOI),
    dict(key="faria_cirr", label="Cirrhosis", name="Faria et al., cirrhosis cohort (n=25)",
         V=v_from_counts(*FARIA_COUNTS["Cirrhosis cohort"]), N=25, domain="oncology", **_ILLUSTRATIVE,
         source="V from published ALBI grade counts 12/13/0 (Faria et al., doi:%s); L, E, rho illustrative" % FARIA_DOI),
]

# ---------------------------------------------------------------- disaster science (published rubric values, calculator v2.3.0)
DISASTER_CASES = [
    dict(key="palisades", label="Palisades", name="Pacific Palisades, USA (Palisades Fire, Jan 2025)", N=21_300,
         L=0.40, E=0.90, V=0.40, rho_now=0.20, rho_after=0.35, C=4, domain="disaster",
         source="RMTI disaster calculator v2.3.0, '2025 case study'; rho-after is a scenario target"),
    dict(key="altadena", label="Altadena", name="Altadena, USA (Eaton Fire, Jan 2025)", N=23_000,
         L=0.40, E=0.80, V=0.60, rho_now=0.20, rho_after=0.35, C=4, domain="disaster",
         source="RMTI disaster calculator v2.3.0, '2025 case study'; rho-after is a scenario target"),
    dict(key="lilongwe", label="Lilongwe", name="Lilongwe, Malawi (pluvial / river flood)", N=1_100_000,
         L=0.875, E=0.80, V=0.80, rho_now=0.25, rho_after=0.48, C=4, domain="disaster",
         source="RMTI disaster calculator v2.3.0, worked example; rho-after is a scenario target"),
]

PRESETS = {c["label"]: c for c in ONCOLOGY_CASES + DISASTER_CASES}
