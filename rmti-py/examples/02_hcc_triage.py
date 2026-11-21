"""HCC: patient-level triage and tier robustness. Research prototype; NOT clinical advice."""
from rmti import UncertainParam as U, simulate_rmti
from rmti.domains import hcc

# ALBI from labs (units explicit)
s = hcc.albi_score(albumin=38, bilirubin=1.2, albumin_unit="g/L", bilirubin_unit="mg/dL")
print(f"ALBI {s:.2f} -> grade {hcc.albi_grade(s)} -> V={hcc.albi_grade_to_V(hcc.albi_grade(s))}")

patients = [
    dict(id="A", L=0.30, E=0.60, albi_grade=1, surveillance="usual", bclc_if_missed="A", improved_surveillance="optimised"),
    dict(id="B", L=0.25, E=0.60, albi_grade=2, surveillance="usual", bclc_if_missed="C-D", improved_surveillance="optimised"),
]
for r in hcc.triage(patients):
    print(r)

# Cohort-level: how confident is "High" for high-burden MASLD under usual care?
c = hcc.PEARL_COHORTS["High-burden MASLD"]
for grade in ("w_ib", "w_id"):
    r = simulate_rmti(U(c["L"], grade), U(c["E_sel"], grade), U(c["V"], grade), U(c["rho_now"], grade),
                      rho_after=U(c["rho_after"], grade))
    print(grade, r.summary()["tier_probabilities"], "P(point tier)=", round(r.p_point_tier, 2))
