"""Breast scaffold, imaging ROI scaffold, tumour-at-diagnosis table, and the Ogaki converter. All data here are synthetic."""
import json, os, subprocess, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
import pandas as pd
import service as S
import sandbox as B
import rmti_breast as BR

ROOT = os.path.join(os.path.dirname(__file__), "..")
try:
    from fastapi.testclient import TestClient
except Exception:
    TestClient = None
try:
    from streamlit.testing.v1 import AppTest
except Exception:
    AppTest = None
MP = {"L": dict(column="feat_texture", lo=0, hi=6), "E": dict(column="feat_intensity_var", lo=500, hi=3500),
      "V": dict(column="feat_adc", lo=0.6, hi=2.0, invert=True), "rho": dict(column="feat_sphericity", lo=0.3, hi=0.95)}


class BreastModule(unittest.TestCase):
    def test_five_year_only_and_placeholder_flag(self):
        self.assertTrue(BR.PLACEHOLDER)
        with self.assertRaises(ValueError):
            BR.l_from_risk(0.05, 10)
        with self.assertRaises(ValueError):
            BR.l_from_risk(1.5)
        self.assertEqual(BR.l_from_risk(0.001), 0.0)
        self.assertEqual(BR.l_from_risk(0.5), 1.0)
        self.assertAlmostEqual(BR.l_from_risk(0.0167), 0.403, places=3)

    def test_no_invented_breast_specific_items(self):
        for name in ("V_ITEMS", "RHO_BIO_LADDER", "ECOG"):
            self.assertFalse(hasattr(BR, name), name)

    def test_service_layer_uses_breast_not_disaster_defaults(self):
        self.assertEqual(S._params("breast"), BR.BREAST_PARAMS)                  # _params returns a copy, so compare by value
        self.assertNotEqual(S._params("breast").y_max, S._params("disaster").y_max)   # and it is not the disaster fallback
        o = S.snapshot("breast", 100000, BR.l_from_risk(0.0167), 0.6, 0.5, 0.2, 0.45, 3)
        self.assertEqual(o["tier_now"], "2 Moderate")
        self.assertIn("screening", o["posture_now"].lower())
        c = S.cohort("breast", [dict(name="A", N=1e5, risk5=0.0167, E=.6, V=.5, rho_now=.2, C=3), dict(name="B", N=1e5, risk5=0.05, E=.6, V=.6, rho_now=.2, C=3)])
        self.assertEqual([r["name"] for r in c], ["B", "A"])

    @unittest.skipUnless(TestClient, "fastapi TestClient not installed")
    def test_api_accepts_breast_site(self):
        import api
        os.environ.pop("RMTI_API_KEYS", None)
        r = TestClient(api.app).post("/v1/snapshot", json=dict(domain="oncoclastics", site="breast", N=1e5, L=.3, E=.6, V=.5, rho_now=.2, C=3))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["tier_now"], "2 Moderate")


class BreastSandbox(unittest.TestCase):
    def test_refusals(self):
        base = dict(patient_id="a", risk5=0.03, V=0.4)
        for bad in (dict(sex="male"), dict(prior_breast_cancer=1), dict(risk_horizon_years=10)):
            with self.assertRaises(ValueError, msg=str(bad)):
                B.run("breast", records=[{**base, **bad}])
        with self.assertRaises(ValueError):
            B.run("breast", records=[base], options={"declared_l_variables": ["age"], "declared_v_variables": ["Age"]})

    def test_runs_on_risk5_and_status_says_scaffold(self):
        o = B.run("breast", records=B.demo_records("breast"))
        self.assertEqual(o["n"], 300)
        self.assertIn("SCAFFOLD", o["score_status"][0])


