import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
import service as S
import sandbox as B

try:
    from fastapi.testclient import TestClient
except Exception:                      # httpx missing: API tests are skipped, nothing else is affected
    TestClient = None
HAS_DATA = "ogaki" in B.datasets()


class Calculator(unittest.TestCase):
    def test_matches_excel_calculator_example(self):
        # Values cached in the workbook's Calculator sheet: 62 y male, albumin 40, bilirubin 14, platelets 150, E 0.60, rho 0.20 / 0.65, C 5
        o = S.hcc_patient(62, 1, 40, 14, 150)
        for key, excel in (("albi", -2.6435554964523633), ("amap", 62.56664429047303), ("amap_ref", 62.708192281651996), ("annual_incidence", 0.028),
                           ("L", 0.7057337317159487), ("V", 0.35), ("R_raw", 0.11856326692827937), ("EAL", 0.565)):
            self.assertAlmostEqual(o[key], excel, places=3 if key == "EAL" else 9, msg=key)   # EAL: engine rounds to 3 dp (Excel 0.564587)
        self.assertAlmostEqual(o["R_after"], 0.052, places=3)                                 # Excel R after 0.0518714 (engine display 3 dp)
        self.assertEqual((o["tier"], o["tier_after"], o["albi_grade"], o["risk_group"]), ("2 Moderate", "2 Moderate", 1, 3))
        self.assertEqual(o["status"], "CLEAN: L and V use disjoint variables")

    def test_overlap_refused_then_diagnostic(self):
        with self.assertRaises(ValueError):
            S.hcc_patient(62, 1, 40, 14, 150, l_tool="aMAP")
        self.assertTrue(S.hcc_patient(62, 1, 40, 14, 150, l_tool="aMAP", allow_overlap=True)["status"].startswith("DIAGNOSTIC"))


