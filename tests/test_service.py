import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import service as S


class T(unittest.TestCase):
    def test_patient_a_b_tables(self):
        A = S.trajectory("hcc", .30, .65, 3, .20, [2, 1, 1, 0], [.40, .55, .70, .75])
        B = S.trajectory("hcc", .30, .65, 3, .20, [2, 3, 4, 5], [.40, .40, .35, .35])
        self.assertEqual([r["R_display"] for r in A["memoryless"]], [.081, .055, .042, .031])
        self.assertEqual([r["R_display"] for r in B["memoryless"]], [.081, .094, .113, .127])
        self.assertEqual([round(r["R"], 4) for r in A["filtered"]], [.0806, .0602, .0435, .0340])

    def test_published_table2_snapshot(self):
        o = S.snapshot("hcc", 100_000, .30, .65, .60, .20, .50, 5)
        self.assertEqual((o["R_now"], o["R_after"]), (0.094, 0.059))      # the 0.0585 -> 0.059 case

    def test_input_validation(self):
        with self.assertRaises(ValueError):
            S.snapshot("hcc", 1000, .3, .6, .5, 1.0)
        with self.assertRaises(ValueError):
            S.trajectory("hcc", .3, .6, 3, .2, [9.0], [.5])

    def test_cohort_priority_resets_per_tier(self):
        rows = [dict(name="a", N=1e5, L=.9, E=.7, V=.55, rho_now=.1, C=5),
                dict(name="b", N=1e5, L=.2, E=.55, V=.45, rho_now=.2, C=5),
                dict(name="c", N=1e5, L=.25, E=.6, V=.48, rho_now=.2, C=5)]
        r = S.cohort("hcc", rows)
        self.assertEqual(r[0]["name"], "a")
        self.assertEqual([x["priority_in_tier"] for x in r if x["tier_now"] == r[1]["tier_now"]][0], 1)

    def test_metrics(self):
        self.assertEqual(S.c_index([1, 2, 3, 4], [1, 1, 1, 0], [4, 3, 2, 1]), 1.0)
        self.assertEqual(S.auc([1, 1, 0, 0], [.9, .8, .2, .1]), 1.0)
        self.assertEqual(S.km([1, 2, 3], [1, 0, 1])[-1][1], 0.0)          # S(1)=2/3, S(3)=0

    def test_validation_pipeline(self):
        v = S.validate_serial(S.example_serial(), "hcc")
        self.assertIn("c_index_final", v)
        self.assertEqual(v["n"], 60)
        self.assertTrue(0 <= v["c_index_final"] <= 1)


    def test_privacy_guard(self):
        import pandas as pd
        with self.assertRaises(ValueError):
            S.privacy_check(pd.DataFrame({"patient_name": ["x"], "y": [1]}))
        with self.assertRaises(ValueError):
            S.privacy_check(pd.DataFrame({"note": ["call 555-123-4567"], "y": [1]}))
        with self.assertRaises(ValueError):
            S.privacy_check(pd.DataFrame({"patient_id": ["a@b.org"]}))
        S.privacy_check(pd.DataFrame({"patient_id": ["S001"], "y": [1.0]}))      # pseudonymous id passes

    def test_bootstrap_and_calibration(self):
        v = S.validate_serial(S.example_serial(), "hcc")
        ci = S.bootstrap_ci(v["patients"], 100)
        self.assertLessEqual(ci["delta_c"][0], ci["delta_c"][1])
        cal = S.calibration(v["patients"])
        self.assertTrue((cal["by_tier"]["ci_low"] <= cal["by_tier"]["observed_event_rate"]).all())
        lo, hi = S.wilson(5, 10); self.assertTrue(lo < 0.5 < hi)


