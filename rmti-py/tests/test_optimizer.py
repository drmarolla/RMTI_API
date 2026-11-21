import itertools
import pytest
from rmti import Project, optimize_portfolio, project_from_inputs, budget_frontier
from rmti.domains import urban


def brute(projects, budget, key):
    best = 0
    for k in range(len(projects) + 1):
        for combo in itertools.combinations(projects, k):
            groups = [p.group for p in combo if p.group]
            if len(groups) != len(set(groups)) or sum(p.cost for p in combo) > budget:
                continue
            best = max(best, sum(key(p) for p in combo))
    return best


def make():
    return [Project("A", 50, 0.40, 0.20), Project("B", 40, 0.30, 0.12), Project("C", 30, 0.25, 0.15),
            Project("D", 20, 0.20, 0.14), Project("A2", 25, 0.40, 0.32, group="cityA"),
            Project("A3", 45, 0.40, 0.22, group="cityA")]


@pytest.mark.parametrize("budget", [20, 45, 70, 100, 150, 400])
def test_matches_brute_force(budget):
    ps = make()
    r = optimize_portfolio(ps, budget)
    assert r.objective_value == pytest.approx(brute(ps, budget, lambda p: p.delta_R))
    assert r.total_cost <= budget + 1e-9


def test_mutually_exclusive_groups_respected():
    r = optimize_portfolio([Project("x1", 10, 0.5, 0.2, group="g"), Project("x2", 10, 0.5, 0.25, group="g")], 100)
    assert len(r.selected) == 1 and r.selected == ["x1"]


def test_beats_or_ties_greedy_and_knapsack_trap():
    # greedy by ratio picks the small one first and blocks the pair that is jointly better
    ps = [Project("big", 10, 1.0, 0.0), Project("s1", 6, 0.55, 0.0), Project("s2", 5, 0.45, 0.0)]
    r = optimize_portfolio(ps, 11)
    assert set(r.selected) == {"s1", "s2"} or r.objective_value >= r.greedy_value
    assert r.gain_over_greedy >= -1e-12


def test_mandatory_and_infeasible():
    ps = make()
    assert "D" in optimize_portfolio(ps, 100, mandatory=["D"]).selected
    with pytest.raises(ValueError):
        optimize_portfolio(ps, 10, mandatory=["A"])
    with pytest.raises(ValueError):
        optimize_portfolio(ps, 10, mandatory=["nope"])


def test_equity_objective_changes_choice_and_needs_fields():
    big = project_from_inputs("big", 50, 16_000_000, 0.9, 0.65, 0.8, 0.2, 0.55, 5)
    small = project_from_inputs("small", 50, 1_100_000, 0.875, 0.8, 0.8, 0.25, 0.48, 4)
    assert optimize_portfolio([big, small], 50, "delta_R").selected == ["big"]     # dR 0.163 vs 0.129
    assert optimize_portfolio([big, small], 50, "delta_EAL").selected == ["big"]   # dEAL 0.315 vs 0.151
    assert optimize_portfolio([big, small], 50, "delta_equity").selected == ["small"]
    with pytest.raises(ValueError):
        optimize_portfolio([Project("p", 1, 0.3, 0.1)], 5, "delta_equity")


def test_frontier_monotone_and_unique_names():
    f = budget_frontier(make(), [0, 25, 50, 100, 200])
    vals = [r["value"] for r in f]
    assert vals == sorted(vals) and vals[0] == 0
    with pytest.raises(ValueError):
        optimize_portfolio([Project("d", 1, .3, .1), Project("d", 1, .3, .1)], 5)


def test_paper_scale_example():
    ps = [project_from_inputs(n, 50, c["N"], c["L"], c["E_sel"], c["V"], c["rho_now"], c["rho_after"], c["C"])
          for n, c in urban.COHORT.items() if "rho_after" in c]
    r = optimize_portfolio(ps, 100)
    assert len(r.selected) == 2 and r.total_cost == 100
