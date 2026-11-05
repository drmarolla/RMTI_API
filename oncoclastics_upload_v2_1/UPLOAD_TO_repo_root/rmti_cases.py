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



# ---------------------------------------------------------------- liver: published Table 2 cohorts (HCC calculator v2.3.0, rows 5-10)
# NOTE (from the workbook): rho-after values for Table 2 rows are back-solved to reproduce the paper's published R-after column.
def _liver(key, label, name, L, E, V, r1, r2, C, note):
    return dict(key=key, label=label, name=name, L=L, E=E, V=V, rho_now=r1, rho_after=r2, C=C, N=100_000, domain="oncology",
                source="RMTI-HCC calculator v2.3.0, Table 2 (published cohort). " + note)

LIVER_CASES = [
    _liver("hbv_untreated", "HBV untreated", "Untreated hepatitis B (~12.8%/yr, historical)", 0.90, 0.70, 0.55, 0.10, 0.45, 5, "rho-after back-solved to the published R-after"),
    _liver("viral_cirrhosis", "Viral cirrhosis", "Active viral cirrhosis (2-7%/yr)", 0.55, 0.70, 0.53, 0.50, 0.65, 5, "rho-after back-solved to the published R-after"),
    _liver("alcohol_cirrhosis", "Alcohol cirrh.", "Alcohol-related cirrhosis (1-2.5%/yr)", 0.30, 0.65, 0.60, 0.20, 0.50, 5, "rho-after back-solved to the published R-after"),
    _liver("hcv_cured", "HCV cured", "Cured-HCV cirrhosis (~1.8%/yr)", 0.25, 0.60, 0.48, 0.20, 0.55, 5, "rho-after back-solved to the published R-after"),
]
LIVER_EXTRA = dict(hbv_suppressed=_liver("hbv_suppressed", "HBV suppressed", "Suppressed hepatitis B (~1.25%/yr)", 0.20, 0.55, 0.45, 0.20, 0.55, 5, "rho-after back-solved"))

# resilience ladder for HCC surveillance (workbook 'Reference'): advisory anchors, not a lookup
RHO_LADDER_HCC = [("none", 0.15), ("usual care", 0.20), ("outreach", 0.45), ("specialist", 0.50), ("optimised", 0.65)]

# ---------------------------------------------------------------- floods and heat (published rubric values, disaster calculator v2.3.0, rows 5-6, 7)
FLOOD_HEAT_CASES = [
    dict(key="lilongwe", label="Lilongwe", name="Lilongwe, Malawi (pluvial and river flood)", N=1_100_000, L=0.875, E=0.80, V=0.80,
         rho_now=0.25, rho_after=0.48, C=4, domain="disaster",
         source="RMTI disaster calculator v2.3.0, worked example; rho-after is a scenario target (pathway 0.43-0.53 by 2027-2030)"),
    dict(key="lagos", label="Lagos", name="Lagos, Nigeria (coastal and pluvial flood)", N=16_000_000, L=0.90, E=0.65, V=0.80,
         rho_now=0.20, rho_after=0.55, C=5, domain="disaster",
         source="RMTI disaster calculator v2.3.0, worked example; E is the published rubric value (population-derived helper gives about 0.98)"),
    dict(key="bamako", label="Bamako", name="Bamako, Mali (drought, flood and heat)", N=4_500_000, L=0.80, E=0.85, V=0.75,
         rho_now=0.20, rho_after=0.58, C=4, domain="disaster",
         source="RMTI disaster calculator v2.3.0, worked example (multi-hazard: drought, flood, heat); rho-after is a scenario target"),
]

PRESETS = {c["label"]: c for c in ONCOLOGY_CASES + DISASTER_CASES + LIVER_CASES + FLOOD_HEAT_CASES}
for _c in LIVER_EXTRA.values():
    PRESETS[_c["label"]] = _c

# ---------------------------------------------------------------- tier postures (workbook 'Reference' sheets)
POSTURE_HCC = {1: "Monitor; usual-care biannual surveillance appropriate",
               2: "Usual-care biannual surveillance appropriate; confirm adherence and recall",
               3: "Prioritise for surveillance; fixed-interval adherence essential",
               4: "Structured navigation; close specialist hepatology follow-up",
               5: "Immediate, resourced pathway; case management"}
POSTURE_DISASTER = {1: "Monitor; maintain baseline", 2: "Low-regret preventive measures", 3: "Structured mitigation; fund soon",
                    4: "Priority capital; act now", 5: "Immediate, system-level response"}
TIER_LOWER = {1: 0.0, 2: 0.05, 3: 0.15, 4: 0.35, 5: 0.60}


def tier_no(R):
    return int(tier(R)[0])


# ---------------------------------------------------------------- lever mathematics (pure arithmetic on R = L*E*V*(1-rho))
LEVERS = ("L", "E", "V", "rho")


def _val(c, lever):
    return c["rho_now"] if lever == "rho" else c[lever]


def r_with(c, **over):
    L, E, V, rho = (over.get(k, _val(c, k)) for k in LEVERS)
    return r_score(L, E, V, rho)


def sweep(c, lever, lo, hi, n=60):
    xs = [lo + (hi - lo) * i / (n - 1) for i in range(n)]
    return xs, [r_with(c, **{lever: x}) for x in xs]


def tornado(c, step=0.10):
    """R change if each lever moves by `step` in the risk-reducing direction (L, E, V down; rho up). Illustrative step, not an effect size."""
    base = r_with(c)
    out = {}
    for k in LEVERS:
        v = _val(c, k)
        nv = min(0.99, v + step) if k == "rho" else max(0.0, v - step)
        out[k] = r_with(c, **{k: nv}) - base
    return base, out


def to_next_tier(c):
    """For the tier below the case's current tier: the single-lever value that would just reach it (others fixed). None if tier 1."""
    R = r_with(c)
    t = tier_no(R)
    if t == 1:
        return None
    target = TIER_LOWER[t]                         # R must fall below this
    L, E, V, rho = (_val(c, k) for k in LEVERS)
    need = {}
    need["rho"] = 1 - target / (L * E * V) if L * E * V > 0 else None        # rho must be at least this
    need["V"] = target / (L * E * (1 - rho))                                  # V must be at most this
    need["E"] = target / (L * V * (1 - rho))
    need["L"] = target / (E * V * (1 - rho))
    return dict(tier=t, target=target, R=R, need=need,
                feasible={k: (v is not None and 0 <= v < (0.99 if k == "rho" else 1.0)) for k, v in need.items()})