class TestLung(unittest.TestCase):
    A = {"p_resection": [(0.01, 0.6), (0.03, 0.5), (0.05, 0.4)], "s5_resection": [(0.01, 0.7), (0.03, 0.6), (0.05, 0.5)]}

    def test_engine_is_the_v231_module(self):
        self.assertEqual(S.ENGINE_VERSION, "2.4.0"); self.assertEqual(S.LUNG.__version__, "2.4.0")

    def test_scaling_and_horizon(self):
        self.assertEqual(S.LUNG.l_from_risk(0.0005), 0.0)
        self.assertAlmostEqual(S.LUNG.l_from_risk(0.10), 1.0)
        with self.assertRaises(ValueError): S.LUNG.l_from_risk(0.02, horizon_years=2)

    def test_rtp_method_only_and_no_extrapolation(self):
        p = S.LUNG.rtp_point(0.03, self.A)
        self.assertAlmostEqual(p["p_resection"], 0.5)
        self.assertIsNone(S.LUNG.rtp_point(0.08, self.A))
        self.assertEqual(len(S.rtp_curve(S.RTP_DEMO_ANCHORS)), 41)
        flat = [v for k in S.RTP_DEMO_ANCHORS.values() for _, v in k]          # unpublished draft figures must not ship
        for banned in (0.37, 0.49, 0.54): self.assertNotIn(banned, flat)
        self.assertFalse(hasattr(S.LUNG, "RTP_ANCHORS"))

    def test_no_double_counting(self):
        muller = S.LUNG_EVIDENCE.L_TOOL_VARIABLES["UK Biobank model (Muller 2017)"]
        clash = S.LUNG.overlap(muller)
        self.assertEqual(len(clash), 2)
        with self.assertRaises(ValueError): S.LUNG.v_indicator(clash, muller)
        self.assertEqual(S.LUNG.v_indicator(["Cardiovascular disease"], muller), 1)

    def test_rho_bio_ladder(self):
        ladders = {"A": [0.10, 0.25, 0.40, 0.55, 0.70], "B": [0.16, 0.41, 0.59, 0.74, 0.80]}
        self.assertEqual([S.LUNG.rho_bio_from_ecog(e) for e in (4, 3, 2, 1, 0)], ladders[S.LUNG.ACTIVE_LADDER])      # the active ladder is a registry setting
        for name, vals in ladders.items():
            self.assertEqual([S.LUNG.rho_bio_from_ecog(e, name) for e in (4, 3, 2, 1, 0)], vals)

    def test_lung_snapshot_and_cohort(self):
        o = S.snapshot("lung", 1e5, S.LUNG.l_from_risk(.03), .6, S.LUNG.v_from_indicator(2), .25, .5, 3)
        self.assertIn("pathway", o["posture_now"].lower())
        r = S.cohort("lung", [dict(name="a", N=1e5, risk5=.06, E=.65, V=.8, rho_now=.2, C=4),
                              dict(name="b", N=1e5, risk5=.004, E=.55, V=.4, rho_now=.2, C=2)])
        self.assertEqual(r[0]["name"], "a")

    def test_stratified_withholds_small_cells(self):
        v = S.validate_serial(S.example_serial(y_max=4.0), "lung")
        self.assertTrue(v["by_stratum"]["note"].str.contains("withheld").all())


class TestFhir(unittest.TestCase):
    INP = dict(N=1e5, L=0.74, E=0.6, V=0.47, rho_now=0.25, rho_after=0.45, C=3, rho_bio=0.55)

    def test_structure_and_safety(self):
        ra = S.fhir_risk_assessment("STUDY-001", "oncoclastics", self.INP, site="lung")
        self.assertEqual(S.fhir_export.structural_problems(ra), [])
        self.assertEqual(ra["status"], "preliminary")
        pr = ra["prediction"][0]
        self.assertNotIn("probabilityDecimal", pr)                      # R is not a probability
        self.assertNotIn("mitigation", ra)                              # posture is not a recommendation
        self.assertEqual(ra["subject"], {"display": "STUDY-001"})       # pseudonymous display only
        self.assertTrue(pr["qualitativeRisk"]["coding"][0]["code"].startswith("tier-"))
        self.assertIn("not a probability", ra["note"][0]["text"])

    def test_refuses_identifiers_and_disaster(self):
        for bad in ("", "a@b.org", "call 555-123-4567"):
            with self.assertRaises(ValueError): S.fhir_risk_assessment(bad, "oncoclastics", self.INP, site="hcc")
        with self.assertRaises(ValueError): S.fhir_risk_assessment("X-1", "disaster_science", self.INP)

    def test_checker_catches_unsafe_resources(self):
        ra = S.fhir_risk_assessment("STUDY-002", "oncoclastics", self.INP, site="hcc")
        ra["prediction"][0]["probabilityDecimal"] = 0.2; ra["status"] = "final"
        self.assertGreaterEqual(len(S.fhir_export.structural_problems(ra)), 2)


