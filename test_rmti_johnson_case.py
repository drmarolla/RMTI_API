# Copyright 2026 Cesar Marolla. Licensed under the Apache License, Version 2.0.
"""python -m unittest -v test_rmti_johnson_case"""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rmti_johnson_case as jc  # noqa: E402
from rmti_elasticity import elasticity_wrt_drive, numerical_elasticity  # noqa: E402
from rmti_resilience_components import combine_rho  # noqa: E402


class JohnsonCase(unittest.TestCase):
    def test_cumulative_risk(self):
        self.assertAlmostEqual(jc.cumulative_risk(5, 10), 1 - math.exp(-0.05), places=12)
        self.assertAlmostEqual(jc.cumulative_risk(31, 10), 1 - math.exp(-0.31), places=12)
        with self.assertRaises(ValueError):
            jc.cumulative_risk(0, 10)

    def test_scenario_is_equation_2(self):
        s = jc.scenario(0.2, 0.6, 0.5, 0.3, 0.4)
        self.assertAlmostEqual(s["R"], 0.2 * 0.6 * 0.5 * (1 - combine_rho(0.3, 0.4)), places=12)

    def test_table_shape_and_order(self):
        rows = jc.case_table()
        self.assertEqual(len(rows), 4)
        self.assertGreater(rows[2]["L"], rows[0]["L"])         # cirrhosis has the higher L
        self.assertLess(rows[1]["R"], rows[0]["R"])            # more care delivery lowers R

    def test_R_ratio_equals_one_minus_rho_care_ratio(self):
        rows = jc.case_table(rho_bio=0.35, rho_care_low=0.2, rho_care_high=0.7)
        self.assertAlmostEqual(rows[1]["R"] / rows[0]["R"], (1 - 0.7) / (1 - 0.2), places=12)

    def test_breakeven_roundtrip(self):
        rows = jc.case_table()
        x = jc.breakeven_rho_care(rows[0]["L"], rows[2]["L"], 0.20)
        self.assertIsNotNone(x)
        s = jc.scenario(rows[2]["L"], 0.6, 0.5, 0.3, x)
        self.assertAlmostEqual(s["R"], rows[0]["R"], places=12)
        self.assertIsNone(jc.breakeven_rho_care(0.5, 0.05, 0.2))

    def test_pathway_decomposition_total(self):
        rows = jc.case_table()
        d = jc.pathway_comparison(rows)
        self.assertAlmostEqual(math.exp(d["total_dlnR"]), rows[3]["R"] / rows[0]["R"], places=10)

    def test_fib4_elasticity_matches_numeric(self):
        for r in jc.fib4_v_elasticity():
            f = lambda d: 0.35 + (0.5 / 6.0) * d
            self.assertAlmostEqual(r["eps_d"], numerical_elasticity(f, r["fib4"]), places=5)
            self.assertAlmostEqual(r["eps_d"], elasticity_wrt_drive(r["fib4"], 0.35, 0.85, 6.0), places=12)


if __name__ == "__main__":
    unittest.main()