class Imaging(unittest.TestCase):
    def setUp(self):
        self.recs = B.demo_records("imaging")

    def test_refuses_without_mapping_or_anchors_or_with_shared_column(self):
        for m in (None, {**MP, "L": dict(column="feat_texture")}, {**MP, "E": dict(column="feat_texture", lo=0, hi=6)}, {**MP, "L": dict(column="feat_texture", lo=5, hi=5)}):
            with self.assertRaises(ValueError):
                B.run("imaging", records=self.recs, options={"mapping": m})

    def test_missing_values_are_excluded_never_zero(self):
        r = [dict(x) for x in self.recs]
        r[0]["feat_texture"] = None
        r[1]["feat_adc"] = "n/a"
        o = B.run("imaging", records=r, options={"mapping": MP})
        self.assertEqual((o["imaging"]["rows_scored"], o["imaging"]["rows_excluded_missing"]), (298, 2))
        self.assertEqual(o["imaging"]["excluded_row_numbers"], [1, 2])
        self.assertEqual(len(o["patients"]), 298)

    def test_all_missing_is_an_error_not_tier_1(self):
        with self.assertRaises(ValueError):
            B.run("imaging", records=[{"patient_id": "a", "feat_texture": None, "feat_intensity_var": None, "feat_adc": None, "feat_sphericity": None}], options={"mapping": MP})

    def test_clipping_is_reported_and_tiers_are_the_platform_tiers(self):
        o = B.run("imaging", records=self.recs, options={"mapping": MP})
        self.assertGreater(sum(o["imaging"]["values_clipped_to_anchors"].values()), 0)
        self.assertEqual([t["tier"] for t in o["tiers"]], B.TIER_SHORT)
        text = json.dumps(o["tiers"]) + o["status"]
        for word in ("Definitively", "malignant mass", "Normal tissue"):
            self.assertNotIn(word, text)

    def test_validation_reports_each_term_and_split(self):
        v = B.run("imaging", records=self.recs, options={"mapping": MP})["imaging"]["validation"]
        self.assertEqual(set(v["by_split"]), {"all rows", "dev", "test"})
        self.assertEqual(set(v["by_split"]["test"]["auc"]), {"R", "L alone", "E alone", "V alone", "1 - rho alone", "simple mean of the four terms"})
        self.assertIn("test", v["note"])
        nosplit = [{k: x for k, x in r.items() if k != "split"} for r in self.recs]
        self.assertIn("optimistic", B.run("imaging", records=nosplit, options={"mapping": MP})["imaging"]["validation"]["note"])

    def test_a_term_pointing_the_wrong_way_is_called_out(self):
        wrong = {**MP, "V": dict(column="feat_adc", lo=0.6, hi=2.0, invert=False)}      # ADC mapped without inverting: lower ADC should raise V
        v = B.run("imaging", records=self.recs, options={"mapping": wrong})["imaging"]["validation"]
        self.assertTrue(any(w["term"] == "V alone" for w in v["direction_warnings"]))
        ok = B.run("imaging", records=self.recs, options={"mapping": MP})["imaging"]["validation"]
        self.assertEqual(ok["direction_warnings"], [])

    def test_correlated_terms_are_flagged(self):
        r = [dict(x) for x in self.recs]
        for x in r:
            x["feat_intensity_var"] = x["feat_texture"] * 500 + 100
        o = B.run("imaging", records=r, options={"mapping": MP})
        self.assertTrue(o["imaging"]["correlated_term_pairs"])

    def test_auc_function(self):
        self.assertEqual(B.auc([0, 0, 1, 1], [1, 2, 3, 4]), 1.0)
        self.assertEqual(B.auc([0, 1], [5, 5]), 0.5)
        self.assertIsNone(B.auc([1, 1], [1, 2]))


class TumourTable(unittest.TestCase):
    def test_percentages_use_only_recorded_values(self):
        rows = []
        for i in range(40):
            rows.append(dict(patient_id=f"p{i}", age_years=60, male=1, albumin_g_l=40, bilirubin_umol_l=14, platelets_1e9_l=150, time_years=3 + i * 0.1, cause=1 if i < 12 else 0,
                             max_diameter_cm=(4.0 if i < 3 else 2.0) if i < 8 else None, vp=(1 if i == 0 else 0) if i < 8 else None, n_nodules=1 if i < 8 else None))
        t = B.run("hcc", records=rows)["extras"]["tumour_at_diagnosis_by_tier"][0]
        self.assertEqual(t["n_size_recorded"], 8)
        self.assertAlmostEqual(t["pct_over_3cm"], 100 * 3 / 8)
        self.assertEqual(t["n_vp_recorded"], 8)
        self.assertAlmostEqual(t["pct_portal_vein_invasion"], 100 / 8)