@unittest.skipUnless(HAS_DATA, "bundled Ogaki cohort not installed")
class Ogaki(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.o = B.run("hcc", dataset="ogaki")

    def test_workbook_checks_all_pass(self):
        bad = [c for c in self.o["verification"]["checks"] if c["result"] != "PASS"]
        self.assertEqual(bad, [])
        self.assertEqual(self.o["verification"]["overall"], "ALL PASS")

    def test_tier_counts_as_in_workbook(self):
        t = {r["tier"]: (r["patients_now"], r["patients_after"]) for r in self.o["tiers"]}
        self.assertEqual((t["1 Low"], t["2 Moderate"], t["3 High"]), ((787, 1855), (1870, 1246), (444, 0)))

    def test_no_patient_rows_by_default(self):
        self.assertIsNone(self.o["patients"])

    def test_changed_settings_skip_comparison(self):
        o = B.run("hcc", dataset="ogaki", options={"E": 0.5})
        self.assertEqual(o["verification"]["checks"], [])

    def test_no_double_counting_by_default(self):
        self.assertEqual(self.o["score_status"], ["CLEAN: L and V use disjoint variables"])


class CohortFiles(unittest.TestCase):
    """Delete, update and add bundled cohorts by changing files only (RMTI_COHORT_DIR points at a scratch folder)."""
    def setUp(self):
        import tempfile
        self.dir = tempfile.mkdtemp()
        self._old, B.COHORT_DIR = B.COHORT_DIR, self.dir

    def tearDown(self):
        import shutil
        B.COHORT_DIR = self._old
        shutil.rmtree(self.dir, ignore_errors=True)

    def _write(self, name, rows, header="patient_id,risk5,v_count,time_years,cause"):
        open(os.path.join(self.dir, name), "w").write(header + "\n" + "\n".join(rows) + "\n")

    def test_empty_folder_means_no_bundled_cohorts_and_nothing_breaks(self):
        self.assertEqual(B.datasets(), {})
        with self.assertRaises(ValueError):
            B.run("hcc", dataset="ogaki")

    def test_new_file_is_discovered_with_disease_inferred_and_scored(self):
        self._write("lung_pilot.csv", ["a,0.02,1,3.0,0", "b,0.05,2,1.5,1", "c,0.01,0,6.0,0", "d,0.08,3,2.0,2"])
        self.assertEqual(B.datasets()["lung_pilot"]["disease"], "lung")
        o = B.run("lung", dataset="lung_pilot")
        self.assertEqual((o["n"], o["audit"]["bundled_dataset"]["rows"]), (4, 4))
        self.assertIsNone(o["patients"])                                  # aggregate only by default
        self.assertEqual(len(o["audit"]["bundled_dataset"]["sha256"]), 64)

    def test_metadata_sidecar_sets_id_and_label(self):
        self._write("x.csv", ["a,0.02,1,3.0,0"])
        open(os.path.join(self.dir, "x.meta.json"), "w").write('{"id": "pilot", "label": "Pilot", "disease": "lung"}')
        self.assertEqual(B.datasets()["pilot"]["label"], "Pilot")

    def test_updating_a_file_changes_results_and_stale_reference_is_not_compared(self):
        import json, shutil
        src = os.path.join(os.path.dirname(os.path.abspath(B.__file__)), "cohort_data")
        if not os.path.exists(os.path.join(src, "ogaki_hcc_cohort.csv")):
            self.skipTest("Ogaki cohort not installed")
        for f in ("ogaki_hcc_cohort.csv", "ogaki_hcc_cohort.meta.json", "ogaki_reference.json"):
            shutil.copy(os.path.join(src, f), self.dir)
        self.assertEqual(B.run("hcc", dataset="ogaki")["verification"]["overall"], "ALL PASS")
        p = os.path.join(self.dir, "ogaki_hcc_cohort.csv")
        lines = open(p).read().splitlines()
        open(p, "w").write("\n".join(lines[:-1]) + "\n")                  # one patient removed = an updated cohort
        o = B.run("hcc", dataset="ogaki")
        self.assertEqual(o["n"], 3100)
        self.assertEqual(o["verification"]["checks"], [])
        self.assertIn("changed", o["verification"]["note"])

    def test_identifier_column_in_a_dropped_in_file_is_refused(self):
        self._write("bad.csv", ["a,0.02,1,3.0,0"], header="patient_name,risk5,v_count,time_years,cause")
        with self.assertRaises(ValueError):
            B.run("lung", dataset="bad")


class Accessibility(unittest.TestCase):
    @staticmethod
    def _cr(a, b):
        def lum(h):
            h = h.lstrip("#"); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
            f = lambda v: v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
            return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2])
        hi, lo = sorted([lum(a), lum(b)], reverse=True)
        return (hi + 0.05) / (lo + 0.05)

    def test_wcag_aa_contrast_of_tier_colours_and_text(self):
        import style
        for i, (accent, tint, text) in style.TIER.items():
            self.assertGreaterEqual(self._cr(accent, "#FFFFFF"), 3.0, "tier %d accent vs white (graphics, 3:1)" % i)
            self.assertGreaterEqual(self._cr(text, tint), 4.5, "tier %d text on tint (4.5:1)" % i)
        self.assertGreaterEqual(self._cr(style.INK, "#FFFFFF"), 4.5)
        self.assertGreaterEqual(self._cr(style.MUTED, style.PANEL), 4.5)
        self.assertGreaterEqual(self._cr(style.PRIMARY, "#FFFFFF"), 4.5)

    def test_tier_chip_always_carries_number_and_name(self):
        import style
        for name in style.TIER_NAMES:
            self.assertIn(name, style.tier_chip(name))


class CumulativeIncidence(unittest.TestCase):
    def test_no_competing_equals_one_minus_km(self):
        t, c = [1, 2, 3, 4], [1, 0, 1, 0]           # KM: S(1)=.75, S(3)=.375 -> CIF(3)=.625
        self.assertAlmostEqual(B.cumulative_incidence(t, c, [3])[3], 0.625)

    def test_competing_event_lowers_cif(self):
        self.assertLess(B.cumulative_incidence([1, 2, 3], [2, 1, 0], [5])[5], 2 / 3)


