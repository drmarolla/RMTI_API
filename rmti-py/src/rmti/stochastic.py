# Copyright 2025-2026 Cesar Marolla. Apache-2.0.
"""Monte Carlo propagation of parameter uncertainty into R and tier assignment.

Each of L, E_sel, V, rho is treated as a Beta-distributed quantity centred on
the analyst's point estimate. The spread is set by a *concentration* k
(Beta(mu*k, (1-mu)*k); sd = sqrt(mu(1-mu)/(k+1))). Larger k = tighter.

ASSUMPTION, NOT RESULT: ``WOE_CONCENTRATION`` maps the six Weight-of-Evidence
grades of Marolla (2018, Table 9.3) to k. Table 9.3 is ordinal and gives no
variances, so these numbers are a modelling choice. They are exposed so users
can override them, supply an explicit ``sd`` instead, and run the sensitivity
sweep in :func:`woe_sensitivity`. Tier probabilities are only as defensible as
this mapping; report them with that caveat.

With independent inputs, E[R] equals the point-estimate R exactly (product of
means), so the simulation changes the *tier probabilities* and interval, not
the central value. Dependence (e.g. L and V correlated) can be introduced with
a Gaussian copula via ``correlation=``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Mapping, Optional, Sequence, Tuple

import numpy as np
from scipy import stats

from .core import TIER_LABELS, tier_index

# ASSUMED mapping (see module docstring). w_ia = strongest evidence.
WOE_CONCENTRATION: Dict[str, float] = {
    "w_ia": 100.0, "w_ib": 60.0, "w_ic": 35.0, "w_id": 20.0, "w_ie": 10.0, "w_if": 5.0,
}
PARAM_ORDER = ("L", "E", "V", "rho")


@dataclass(frozen=True)
class UncertainParam:
    """A [0,1] parameter with a mean and an evidence-based or explicit spread.

    Give either ``woe`` (a key of ``WOE_CONCENTRATION``) or an explicit ``sd``
    (which wins). ``sd=0`` fixes the parameter at its mean.
    """
    mean: float
    woe: str = "w_ic"
    sd: Optional[float] = None

    def __post_init__(self):
        if not 0.0 <= self.mean <= 1.0:
            raise ValueError(f"mean must lie in [0, 1]; got {self.mean}")
        if self.sd is None and self.woe not in WOE_CONCENTRATION:
            raise ValueError(f"unknown WoE grade {self.woe!r}; use one of {sorted(WOE_CONCENTRATION)}")
        if self.sd is not None:
            if self.sd < 0:
                raise ValueError("sd must be >= 0")
            if self.sd > 0 and self.sd ** 2 >= self.mean * (1 - self.mean):
                raise ValueError(f"sd={self.sd} is impossible for a Beta with mean {self.mean} "
                                 f"(max {np.sqrt(self.mean * (1 - self.mean)):.3f})")

    @property
    def fixed(self) -> bool:
        return self.sd == 0 or self.mean in (0.0, 1.0)

    @property
    def concentration(self) -> float:
        if self.sd is not None and self.sd > 0:
            return self.mean * (1 - self.mean) / self.sd ** 2 - 1
        return WOE_CONCENTRATION[self.woe]

    def ppf(self, u: np.ndarray) -> np.ndarray:
        """Quantile function (used by the copula and by plain sampling)."""
        if self.fixed:
            return np.full_like(u, self.mean, dtype=float)
        k = self.concentration
        return stats.beta.ppf(u, self.mean * k, (1 - self.mean) * k)

    def sample(self, rng: np.random.Generator, n: int) -> np.ndarray:
        if self.fixed:
            return np.full(n, self.mean)
        k = self.concentration
        return rng.beta(self.mean * k, (1 - self.mean) * k, size=n)


@dataclass
class SimulationResult:
    point_R: float
    point_tier: str
    R: np.ndarray
    tier_probabilities: Dict[str, float]
    n_sims: int
    seed: int
    R_after: Optional[np.ndarray] = None
    tier_probabilities_after: Optional[Dict[str, float]] = None
    p_tier_improves: Optional[float] = None
    reduction: Optional[np.ndarray] = field(default=None, repr=False)

    @staticmethod
    def _ci(x, level=0.95):
        a = (1 - level) / 2 * 100
        return (float(np.percentile(x, a)), float(np.percentile(x, 100 - a)))

    @property
    def p_point_tier(self) -> float:
        """Probability that the simulated tier equals the point-estimate tier."""
        return self.tier_probabilities[self.point_tier]

    @property
    def modal_tier(self) -> str:
        return max(self.tier_probabilities, key=self.tier_probabilities.get)

    def summary(self) -> Dict:
        out = {"R_point": round(self.point_R, 3), "R_mean": round(float(self.R.mean()), 3),
               "R_ci_95": tuple(round(v, 3) for v in self._ci(self.R)),
               "point_tier": self.point_tier, "p_point_tier": round(self.p_point_tier, 3),
               "modal_tier": self.modal_tier,
               "tier_probabilities": {k: round(v, 3) for k, v in self.tier_probabilities.items() if v > 0}}
        if self.R_after is not None:
            out.update({"R_after_mean": round(float(self.R_after.mean()), 3),
                        "R_after_ci_95": tuple(round(v, 3) for v in self._ci(self.R_after)),
                        "tier_probabilities_after": {k: round(v, 3) for k, v in self.tier_probabilities_after.items() if v > 0},
                        "p_tier_improves": round(self.p_tier_improves, 3),
                        "reduction_ci_95": tuple(round(v, 3) for v in self._ci(self.reduction))})
        return out


def _tier_probs(R: np.ndarray) -> Dict[str, float]:
    counts = np.bincount(tier_index(R), minlength=len(TIER_LABELS))
    return {lbl: float(c) / len(R) for lbl, c in zip(TIER_LABELS, counts)}


def _draw(params: Sequence[UncertainParam], n: int, rng, correlation) -> np.ndarray:
    if correlation is None:
        return np.column_stack([p.sample(rng, n) for p in params])
    corr = np.asarray(correlation, dtype=float)
    if corr.shape != (len(params), len(params)) or not np.allclose(corr, corr.T):
        raise ValueError("correlation must be a symmetric (4x4) matrix in order L, E, V, rho")
    np.linalg.cholesky(corr)  # raises if not positive definite
    z = rng.multivariate_normal(np.zeros(len(params)), corr, size=n)
    u = stats.norm.cdf(z)
    return np.column_stack([p.ppf(u[:, i]) for i, p in enumerate(params)])


def simulate_rmti(L: UncertainParam, E_sel: UncertainParam, V: UncertainParam, rho: UncertainParam,
                  rho_after: Optional[UncertainParam] = None, n_sims: int = 20_000, seed: int = 42,
                  correlation: Optional[Sequence[Sequence[float]]] = None) -> SimulationResult:
    """Propagate parameter uncertainty into R, tier probabilities and (optionally)
    the post-investment state.

    The after-state reuses the same L, E, V draws (paired), and draws rho_after
    independently of rho: the gain in resilience is a scenario assumption, so
    treating it as uncertain on its own is the conservative reading.
    ``correlation`` is a 4x4 Gaussian-copula matrix in the order L, E, V, rho.
    """
    rng = np.random.default_rng(seed)
    draws = _draw((L, E_sel, V, rho), n_sims, rng, correlation)
    Ld, Ed, Vd, rd = draws.T
    IR = Ld * Ed * Vd
    R = IR * (1 - rd)
    point = L.mean * E_sel.mean * V.mean * (1 - rho.mean)
    res = SimulationResult(point_R=point, point_tier=TIER_LABELS[int(tier_index(point))], R=R,
                           tier_probabilities=_tier_probs(R), n_sims=n_sims, seed=seed)
    if rho_after is not None:
        ra = rho_after.sample(rng, n_sims)
        R2 = IR * (1 - ra)
        res.R_after = R2
        res.tier_probabilities_after = _tier_probs(R2)
        res.p_tier_improves = float(np.mean(tier_index(R2) < tier_index(R)))
        with np.errstate(divide="ignore", invalid="ignore"):
            res.reduction = np.where(R > 0, 1 - R2 / R, 0.0)
    return res


def woe_sensitivity(L: float, E_sel: float, V: float, rho: float, grades: Sequence[str] = tuple(WOE_CONCENTRATION),
                    n_sims: int = 20_000, seed: int = 42) -> Dict[str, float]:
    """P(point-estimate tier) when *all four* inputs carry the same WoE grade.
    Shows how strongly the tier probability depends on the assumed mapping."""
    return {g: simulate_rmti(UncertainParam(L, g), UncertainParam(E_sel, g), UncertainParam(V, g),
                             UncertainParam(rho, g), n_sims=n_sims, seed=seed).p_point_tier
            for g in grades}
