# Copyright 2026 Cesar Marolla
# Licensed under the Apache License, Version 2.0 (see the LICENSE file in this repository).
"""Tests for rmti_elasticity.py. Run from this folder:

    python -m unittest -v test_rmti_elasticity

The integration test uses the time-indexed reference implementation if it can
be imported. Point RMTI_PY_PATH at the folder that contains dynamic/ (for
example the rmti-python folder of the archived release); otherwise it is skipped.
"""
import itertools
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rmti_elasticity as el  # noqa: E402

RHOS = [0.0, 0.1, 0.2, 0.35, 0.5, 0.65, 0.8, 0.9]


def R(L, E, V, rho):
    return L * E * V * (1 - rho)


def combine(rb, rc):
    return 1 - (1 - rb) * (1 - rc)


class ClosedForms(unittest.TestCase):
    def test_L_E_V_are_one(self):
        base = dict(L=0.25, E=0.6, V=0.5, rho=0.3)
        for k in ("L", "E", "V"):
            f = lambda x, k=k: R(**{**base, k: x})
            self.assertAlmostEqual(el.numerical_elasticity(f, base[k]), 1.0, places=6)
            self.assertEqual(el.elasticities(**base)[k], 1.0)

    def test_rho_matches_numerical(self):
        for rho in RHOS[1:]:
            f = lambda x: R(0.25, 0.6, 0.5, x)
            self.assertAlmostEqual(el.numerical_elasticity(f, rho), el.elasticity_rho(rho), places=4)

    def test_reference_values(self):
        self.assertAlmostEqual(el.elasticity_rho(0.2), -0.25)
        self.assertAlmostEqual(el.elasticity_rho(0.5), -1.0)
        self.assertAlmostEqual(el.elasticity_rho(0.8), -4.0)

    def test_component_elasticity(self):
        rb, rc = 0.30, 0.50
        f = lambda x: R(0.25, 0.6, 0.5, combine(rb, x))
        self.assertAlmostEqual(el.numerical_elasticity(f, rc), el.elasticity_rho_component(rc), places=4)
        g = lambda x: R(0.25, 0.6, 0.5, combine(x, rc))
        self.assertAlmostEqual(el.numerical_elasticity(g, rb), el.elasticity_rho_component(rb), places=4)

    def test_eal(self):
        e = el.eal_elasticities(0.25, 0.75, 0.4)
        f = lambda x: 0.25 * 0.75 * (1 - x)
        self.assertEqual((e["L"], e["C"]), (1.0, 1.0))
        self.assertAlmostEqual(el.numerical_elasticity(f, 0.4), e["rho"], places=4)


class ErrorPropagation(unittest.TestCase):
    def test_relative_change_exact(self):
        self.assertAlmostEqual(el.relative_change_in_R(0.2, 0.22), 0.78 / 0.80 - 1)
        self.assertAlmostEqual(el.relative_change_in_R(0.65, 0.715), -0.185714285714, places=9)

    def test_ten_percent_rise_equals_eps_times_ten_percent(self):
        for rho in RHOS[1:]:
            self.assertAlmostEqual(el.relative_change_in_R(rho, 1.1 * rho) if 1.1 * rho < 1 else 0.0,
                                   0.1 * el.elasticity_rho(rho) if 1.1 * rho < 1 else 0.0, places=9)

    def test_absolute_rho_error(self):
        self.assertAlmostEqual(el.relative_R_error_from_rho_error(0.2, 0.05), -0.0625)
        self.assertAlmostEqual(el.relative_R_error_from_rho_error(0.8, 0.05), -0.25, places=9)


class LogDecomposition(unittest.TestCase):
    def test_sum_of_logs_equals_change_in_lnR(self):
        s1 = dict(L=0.25, E=0.5, V=0.6, rho=0.3)
        s2 = dict(L=0.30, E=0.4, V=0.5, rho=0.45)
        d = el.log_decomposition(s1, s2)
        self.assertAlmostEqual(d["total_dlnR"], math.log(R(**s2)) - math.log(R(**s1)), places=12)
        self.assertAlmostEqual(d["pct_change_R"], 100 * (R(**s2) / R(**s1) - 1), places=9)

    def test_only_V_moves(self):
        d = el.log_decomposition(dict(L=.25, E=.6, V=.769, rho=.3), dict(L=.25, E=.6, V=.647, rho=.3))
        self.assertAlmostEqual(d["pct_change_R"], 100 * (.647 / .769 - 1), places=9)   # -15.9%


class TimeIndexedRelation(unittest.TestCase):
    V_LO, V_HI, Y_MAX = 0.35, 0.85, 10.0

    def V(self, d):
        return self.V_LO + (self.V_HI - self.V_LO) * min(max(d, 0.0), self.Y_MAX) / self.Y_MAX

    def test_drive_elasticity_matches_numerical(self):
        for d in (1.0, 4.0, 8.0, 9.5):
            f = lambda x: R(0.25, 0.6, self.V(x), 0.3)
            self.assertAlmostEqual(el.numerical_elasticity(f, d), el.elasticity_wrt_drive(d, self.V_LO, self.V_HI, self.Y_MAX), places=4)

    def test_below_one_and_value_at_8(self):
        e = el.elasticity_wrt_drive(8.0, self.V_LO, self.V_HI, self.Y_MAX)
        self.assertLess(e, 1.0)
        self.assertAlmostEqual(e, 0.4 / 0.75, places=12)          # about 0.53

    def test_zero_when_clipped(self):
        self.assertEqual(el.elasticity_wrt_drive(10.0, self.V_LO, self.V_HI, self.Y_MAX), 0.0)

    def test_integration_with_reference_implementation(self):
        path = os.environ.get("RMTI_PY_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "rmti-python"))
        sys.path.insert(0, path)
        try:
            from dynamic.rmti_dynamic import run_trajectory, DISASTER_PARAMS
        except Exception as exc:                                    # pragma: no cover
            self.skipTest(f"reference implementation not found ({exc})")
        obs = [3, 3.5, 4, 4.5, 5, 5.5, 6, 6.5, 7, 7.5, 8, 7.0, 6.5, 6.0, 5.8, 5.5]
        rows = run_trajectory(L=0.25, E=0.60, C=3, rho0=0.30, observations=obs,
                              delivery=[0.5] * len(obs), params=DISASTER_PARAMS)
        steps = el.trajectory_decomposition(rows, L=0.25, E=0.60)
        for s, (a, b) in zip(steps, zip(rows, rows[1:])):
            self.assertAlmostEqual(s["total_dlnR"], math.log(b["R"] / a["R"]), places=2)  # core rounds R
            self.assertAlmostEqual(s["dln_L"], 0.0)
            self.assertAlmostEqual(s["dln_E"], 0.0)
            self.assertAlmostEqual(s["dln_1-rho"], 0.0, places=9)   # rho constant


if __name__ == "__main__":
    unittest.main()