class Sandboxes(unittest.TestCase):
    def test_all_diseases_run_on_synthetic_demo(self):
        mp = {"L": dict(column="feat_texture", lo=0, hi=6), "E": dict(column="feat_intensity_var", lo=500, hi=3500),
              "V": dict(column="feat_adc", lo=0.6, hi=2.0, invert=True), "rho": dict(column="feat_sphericity", lo=0.3, hi=0.95)}
        for d in B.DISEASES:
            o = B.run(d, records=B.demo_records(d), options={"mapping": mp} if d == "imaging" else None)
            self.assertEqual(o["n"], 300)
            self.assertEqual(len(o["patients"]), 300)
            self.assertTrue(o["outcomes"] is not None or d == "imaging")

    def test_lung_refuses_two_year_risk_and_percentages(self):
        rows = [dict(patient_id="a", risk5=0.03, v_count=1, risk_horizon_years=2)]
        with self.assertRaises(ValueError):
            B.run("lung", records=rows)
        with self.assertRaises(ValueError):
            B.run("lung", records=[dict(patient_id=str(i), risk5=2.5, v_count=1) for i in range(5)])

    def test_breast_refuses_declared_overlap_and_bad_ranges(self):
        rows = [dict(patient_id="a", L=0.3, V=0.4)]
        with self.assertRaises(ValueError):
            B.run("breast", records=rows, options={"declared_l_variables": ["Age"], "declared_v_variables": ["age"]})
        with self.assertRaises(ValueError):
            B.run("breast", records=[dict(patient_id="a", L=1.3, V=0.4)])

    def test_privacy_guard_and_input_checks(self):
        with self.assertRaises(ValueError):
            B.run("breast", records=[dict(patient_name="x", L=0.3, V=0.4)])
        with self.assertRaises(ValueError):
            B.run("hcc", records=[dict(age_years=60)])                         # missing columns
        with self.assertRaises(ValueError):
            B.run("hcc", records=[dict(age_years=60, male=1, albumin_g_l=40, bilirubin_umol_l=14, platelets_1e9_l=150, cause=3)])
        with self.assertRaises(ValueError):
            B.run("hcc", dataset="nope")
        with self.assertRaises(ValueError):
            B.run("lung", dataset="ogaki") if HAS_DATA else B.run("lung", dataset="nope")

    def test_event_alias_and_uploaded_rows_returned(self):
        rows = [dict(age_years=60 + i, male=i % 2, albumin_g_l=40, bilirubin_umol_l=14, platelets_1e9_l=150, time_years=3 + i, event=i % 2) for i in range(12)]
        o = B.run("hcc", records=rows)
        self.assertEqual(len(o["patients"]), 12)
        self.assertEqual(o["outcomes"]["events"], 6)


@unittest.skipUnless(TestClient, "fastapi TestClient/httpx not installed")
class Api(unittest.TestCase):
    def setUp(self):
        os.environ.pop("RMTI_API_KEYS", None)
        import api
        self.c = TestClient(api.app)

    def tearDown(self):
        os.environ.pop("RMTI_API_KEYS", None)

    def test_templates_and_score(self):
        t = self.c.get("/v1/sandbox/templates").json()
        self.assertEqual(sorted(t), ["breast", "hcc", "imaging", "lung"])
        r = self.c.post("/v1/sandbox/lung/score", json={"records": B.demo_records("lung")})
        self.assertEqual(r.status_code, 200)
        self.assertIn("X-RMTI-Registry", r.headers)
        self.assertEqual(r.json()["n"], 300)

    @unittest.skipUnless(HAS_DATA, "bundled Ogaki cohort not installed")
    def test_bundled_dataset_over_api(self):
        r = self.c.post("/v1/sandbox/hcc/score", json={"dataset": "ogaki"}).json()
        self.assertEqual(r["verification"]["overall"], "ALL PASS")
        self.assertIsNone(r["patients"])

    def test_datasets_listing_has_no_patient_data(self):
        r = self.c.get("/v1/sandbox/datasets").json()
        self.assertIsInstance(r, list)
        for d in r:
            self.assertEqual(set(d), {"id", "disease", "label", "description", "has_reference"})

    def test_errors_are_422_not_500(self):
        self.assertEqual(self.c.post("/v1/sandbox/lung/score", json={"records": [{"risk5": 0.03, "v_count": 1, "risk_horizon_years": 2}]}).status_code, 422)
        self.assertEqual(self.c.post("/v1/sandbox/hcc/score", json={}).status_code, 422)
        self.assertEqual(self.c.post("/v1/sandbox/ovarian/score", json={"records": []}).status_code, 422)

    def test_api_key_protects_new_routes_and_existing_ones_unchanged(self):
        os.environ["RMTI_API_KEYS"] = "k1"
        self.assertEqual(self.c.get("/v1/sandbox/templates").status_code, 401)
        self.assertEqual(self.c.get("/v1/sandbox/templates", headers={"X-API-Key": "k1"}).status_code, 200)
        self.assertEqual(self.c.get("/health").status_code, 200)
        self.assertEqual(self.c.post("/v1/hcc/patient", json=dict(age_years=62, male=1, albumin_g_l=40, bilirubin_umol_l=14, platelets_1e9_l=150)).status_code, 401)

    def test_existing_hcc_patient_endpoint_still_works(self):
        r = self.c.post("/v1/hcc/patient", json=dict(age_years=62, male=1, albumin_g_l=40, bilirubin_umol_l=14, platelets_1e9_l=150)).json()
        self.assertEqual(r["tier"], "2 Moderate")


if __name__ == "__main__":
    unittest.main()
