# Copyright 2026 Cesar Marolla
# Licensed under the Apache License, Version 2.0 (see the LICENSE file in this repository).
"""
rmti_elasticity.py -- elasticities of the Risk Mechanism Theory Index (RMTI),
and their relation to the time-indexed layer.

RESEARCH PROTOTYPE. Nothing here is validated against outcomes. All examples
are synthetic. Not a medical device.

This module adds NO new model equation. It evaluates properties that follow
from R = L * E * V * (1 - rho) (Equation 2) by taking logarithms and
differentiating, and from the V*(t) mapping of the time-indexed layer.

Elasticity of R with respect to a term X (others held fixed):

    eps_X = (dR/dX) * (X / R) = d ln R / d ln X

Results (all tested against numerical differentiation):

    eps_L = eps_E = eps_V = 1
    eps_rho = -rho / (1 - rho)                       # for rho in [0, 1)
    eps_rho_care = -rho_care / (1 - rho_care)        # rho_bio fixed (and vice versa)
    EAL = L * C * (1 - rho):  eps_L = eps_C = 1,  eps_rho = -rho / (1 - rho)

Logarithm of Equation 2 (a product becomes a sum):

    ln R = ln L + ln E + ln V + ln(1 - rho)

so the change in ln R between two states is the sum of the changes in the
four logs (log_decomposition), and, in the time-indexed layer, R(t) has the
same elasticities at each cycle.

Relation to the time-indexed layer (rmti_dynamic.py, Marolla 2026d):

    V*(t) = v_lo + (v_hi - v_lo) * clip(d, 0, y_max) / y_max,
    d = level + look_ahead * slope  (filter on)  or the observed y  (filter off)

With k = (v_hi - v_lo) / y_max and the clip inactive,

    eps_d = k * d / (v_lo + k * d)   (below 1, because V* has a floor v_lo)

Caveats: elasticities are local; they assume the other terms are fixed and
independent; they say nothing about cost or whether a term can be changed;
and R is a relative index, not a probability.
"""
import math
from typing import Callable, Dict, Iterable, List, Mapping

__all__ = [
    "elasticities", "elasticity_rho", "elasticity_rho_component", "eal_elasticities",
    "relative_change_in_R", "relative_R_error_from_rho_error", "log_decomposition",
    "elasticity_wrt_drive", "trajectory_decomposition", "numerical_elasticity",
]


def _check_unit(name: str, x: float, open_lower: bool = False) -> None:
    ok = (0.0 < x <= 1.0) if open_lower else (0.0 <= x <= 1.0)
    if not ok:
        raise ValueError(f"{name} must lie in {'(0, 1]' if open_lower else '[0, 1]'}; got {x}")


def _check_rho(name: str, x: float) -> None:
    if not 0.0 <= x < 1.0:
        raise ValueError(f"{name} must lie in [0, 1); got {x}")


def elasticity_rho(rho: float) -> float:
    """Elasticity of R with respect to rho: -rho / (1 - rho)."""
    _check_rho("rho", rho)
    return -rho / (1.0 - rho)


def elasticity_rho_component(rho_component: float) -> float:
    """Elasticity of R with respect to rho_bio (rho_care fixed) or rho_care
    (rho_bio fixed). Because 1 - rho = (1 - rho_bio)(1 - rho_care), R is
    proportional to (1 - rho_component), so the form is the same as for rho."""
    _check_rho("rho_component", rho_component)
    return -rho_component / (1.0 - rho_component)


def elasticities(L: float, E: float, V: float, rho: float) -> Dict[str, float]:
    """Elasticities of R = L * E * V * (1 - rho). The values for L, E and V do
    not depend on the inputs; they are returned with the inputs validated."""
    for n, x in (("L", L), ("E", E), ("V", V)):
        _check_unit(n, x, open_lower=True)
    return {"L": 1.0, "E": 1.0, "V": 1.0, "rho": elasticity_rho(rho)}


def eal_elasticities(L: float, C: float, rho: float) -> Dict[str, float]:
    """Elasticities of EAL = L * C * (1 - rho)."""
    _check_unit("L", L, open_lower=True)
    _check_unit("C", C, open_lower=True)
    return {"L": 1.0, "C": 1.0, "rho": elasticity_rho(rho)}


def relative_change_in_R(rho: float, rho_new: float) -> float:
    """Exact relative change in R when only rho changes: (1 - rho_new)/(1 - rho) - 1."""
    _check_rho("rho", rho)
    _check_rho("rho_new", rho_new)
    return (1.0 - rho_new) / (1.0 - rho) - 1.0


