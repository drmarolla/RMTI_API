import math
import numpy as np
import pytest
import rmti
from rmti import core
from rmti.domains import urban


def test_lagos_scalar_matches_paper():
    r = core.assess(**urban.COHORT["Lagos"])
    assert (r["R_now"], r["R_after"], r["EAL_now"]) == (0.374, 0.211, 0.720)
    assert r["tier_now"] == "Tier 4 - Severe" and r["tier_after"] == "Tier 3 - High"
    assert r["risk_reduction_pct"] == 43.8


def test_decimal_rounding_half_up():
    # 0.30*0.65*0.60*0.5 is 0.058499999... in binary float; the paper reports 0.058/0.059 boundary cases
    assert core.score(0.30, 0.65, 0.60, 0.5)["R"] == 0.059


@pytest.mark.parametrize("R,idx", [(0.0, 0), (0.0499, 0), (0.05, 1), (0.15, 2), (0.35, 3), (0.5999, 3), (0.60, 4), (1.0, 4)])
def test_tier_boundaries_lower_inclusive(R, idx):
    assert int(core.tier_index(R)) == idx
    assert core.tier(R) == core.TIER_LABELS[idx]


def test_vectorised_equals_scalar():
    rng = np.random.default_rng(0)
    L, E, V, rho = rng.uniform(0, 1, (4, 500))
    v = core.score_array(L, E, V, rho)
    for i in range(500):
        assert core.tier(v["R"][i]) == core.TIER_LABELS[v["tier_index"][i]]


def test_e_log_lilongwe_walkthrough():
    assert round(core.e_log(1_100_000), 3) == 0.800
    assert core.e_log_clipped(5) == 0.0


def test_input_validation():
    with pytest.raises(ValueError):
        core.score(1.2, 0.5, 0.5, 0.5)
    with pytest.raises(ValueError):
        core.score(0.5, 0.5, 0.5, 0.5, C=9)


def test_boundary_margins_reproduce_table8_lagos():
    c = urban.COHORT["Lagos"]
    m = core.boundary_margins(c["L"], c["E_sel"], c["V"], c["rho_now"])
    assert m["lower_threshold"] == 0.35
    assert m["rel_change_LEV_to_lower"] == pytest.approx(0.35 / 0.3744 - 1)  # about -6.5%: a 10% error flips it
    assert m["rel_change_LEV_to_lower"] > -0.10
    # rho needs a much larger error: 0.20 -> 0.252 (+0.052 absolute, +26% relative) to cross 0.35.
    assert m["delta_rho_to_lower"] == pytest.approx(1 - 0.35 / 0.468 - 0.20)
    # Correct +/-10% rho perturbation (elasticity -rho/(1-rho)): R = 0.468*(1-0.22) = 0.365 -> still Tier 4.
    # (Table 8 of the IJMADA paper shows 0.336 / 'flips', which scales R by 10% instead.)
    assert core.tier(0.468 * (1 - 0.22)) == "Tier 4 - Severe"
    assert core.tier(0.468 * (1 - 0.18)) == "Tier 4 - Severe"
    b = urban.COHORT["Bamako"]
    mb = core.boundary_margins(b["L"], b["E_sel"], b["V"], b["rho_now"])
    assert mb["rel_change_LEV_to_lower"] < -0.10     # robust to 10%


def test_multi_weights_enforced():
    with pytest.raises(ValueError):
        core.check_weights({"social": 0.5, "economic": 0.3, "environmental": 0.3})


def test_multi_reduces_to_single_when_one_hazard_equal_categories():
    cat = {"E": 0.65, "V": 0.8, "rho": 0.2}
    h = [{"name": "x", "L": 0.9, "categories": {c: cat for c in core.CATEGORIES}, "rho_hazard": 0.2, "C": 5}]
    res = core.score_multi(h, {"social": 0.4, "economic": 0.3, "environmental": 0.3})
    assert res["R"] == 0.374 and res["EAL"] == 0.720
