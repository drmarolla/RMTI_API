"""tests/test_scene.py -- scene manifests: arithmetic matches rmti_cases, validation, and the FastAPI routes."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import rmti_cases as K
import scene as SC


class SceneTests(unittest.TestCase):
    def test_all_cases_match_rmti_cases(self):
        for row in SC.list_cases():
            s = SC.scene_for_case(row["key"])
            c = SC.case_inputs(row["key"])
            self.assertAlmostEqual(s["summary"]["R_now"], K.r_score(c["L"], c["E"], c["V"], c["rho_now"]), places=4)
            self.assertAlmostEqual(s["summary"]["R_after"], K.r_score(c["L"], c["E"], c["V"], c["rho_after"]), places=4)
            self.assertEqual(s["summary"]["tier_now"], K.tier(K.r_score(c["L"], c["E"], c["V"], c["rho_now"])))

    def test_frames_walk_the_cube_and_end_at_published_values(self):
        s = SC.scene_for_case("lagos")
        f = s["frames"]
        self.assertEqual(f[0]["pos"], [0, 0, 0])
        self.assertEqual(f[-1]["pos"], [0.9, 0.65, 0.8])
        self.assertAlmostEqual(f[-1]["product"], s["summary"]["R_after"], places=4)
        self.assertEqual(s["frame_count"], len(f))
        self.assertTrue(all(0 <= p <= 1 for fr in f for p in fr["pos"]))
        self.assertEqual([fr["i"] for fr in f], list(range(len(f))))

    def test_video_numbers(self):
        # the narrated videos quote these
        self.assertEqual(SC.scene_for_case("hbv_untreated")["summary"]["tier_now"], "3 High")
        self.assertEqual([round(SC.scene_for_case(k)["summary"]["R_now"], 2) for k in ("lilongwe", "lagos", "bamako")], [0.42, 0.37, 0.41])

    def test_validation(self):
        for bad in (dict(L=1.2, E=.5, V=.5, rho_now=.2, rho_after=.5), dict(L=.5, E=.5, V=.5, rho_now=1.0, rho_after=.5),
                    dict(L=-.1, E=.5, V=.5, rho_now=.2, rho_after=.5)):
            with self.assertRaises(ValueError):
                SC.build(**bad)
        with self.assertRaises(KeyError):
            SC.scene_for_case("nope")

    def test_bar_values_end_state(self):
        s = SC.scene_for_case("bamako"); b = SC.bar_values(s["frames"][-1], s["inputs"])
        self.assertAlmostEqual(b[4], s["summary"]["R_now"], places=4)
        self.assertAlmostEqual(b[5], s["summary"]["R_after"], places=4)

    def test_routes(self):
        try:
            from fastapi import FastAPI
            from fastapi.testclient import TestClient
        except ImportError:
            self.skipTest("fastapi/httpx not installed")
        import scene_routes
        app = FastAPI(); app.include_router(scene_routes.router); c = TestClient(app)
        self.assertGreaterEqual(c.get("/v1/scene/cases").json()["count"], 8)
        r = c.get("/v1/scene/lagos"); self.assertEqual(r.status_code, 200); self.assertEqual(r.json()["summary"]["tier_now"], "4 Severe")
        self.assertEqual(c.get("/v1/scene/nope").status_code, 404)
        ok = c.post("/v1/scene", json=dict(L=.3, E=.65, V=.55, rho_now=.2, rho_after=.5)); self.assertEqual(ok.status_code, 200)
        self.assertEqual(c.post("/v1/scene", json=dict(L=1.5, E=.5, V=.5, rho_now=.2, rho_after=.5)).status_code, 422)
        self.assertEqual(c.get("/v1/scene/lagos?per_leg=1").status_code, 422)


if __name__ == "__main__":
    unittest.main()