def relative_R_error_from_rho_error(rho: float, delta: float) -> float:
    """Exact relative change in R for an absolute change delta in rho:
    -delta / (1 - rho). A 0.05 error at rho = 0.2 is about 6%, at 0.8 about 25%."""
    _check_rho("rho", rho)
    _check_rho("rho + delta", rho + delta)
    return -delta / (1.0 - rho)


def log_decomposition(state1: Mapping[str, float], state2: Mapping[str, float]) -> Dict[str, float]:
    """Attribute the change in R between two states, each a mapping with keys
    L, E, V, rho, to its terms: ln R2 - ln R1 = dlnL + dlnE + dlnV + dln(1-rho)."""
    def terms(s):
        for n in ("L", "E", "V"):
            _check_unit(n, s[n], open_lower=True)
        _check_rho("rho", s["rho"])
        return {"L": math.log(s["L"]), "E": math.log(s["E"]), "V": math.log(s["V"]),
                "1-rho": math.log(1.0 - s["rho"])}
    a, b = terms(state1), terms(state2)
    d = {f"dln_{k}": b[k] - a[k] for k in a}
    d["total_dlnR"] = sum(d.values())
    d["pct_change_R"] = 100.0 * math.expm1(d["total_dlnR"])
    return d


def elasticity_wrt_drive(drive: float, v_lo: float, v_hi: float, y_max: float) -> float:
    """eps_d = k*d / (v_lo + k*d), k = (v_hi - v_lo)/y_max, for the time-indexed
    mapping V* = v_lo + k*clip(d, 0, y_max). Returns 0.0 where the clip is active."""
    if not (0.0 <= v_lo < v_hi <= 1.0) or y_max <= 0:
        raise ValueError("need 0 <= v_lo < v_hi <= 1 and y_max > 0")
    if drive <= 0.0 or drive >= y_max:
        return 0.0
    k = (v_hi - v_lo) / y_max
    return k * drive / (v_lo + k * drive)


def trajectory_decomposition(rows: Iterable[Mapping[str, float]], L: float, E: float) -> List[Dict[str, float]]:
    """Cycle-to-cycle attribution of R(t) for the rows returned by
    dynamic.rmti_dynamic.run_trajectory (keys 'V' and 'rho' per cycle; L and E
    are constant in that layer). Returns one dict per consecutive pair."""
    rows = list(rows)
    out = []
    for i in range(1, len(rows)):
        s1 = {"L": L, "E": E, "V": rows[i - 1]["V"], "rho": rows[i - 1]["rho"]}
        s2 = {"L": L, "E": E, "V": rows[i]["V"], "rho": rows[i]["rho"]}
        d = log_decomposition(s1, s2)
        d["cycle"] = i
        out.append(d)
    return out


def numerical_elasticity(f: Callable[[float], float], x: float, h: float = 1e-6) -> float:
    """Central-difference elasticity d ln f / d ln x, for checking closed forms."""
    return (math.log(f(x * (1 + h))) - math.log(f(x * (1 - h)))) / (math.log(1 + h) - math.log(1 - h))


def _demo() -> None:
    print("rmti_elasticity demo -- synthetic inputs, research prototype\n")
    for rho in (0.2, 0.5, 0.8):
        print(f"rho = {rho:.1f}: eps_rho = {elasticity_rho(rho):+.2f};  "
              f"10% relative rise in rho changes R by {100 * relative_change_in_R(rho, 1.1 * rho):+.1f}%")
    print(f"error of 0.05 in rho at rho 0.2 -> {100 * relative_R_error_from_rho_error(0.2, 0.05):+.1f}% in R; "
          f"at rho 0.8 -> {100 * relative_R_error_from_rho_error(0.8, 0.05):+.1f}%")
    print(f"eps_d at d = 8 (v_lo 0.35, v_hi 0.85, y_max 10) = {elasticity_wrt_drive(8, 0.35, 0.85, 10):.2f}")
    d = log_decomposition({"L": .25, "E": .6, "V": .769, "rho": .3}, {"L": .25, "E": .6, "V": .647, "rho": .3})
    print(f"V* 0.769 -> 0.647 with L, E, rho fixed: R changes {d['pct_change_R']:+.1f}% (equal to the change in V*)")


if __name__ == "__main__":
    _demo()
