import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import rmti_cases as K

# expected values read from the workbooks' calculated cells
EXPECT = {
    "palisades": (0.1152, "2 Moderate", 0.0936, "2 Moderate"),
    "altadena":  (0.1536, "3 High",     0.1248, "2 Moderate"),
    "lilongwe":  (0.42,   "4 Severe",   0.2912, "3 High"),
}


class CaseTests(unittest.TestCase):
    def test_disaster_matches_workbook(self):
        for c in K.DISASTER_CASES:
            rn, tn, ra, ta = EXPECT[c["key"]]
            e = K.evaluate(c)
            self.assertAlmostEqual(e["R_now"], rn, 6); self.assertAlmostEqual(e["R_after"], ra, 6)
            self.assertEqual((e["tier_now"], e["tier_after"]), (tn, ta))

    def test_faria_v(self):
        self.assertAlmostEqual(K.v_from_counts(10, 18, 1), 0.522413793103448, 9)   # workbook G18
        self.assertAlmostEqual(K.v_from_counts(12, 13, 0), 0.48, 9)                # workbook G19

    def test_bounds(self):
        for c in K.PRESETS.values():
            for k in ("L", "E", "V", "rho_now", "rho_after"):
                self.assertTrue(0 <= c[k] < 1.0001)


if __name__ == "__main__":
    unittest.main()