class TestOncoclastics(unittest.TestCase):
    def test_vocabulary(self):
        self.assertEqual(S.resolve_domain("oncoclastics"), "hcc")
        self.assertEqual(S.resolve_domain("oncoclastics", "lung"), "lung")
        self.assertEqual(S.resolve_domain("disaster_science"), "disaster")
        self.assertEqual(S.resolve_domain("hcc"), "hcc")                    # legacy keys still accepted

    def test_manuscript_s5_example(self):
        self.assertAlmostEqual(S.combine_rho(0.50, 0.40), 0.70)             # 0.70, not 0.90

    def test_backward_compatible_with_published_hcc(self):
        std = S.trajectory("oncoclastics", .30, .65, 3, .20, [2, 1, 1, 0], [.40, .55, .70, .75])["filtered"]
        two = S.two_sense_trajectory("oncoclastics", .30, .65, 3, 0.0, .20, [2, 1, 1, 0], [.40, .55, .70, .75])["rows"]
        for a, b in zip(std, two):
            self.assertAlmostEqual(a["R"], b["R_two_sense"], places=3)      # rho_bio = 0 reproduces the standard series

    def test_events_name_their_sense_and_care_disruption(self):
        tr = S.two_sense_trajectory("oncoclastics", .30, .65, 3, .25, .20, [2, 3, None, 4], [.60, .40, None, .30])
        senses = {e["sense"] for e in tr["events"]}
        self.assertEqual(senses, {"care-system", "biological"})
        s = S.two_sense_snapshot(.3, .65, .6, .5, .4, 3, .05)
        self.assertGreater(s["care_disruption"]["R_after"], s["care_disruption"]["R_before"])


