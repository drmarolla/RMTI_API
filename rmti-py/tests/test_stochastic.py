import numpy as np
import pytest
from scipy import stats
from rmti import UncertainParam as U, simulate_rmti, woe_sensitivity
from rmti.domains import urban


def lagos(grade, **kw):
    c = urban.COHORT["Lagos"]
    return simulate_rmti(U(c["L"], grade), U(c["E_sel"], grade), U(c["V"], grade), U(c["rho_now"], grade), **kw)


def test_reproducible_with_seed():
    assert (lagos("w_ic").R == lagos("w_ic").R).all()
    assert not (lagos("w_ic", seed=1).R == lagos("w_ic", seed=2).R).all()


def test_mean_equals_point_estimate_when_independent():
    r = lagos("w_ic", n_sims=200_000)
    assert r.R.mean() == pytest.approx(r.point_R, abs=2e-3)


def test_zero_spread_collapses_to_point():
    c = urban.COHORT["Lagos"]
    r = simulate_rmti(*(U(c[k], sd=0) for k in ("L", "E_sel", "V", "rho_now")), n_sims=1000)
    assert r.p_point_tier == 1.0 and r.R.std() < 1e-12


def test_weaker_evidence_lowers_confidence_in_point_tier():
    p = woe_sensitivity(0.9, 0.65, 0.8, 0.2)
    assert p["w_ia"] > p["w_ic"] > p["w_if"]
    assert p["w_if"] < 0.8               # tier assignment is NOT robust under very weak evidence


def test_tier_probabilities_sum_to_one_and_labels_complete():
    tp = lagos("w_id").tier_probabilities
    assert sum(tp.values()) == pytest.approx(1.0) and len(tp) == 5


def test_explicit_sd_and_validation():
    assert U(0.5, sd=0.1).concentration == pytest.approx(0.25 / 0.01 - 1)
    with pytest.raises(ValueError):
        U(0.5, sd=0.6)
    with pytest.raises(ValueError):
        U(0.5, "w_zz")
    with pytest.raises(ValueError):
        U(1.5)


def test_scenario_pairing_and_improvement():
    c = urban.COHORT["Lagos"]
    r = lagos("w_ic", rho_after=U(c["rho_after"], "w_ic"), n_sims=20_000)
    assert r.R_after.mean() < r.R.mean()
    assert 0.5 < r.p_tier_improves <= 1.0
    s = r.summary()
    assert s["reduction_ci_95"][0] < 0.438 < s["reduction_ci_95"][1]


def test_gaussian_copula_induces_requested_dependence():
    base = [U(0.5, "w_ia")] * 4
    corr = np.eye(4)
    corr[0, 2] = corr[2, 0] = 0.8          # L and V
    rng_check = simulate_rmti(*base, correlation=corr, n_sims=30_000)
    # recover L,V correlation through the R distribution's inflation vs. independent case
    ind = simulate_rmti(*base, n_sims=30_000)
    assert rng_check.R.std() > ind.R.std()
    with pytest.raises(ValueError):
        simulate_rmti(*base, correlation=np.ones((4, 4)) * 0.5 + np.eye(4) * 0.5 - 2 * np.eye(4))  # not PD


def test_copula_preserves_marginals():
    from rmti.stochastic import _draw
    corr = np.eye(4); corr[0, 1] = corr[1, 0] = 0.7
    p = [U(0.3, "w_ic"), U(0.6, "w_ic"), U(0.5, "w_ia"), U(0.2, "w_id")]
    d = _draw(p, 60_000, np.random.default_rng(3), corr)
    for i, q in enumerate(p):
        assert d[:, i].mean() == pytest.approx(q.mean, abs=0.01)
    assert stats.spearmanr(d[:, 0], d[:, 1])[0] > 0.6