class Converter(unittest.TestCase):
    def test_script_strips_identifiers_and_applies_the_stated_rules(self):
        cols = ["ID", "DOB", "Age_at_entry", "Gender", "Etiology", "ALB_g_L", "Tbil_umol_L", "Plt_10^3_mm3", "Date_studyentry", "HCC_Dx_day_detection_day",
                "Years_to_FU", "HCC", "Outcome", "Max_Diameter_in_cm", "Number_of_nodules", "Vp", "Early_HCC", "AFP_ng_mL"]
        e = pd.Timestamp("2010-01-01")
        rows = [
            [101, "1950-03-02", 61.0, "M", "C", 40, 14, 190, e, pd.NaT, 8.0, "No", "alive", "-", "-", "-", "-", 5],                      # censored
            [102, "1948-05-09", 70.2, "F", "B", 38, 20, 150, e, e + pd.Timedelta(days=730), 9.0, "Yes", "dead", 2.5, 1, 0, "Yes", 40],     # HCC at ~2y, then died
            [103, "1955-01-01", 55.0, "M", "NBNC", 42, 9, 220, e, pd.NaT, 5.0, "No", "dead", "-", "-", "-", "-", 3],                      # death without HCC
            [104, "1940-01-01", 80.0, "F", "C", 35, 30, 100, e, e + pd.Timedelta(days=10), 6.0, "Yes", "alive", 3.0, 1, 0, "Yes", 9],      # HCC within 30 d: excluded
            [105, "2005-01-01", 15.0, "M", "C", 44, 10, 250, e, pd.NaT, 4.0, "No", "alive", "-", "-", "-", "-", 2],                       # under 18: excluded
            [106, "1950-01-01", 60.0, "M", "C", 40, 12, "-", e, pd.NaT, 4.0, "No", "alive", "-", "-", "-", "-", 2],                       # missing platelets: excluded
        ]
        with tempfile.TemporaryDirectory() as d:
            x, out = os.path.join(d, "in.xlsx"), os.path.join(d, "out.csv")
            pd.DataFrame(rows, columns=cols).to_excel(x, index=False)
            run = lambda salt: subprocess.run([sys.executable, os.path.join(ROOT, "tools", "prepare_ogaki_cohort.py"), x, out, "--salt", salt, "--include-tumour"], capture_output=True, text=True)
            r = run("a long private phrase")
            self.assertEqual(r.returncode, 0, r.stderr)
            o = pd.read_csv(out)
            self.assertEqual(len(o), 3)
            self.assertEqual(sorted(o["cause"]), [0, 1, 2])
            self.assertEqual(o.loc[o.cause == 1, "time_years"].iloc[0].round(1), 2.0)          # time to HCC from the diagnosis date, not Years_to_FU
            leaked = [c for c in o.columns if any(k in c.lower() for k in ("dob", "date", "birth", "day"))] + [c for c in o.columns if c in ("ID", "Early_HCC", "AFP_ng_mL")]
            self.assertEqual(leaked, [])
            self.assertFalse(set(o["patient_id"]) & {"101", "102", "103"})
            self.assertTrue(all(p.startswith("OG") and len(p) == 10 for p in o["patient_id"]))
            self.assertTrue(o.loc[o.cause != 1, "max_diameter_cm"].isna().all())
            first = list(o["patient_id"])
            run("a long private phrase")
            self.assertEqual(list(pd.read_csv(out)["patient_id"]), first)                       # same salt, same codes
            run("another private phrase")
            self.assertNotEqual(list(pd.read_csv(out)["patient_id"]), first)
            self.assertTrue(os.path.exists(os.path.join(d, "out.meta.json")))
            self.assertNotEqual(run("short").returncode, 0)                                      # weak salt refused


@unittest.skipUnless(AppTest, "streamlit not installed")
class MainAppBreast(unittest.TestCase):
    def test_breast_site_loads_and_says_what_is_missing(self):
        at = AppTest.from_file(os.path.join(ROOT, "app.py.py"), default_timeout=90).run()
        for r in at.sidebar.radio:
            if "Breast cancer, female (proposed scaffold)" in r.options:
                r.set_value("Breast cancer, female (proposed scaffold)").run()
                break
        self.assertEqual([e.value for e in at.exception], [])
        self.assertIn("Breast: scope and limits", [t.label for t in at.tabs])
        txt = " ".join(str(c.value) for c in at.caption) + " ".join(str(i.value) for i in at.info)
        self.assertIn("PLACEHOLDER", txt)
        self.assertIn("No breast ρ_bio ladder", txt)

    def test_ogaki_pointer_on_the_hcc_validation_tab(self):
        at = AppTest.from_file(os.path.join(ROOT, "app.py.py"), default_timeout=90).run()
        self.assertTrue(any("Cohort Sandbox" in str(i.value) for i in at.info))


if __name__ == "__main__":
    unittest.main()