class TestVault(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import tempfile
        os.environ["RMTI_DB"] = os.path.join(tempfile.mkdtemp(), "t.db")
        os.environ["RMTI_INVITE_CODE"] = "invite-xyz"
        import importlib, secure_store
        cls.V = importlib.reload(secure_store)

    def test_roundtrip_and_ciphertext_only(self):
        V = self.V
        V.register("dr.test", "correct horse battery", "invite-xyz")
        s = V.login("dr.test", "correct horse battery")
        rid = V.save_record(s, "snapshot", "STUDY-001", {"R": 0.094, "note": "pseudonymous"})
        self.assertEqual(V.list_records(s)[0]["payload"]["R"], 0.094)
        import sqlite3
        raw = sqlite3.connect(os.environ["RMTI_DB"]).execute("SELECT token FROM records").fetchone()[0]
        self.assertNotIn(b"STUDY-001", raw); self.assertNotIn(b"0.094", raw)          # only ciphertext on disk
        V.delete_record(s, rid); self.assertEqual(V.list_records(s), [])

    def test_auth_rules(self):
        V = self.V
        with self.assertRaises(V.AuthError): V.register("a.user", "short", "invite-xyz")
        with self.assertRaises(V.AuthError): V.register("a.user", "long enough password", "wrong")
        V.register("dr.two", "another long password", "invite-xyz")
        for _ in range(5):
            with self.assertRaises(V.AuthError): V.login("dr.two", "bad password!!")
        with self.assertRaises(V.AuthError): V.login("dr.two", "another long password")   # locked out

    def test_users_cannot_read_each_other_and_password_change(self):
        V = self.V
        V.register("dr.a", "password number one", "invite-xyz"); V.register("dr.b", "password number two", "invite-xyz")
        a, b = V.login("dr.a", "password number one"), V.login("dr.b", "password number two")
        V.save_record(a, "snapshot", "A-1", {"x": 1})
        self.assertEqual(V.list_records(b), [])
        V.change_password(a, "password number one", "brand new password!")
        a2 = V.login("dr.a", "brand new password!")
        self.assertEqual(V.list_records(a2)[0]["label"], "A-1")                          # DEK survives re-wrap

    def test_refuses_identifiers(self):
        V = self.V
        V.register("dr.c", "password number three", "invite-xyz")
        c = V.login("dr.c", "password number three")
        for label, payload in (("J. Smith", {"patient_name": "x"}), ("ok-1", {"note": "mail a@b.org"}), ("ok-2", {"dob": "1950"})):
            with self.assertRaises(V.StoreError): V.save_record(c, "snapshot", label, payload)


class LungInputsAndAuth(unittest.TestCase):
    def test_lung_inputs(self):
        o = S.lung_inputs(0.02, 5, ecog=1, ladder="A", v_items=["Cardiovascular disease"])
        self.assertAlmostEqual(o["L"], 0.6505149978319906)
        self.assertEqual((o["rho_bio"], o["v_count"]), (0.55, 1))
        self.assertEqual(S.lung_inputs(0.02, 5, ecog=1, ladder="B")["rho_bio"], 0.74)

    def test_lung_inputs_refuse_bad_cases(self):
        with self.assertRaises(ValueError):
            S.lung_inputs(0.02, 2)                                           # 2-year risk
        with self.assertRaises(ValueError):                                  # V item already inside the L tool
            S.lung_inputs(0.02, 5, l_tool="UK Biobank model (Muller 2017)",
                          v_items=["COPD, emphysema or chronic bronchitis"])
        with self.assertRaises(ValueError):
            S.lung_inputs(0.02, 5, v_items=["not an item"])

    def test_production_fails_closed(self):
        from fastapi.testclient import TestClient
        import api
        keep = {k: os.environ.pop(k, None) for k in ("RMTI_API_KEYS", "RMTI_ENV")}
        try:
            c = TestClient(api.app)
            os.environ["RMTI_ENV"] = "production"
            self.assertEqual(c.get("/v1/registry/parameters").status_code, 503)
            self.assertEqual(c.get("/health").status_code, 200)             # probes stay open
            os.environ["RMTI_API_KEYS"] = "k1"
            self.assertEqual(c.get("/v1/registry/parameters").status_code, 401)
            self.assertEqual(c.get("/v1/registry/parameters", headers={"X-API-Key": "k1"}).status_code, 200)
        finally:
            for k in ("RMTI_API_KEYS", "RMTI_ENV"):
                os.environ.pop(k, None)
                if keep[k] is not None: os.environ[k] = keep[k]


class HccPatientEndpoint(unittest.TestCase):
    BODY = dict(age_years=55, male=1, albumin_g_l=33, bilirubin_umol_l=30, platelets_1e9_l=150)

    def test_clean_default_and_values(self):
        o = S.hcc_patient(**self.BODY)
        self.assertTrue(o["status"].startswith("CLEAN")); self.assertFalse(o["overlap"])
        self.assertEqual((o["risk_group"], o["tier"], o["R"]), (2, "2 Moderate", 0.133))

    def test_overlap_refused_then_labelled(self):
        with self.assertRaises(ValueError):
            S.hcc_patient(**self.BODY, l_tool="aMAP")
        d = S.hcc_patient(**self.BODY, l_tool="aMAP", allow_overlap=True)
        self.assertTrue(d["status"].startswith("DIAGNOSTIC")); self.assertEqual(d["tier"], "3 High")     # the double count lifts this patient

    def test_http(self):
        from fastapi.testclient import TestClient
        import api
        c = TestClient(api.app)
        r = c.post("/v1/hcc/patient", json=self.BODY); self.assertEqual(r.status_code, 200); self.assertEqual(r.json()["tier"], "2 Moderate")
        r = c.post("/v1/hcc/patient", json={**self.BODY, "l_tool": "aMAP"}); self.assertGreaterEqual(r.status_code, 400)


class CorsOptIn(unittest.TestCase):
    def test_cors_only_for_listed_origin(self):
        import importlib, api
        from fastapi.testclient import TestClient
        os.environ["RMTI_CORS_ORIGINS"] = "https://www.example.org"
        try:
            importlib.reload(api)
            c = TestClient(api.app)
            ok = c.options("/v1/hcc/patient", headers={"Origin": "https://www.example.org", "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "x-api-key,content-type"})
            self.assertEqual(ok.headers.get("access-control-allow-origin"), "https://www.example.org")
            bad = c.options("/v1/hcc/patient", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"})
            self.assertIsNone(bad.headers.get("access-control-allow-origin"))
        finally:
            os.environ.pop("RMTI_CORS_ORIGINS", None); importlib.reload(api)


if __name__ == "__main__":
    unittest.main()
