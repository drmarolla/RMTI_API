# Copyright 2025-2026 Cesar Marolla. Apache-2.0.
"""Budget-constrained selection of resilience projects (0/1 MILP via scipy).

    maximise   sum_i  b_i x_i
    subject to sum_i  cost_i x_i <= budget
               sum_{i in group g} x_i <= 1      (alternative packages for one asset/city)
               x_i in {0, 1}

Interpretation caveats (please carry these into any report):
* R is a *relative index*, not a probability or a monetary loss. Summing
  delta-R across heterogeneous assets assumes they are commensurable; that is a
  normative choice, not a property of the index.
* rho_after (hence every delta) is a scenario assumption unless backed by
  engineering evidence. Optimal portfolios inherit that uncertainty; run them
  over Monte Carlo draws of rho_after if the ranking matters.
* The equity objective is delta-EAL per million residents (Eq. 7 applied to the
  *reduction*), so it requires N and EAL fields.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Union

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

from .core import score


@dataclass(frozen=True)
class Project:
    name: str
    cost: float
    R_now: float
    R_after: float
    group: Optional[str] = None          # projects sharing a group are mutually exclusive
    N: Optional[float] = None
    EAL_now: Optional[float] = None
    EAL_after: Optional[float] = None

    def __post_init__(self):
        if self.cost < 0:
            raise ValueError(f"{self.name}: cost must be >= 0")

    @property
    def delta_R(self) -> float:
        return self.R_now - self.R_after

    @property
    def delta_EAL(self) -> float:
        if self.EAL_now is None or self.EAL_after is None:
            raise ValueError(f"{self.name}: EAL_now/EAL_after required for this objective")
        return self.EAL_now - self.EAL_after

    @property
    def delta_equity(self) -> float:
        if self.N is None:
            raise ValueError(f"{self.name}: N required for the equity objective")
        return self.delta_EAL / (self.N / 1e6)


def project_from_inputs(name: str, cost: float, N: float, L: float, E_sel: float, V: float,
                        rho_now: float, rho_after: float, C: int = 5, group: Optional[str] = None) -> Project:
    """Build a Project from RMTI inputs (unrounded R and EAL)."""
    a, b = score(L, E_sel, V, rho_now, C), score(L, E_sel, V, rho_after, C)
    return Project(name, cost, a["R_raw"], b["R_raw"], group, N, a["EAL_raw"], b["EAL_raw"])


Objective = Union[str, Callable[[Project], float]]


def _benefit(p: Project, objective: Objective) -> float:
    if callable(objective):
        return float(objective(p))
    if objective in ("delta_R", "delta_EAL", "delta_equity"):
        return float(getattr(p, objective))
    raise ValueError("objective must be 'delta_R', 'delta_EAL', 'delta_equity' or a callable")


@dataclass
class PortfolioResult:
    selected: List[str]
    total_cost: float
    budget: float
    objective: str
    objective_value: float
    total_delta_R: float
    greedy_value: float
    success: bool
    message: str = ""

    @property
    def unspent(self) -> float:
        return self.budget - self.total_cost

    @property
    def gain_over_greedy(self) -> float:
        return self.objective_value - self.greedy_value


def _greedy(projects, b, budget, groups):
    order = sorted(range(len(projects)), key=lambda i: -(b[i] / projects[i].cost if projects[i].cost > 0 else np.inf))
    spent, used, val = 0.0, set(), 0.0
    for i in order:
        g = projects[i].group
        if b[i] <= 0 or spent + projects[i].cost > budget + 1e-9 or (g is not None and g in used):
            continue
        spent += projects[i].cost
        val += b[i]
        if g is not None:
            used.add(g)
    return val


def optimize_portfolio(projects: Sequence[Project], budget: float, objective: Objective = "delta_R",
                       mandatory: Iterable[str] = (), max_projects: Optional[int] = None) -> PortfolioResult:
    """Select the project set that maximises the objective within ``budget``."""
    projects = list(projects)
    if not projects:
        raise ValueError("no projects supplied")
    names = [p.name for p in projects]
    if len(set(names)) != len(names):
        raise ValueError("project names must be unique")
    n = len(projects)
    cost = np.array([p.cost for p in projects], dtype=float)
    b = np.array([_benefit(p, objective) for p in projects], dtype=float)

    rows, lbs, ubs = [cost], [0.0], [budget]
    for g in sorted({p.group for p in projects if p.group is not None}):
        rows.append(np.array([1.0 if p.group == g else 0.0 for p in projects]))
        lbs.append(0.0)
        ubs.append(1.0)
    if max_projects is not None:
        rows.append(np.ones(n))
        lbs.append(0.0)
        ubs.append(float(max_projects))
    lb = np.zeros(n)
    unknown = set(mandatory) - set(names)
    if unknown:
        raise ValueError(f"mandatory projects not found: {sorted(unknown)}")
    for m in mandatory:
        lb[names.index(m)] = 1.0

    res = milp(c=-b, integrality=np.ones(n), bounds=Bounds(lb, np.ones(n)),
               constraints=LinearConstraint(np.vstack(rows), lbs, ubs))
    if not res.success or res.x is None:
        raise ValueError(f"no feasible portfolio (mandatory projects may exceed the budget): {res.message}")
    x = np.round(res.x).astype(int)
    sel = [names[i] for i in range(n) if x[i] == 1]
    return PortfolioResult(selected=sel, total_cost=float(cost @ x), budget=float(budget),
                           objective=objective if isinstance(objective, str) else getattr(objective, "__name__", "custom"),
                           objective_value=float(b @ x),
                           total_delta_R=float(sum(projects[i].delta_R for i in range(n) if x[i])),
                           greedy_value=float(_greedy(projects, b, budget, None)), success=True, message=res.message)


def budget_frontier(projects: Sequence[Project], budgets: Iterable[float], objective: Objective = "delta_R") -> List[Dict]:
    """Optimal value across a range of budgets (diminishing-returns curve)."""
    out = []
    for B in budgets:
        r = optimize_portfolio(projects, B, objective)
        out.append({"budget": B, "value": r.objective_value, "cost": r.total_cost, "selected": r.selected})
    return out
