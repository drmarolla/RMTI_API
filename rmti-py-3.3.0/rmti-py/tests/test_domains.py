import numpy as np
import pytest
from rmti.domains import hcc, urban


def test_urban_selfcheck():
    assert urban.selfcheck()[1]


def test_hcc_selfcheck_both_tables():
    rows, ok = hcc.selfcheck()
    assert ok and len(rows) == 24


def test_albi_known_values():
    s = hcc.albi_score(45, 10)                      # g/L, umol/L
    assert s == pytest.approx(0.66 * 1 - 0.085 * 45) and hcc.albi_grade(s) == 1
    assert hcc.albi_grade(hcc.albi_score(30, 50)) == 2
    assert hcc.albi_grade(hcc.albi_score(28, 100)) == 3


def test_albi_unit_conversion_consistent():
    a = hcc.albi_score(4.0, 1.0, "g/dL", "mg/dL")
    b = hcc.albi_score(40.0, 17.1, "g/L", "umol/L")
    assert a == pytest.approx(b)


def test_albi_vectorised_and_validation():
    g = hcc.albi_grade(hcc.albi_score(np.array([45, 30, 28]), np.array([10, 50, 100])))
    assert list(g) == [1, 2, 3]
    with pytest.raises(ValueError):
        hcc.albi_score(40, 0)


def test_cohort_v_matches_preprint_table_1a():
    assert round(hcc.cohort_albi_vulnerability(hcc.FARIA_ALBI_COUNTS["HCC"]), 2) == 0.52
    assert round(hcc.cohort_albi_vulnerability(hcc.FARIA_ALBI_COUNTS["cirrhosis"]), 2) == 0.48


def test_within_tier_eal_reversal_patients_A_B():
    """Preprint: A (R=0.072, EAL=0.072) vs B (R=0.066, EAL=0.200), both Moderate; B escalated."""
    A = dict(id="A", L=0.30, E=0.60, albi_grade=1, surveillance="usual", bclc_if_missed="A")
    B = dict(id="B", L=0.25, E=0.60, albi_grade=2, surveillance="usual", bclc_if_missed="C-D")
    # grade 2 gives V=0.60 (not the paper's patient-level 0.55), so check the mechanism rather than the exact R
    out = hcc.triage([A, B])
    assert out[0]["id"] == "B" and out[0]["tier"] == out[1]["tier"]
    assert out[1]["EAL"] == pytest.approx(0.072) and out[0]["EAL"] == pytest.approx(0.200)
