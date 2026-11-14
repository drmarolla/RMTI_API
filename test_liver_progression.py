"""tests/test_liver_progression.py -- the 4D liver: frames follow the engine and the RMTI formula; geometry is finite; routes validate."""
import math, os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import liver_progression as LP


def run(name="Progression, then surveillance rescue", **kw):
    p = LP.PRESETS[name]
    return LP.manifest(p["L"], p["E"], p["C"], p["rho0"], p["y"], p["delivery"], **kw)


class LiverTests(unittest.TestCase):
    def test_cycle_frames_equal_the_engine(self):
        m = run()
        cyc = [f for f in m["frames"] if f["is_cycle"]]
        self.assertEqual(len(cyc), len(m["cycles"]))
        for f, r in zip(cyc, m["cycles"]):
            self.assertAlmostEqual(f["R"], r["R"], places=5)
            self.assertAlmostEqual(f["V"], r["V"], places=4)
            self.assertAlmostEqual(f["rho"], r["rho"], places=4)

    def test_every_frame_follows_the_formula(self):
        m = run(); L, E = m["inputs"]["L"], m["inputs"]["E"]
        for f in m["frames"]:
            self.assertAlmostEqual(f["R"], L * E * f["V"] * (1 - f["rho"]), places=5)

    def test_rotation_is_one_full_turn(self):
        m = run(turns=1.0)
        self.assertEqual(m["frames"][0]["azimuth_deg"], 0)
        self.assertAlmostEqual(m["frames"][-1]["azimuth_deg"], 360.0, places=1)
        self.assertEqual(run(turns=0)["frames"][-1]["azimuth_deg"], 0)

    def test_glyph_volume_is_proportional_to_R(self):
        r1, r2 = LP.glyph_radius(0.05), LP.glyph_radius(0.40)
        self.assertAlmostEqual((r2 / r1) ** 3, 0.40 / 0.05, places=6)
        self.assertEqual(LP.glyph_radius(5.0), LP.glyph_radius(LP.R_REF))      # capped

    def test_stage_bands_and_bounds(self):
        for name in LP.PRESETS:
            for f in run(name)["frames"]:
                self.assertTrue(0 <= f["stage_f"] <= 1)
        self.assertTrue(LP.stage_band(0.0).startswith("F0")); self.assertTrue(LP.stage_band(1.0).startswith("F4"))

    def test_missed_visits_are_handled(self):
        m = run("Missed visits, then progression")
        self.assertIsNone(m["cycles"][2]["y"]); self.assertTrue(all(math.isfinite(f["R"]) for f in m["frames"]))

    def test_validation_comes_from_the_engine(self):
        with self.assertRaises(ValueError):
            LP.manifest(0.5, 0.5, 5, 0.2, [None, 1.0], [0.5, 0.5])             # baseline y missing
        with self.assertRaises(ValueError):
            LP.manifest(0.5, 0.5, 5, 0.2, [1.0, 9.0], [0.5, 0.5])              # y above y_max
        with self.assertRaises(ValueError):
            LP.manifest(0.5, 0.5, 5, 0.2, [1.0, 2.0], [0.5, 0.5], sub=0)

    def test_geometry(self):
        for f in (0.0, 0.5, 1.0):
            x, y, z, i, j, k, col = LP.liver_mesh(f, 40, 20)
            self.assertEqual(len(x), 40 * 20); self.assertTrue(all(math.isfinite(v) for v in x + y + z))
            self.assertTrue(max(i + j + k) < len(x)); self.assertRegex(col, r"^#[0-9a-f]{6}$")
            self.assertTrue(max(map(abs, x)) < 1.5 and max(map(abs, z)) < 1.0)
        sx, sy, sz, si, sj, sk = LP.sphere_mesh(0.2, nt=20, npp=10)
        self.assertEqual(len(sx), 200); self.assertTrue(max(si + sj + sk) < 200)

    def test_routes(self):
        try:
            from fastapi import FastAPI
            from fastapi.testclient import TestClient
        except ImportError:
            self.skipTest("fastapi/httpx not installed")
        import liver_routes
        app = FastAPI(); app.include_router(liver_routes.router); c = TestClient(app)
        self.assertEqual(set(c.get("/v1/liver/presets").json()["presets"]), set(LP.PRESETS))
        p = LP.PRESETS["Progression, then surveillance rescue"]
        body = dict(L=p["L"], E=p["E"], C=p["C"], rho0=p["rho0"], observations=p["y"], delivery=p["delivery"], sub=4)
        r = c.post("/v1/liver/progression", json=body); self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["frame_count"], (len(p["y"]) - 1) * 4 + 1)
        self.assertEqual(c.post("/v1/liver/progression", json={**body, "observations": [None] + p["y"][1:]}).status_code, 422)
        self.assertEqual(c.post("/v1/liver/progression", json={**body, "L": 1.5}).status_code, 422)


if __name__ == "__main__":
    unittest.main()
