"""Budget allocation. Costs are the paper's $50M benchmark per city; all deltas rest on assumed rho_after."""
from rmti import optimize_portfolio, project_from_inputs, budget_frontier
from rmti.domains import urban

projects = [project_from_inputs(n, 50, c["N"], c["L"], c["E_sel"], c["V"], c["rho_now"], c["rho_after"], c["C"])
            for n, c in urban.COHORT.items() if "rho_after" in c]
for obj in ("delta_R", "delta_EAL", "delta_equity"):
    r = optimize_portfolio(projects, 100, obj)
    print(f"{obj:13} -> {r.selected}  value={r.objective_value:.3f}  (greedy {r.greedy_value:.3f})")
print([(f["budget"], round(f["value"], 3)) for f in budget_frontier(projects, [0, 50, 100, 150])])
