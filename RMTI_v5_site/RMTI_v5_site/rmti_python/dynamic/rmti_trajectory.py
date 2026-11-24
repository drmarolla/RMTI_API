# Copyright 2026 Cesar Marolla
# Licensed under the Apache License, Version 2.0 (see the LICENSE file in this repository).
"""
rmti_trajectory.py -- time-indexed layer for RMTI:  R(t) = L(t) * E * V*(t) * [1 - rho(t)].

STATUS: this file is a thin adapter, written from the equations documented in
oncology/rmti_elasticity.py. The original dynamic/rmti_dynamic.py was not in the
archive it was written against. If you have that file, replace the body of
run_trajectory() with a call into it. The returned row keys ('V', 'rho', per
cycle) are the ones oncology.rmti_elasticity.trajectory_decomposition() expects.

It adds NO scoring math. Every R, tier and EAL value comes from core.rmti_core.score().
What it adds is the V*(t) mapping and the alpha-beta filter:

    level, slope  <- alpha-beta filter on the observed drive y (steady-state gains)
        pred  = level + slope
        resid = y - pred
        level = pred + alpha * resid
        slope = slope + beta * resid
    d     = level + look_ahead * slope        (filter on)   |   d = y   (filter off)
    V*    = v_lo + (v_hi - v_lo) * clip(d, 0, y_max) / y_max

Defaults: alpha 0.41, beta 0.09 (steady-state gains), v_lo/v_hi 0.35/0.85 (the ALBI grade 1
and grade 3 anchors in oncology.rmti_hcc.ALBI_V), y_max 10 (as in the rmti_elasticity demo).
Research prototype. Synthetic inputs only. Not validated, not a medical device.
"""
from __future__ import annotations

import os
import sys
from typing import Dict, List, Sequence, Union

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from core.rmti_core import score  # noqa: E402

__all__ = ["run_trajectory", "DEFAULTS"]

DEFAULTS = dict(alpha=0.41, beta=0.09, look_ahead=1.0, v_lo=0.35, v_hi=0.85, y_max=10.0)


def _per_cycle(name: str, x: Union[float, Sequence[float]], n: int) -> List[float]:
    if isinstance(x, (int, float)):
        return [float(x)] * n
    x = [float(v) for v in x]
    if len(x) != n:
        raise ValueError(f"{name} has {len(x)} values; expected {n} (one per cycle)")
    return x


def run_trajectory(y: Sequence[float], rho: Sequence[float], L: Union[float, Sequence[float]],
                   E: float, *, C: int = 5, alpha: float = DEFAULTS["alpha"],
                   beta: float = DEFAULTS["beta"], look_ahead: float = DEFAULTS["look_ahead"],
                   v_lo: float = DEFAULTS["v_lo"], v_hi: float = DEFAULTS["v_hi"],
                   y_max: float = DEFAULTS["y_max"], use_filter: bool = True,
                   cycle_months: int = 6) -> List[Dict[str, float]]:
    """One row per surveillance cycle. y = observed vulnerability drive (0..y_max),
    rho = surveillance adequacy per cycle, L = scalar or per-cycle likelihood."""
    n = len(y)
    if n < 2:
        raise ValueError("a trajectory needs at least 2 cycles")
    if not (0.0 <= v_lo < v_hi <= 1.0) or y_max <= 0:
        raise ValueError("need 0 <= v_lo < v_hi <= 1 and y_max > 0")
    if not (0.0 < alpha <= 1.0 and 0.0 <= beta <= 2.0):
        raise ValueError("need 0 < alpha <= 1 and 0 <= beta <= 2")
    ys, rhos, Ls = [float(v) for v in y], _per_cycle("rho", rho, n), _per_cycle("L", L, n)
    level, slope, rows = ys[0], 0.0, []
    for k in range(n):
        if k > 0:
            pred = level + slope
            resid = ys[k] - pred
            level, slope = pred + alpha * resid, slope + beta * resid
        d = level + look_ahead * slope if use_filter else ys[k]
        v_star = v_lo + (v_hi - v_lo) * min(max(d, 0.0), y_max) / y_max
        s = score(Ls[k], E, v_star, rhos[k], C)
        rows.append({"cycle": k, "month": k * cycle_months, "y": ys[k], "level": level, "slope": slope,
                     "d": d, "V": v_star, "rho": rhos[k], "L": Ls[k], "R": s["R"], "R_raw": s["R_raw"],
                     "IR_raw": s["IR_raw"], "EAL_raw": s["EAL_raw"], "tier": s["tier"]})
    return rows
