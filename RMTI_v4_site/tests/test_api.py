import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi.testclient import TestClient
import api

H = {"X-API-Key": api.SANDBOX_KEY}
B = {"L": 0.8, "E": 0.85, "V": 0.75, "rho_now": 0.20, "rho_after": 0.58, "C": 4, "N": 4_500_000}


class T(unittest.TestCase):
    def setUp(self):
        api._hits.clear()
        self.c = TestClient(api.app)

    def test_bamako_matches_paper(self):
        d = self.c.post("/v1/risk/score", json=B, headers=H).json()
        self.assertEqual(d["R_now"], 0.408); self.assertEqual(d["R_after"], 0.214)
        self.assertEqual(d["tier_now"], "Tier 4 - Severe"); self.assertEqual(d["tier_after"], "Tier 3 - High")
        self.assertEqual(d["risk_reduction_pct"], 47.5)

    def test_hcc_domain(self):
        d = self.c.post("/v1/risk/score", json={**B, "domain": "hcc", "N": 100000, "C": 5}, headers=H).json()
        self.assertIn("posture_now", d)

    def test_auth_and_validation(self):
        self.assertEqual(self.c.post("/v1/risk/score", json=B).status_code, 401)
        self.assertEqual(self.c.post("/v1/risk/score", json={**B, "rho_now": 1.0}, headers=H).status_code, 422)

    def test_rate_limit(self):
        for _ in range(20):
            self.assertEqual(self.c.get("/v1/usage", headers=H).status_code, 200)
        self.assertEqual(self.c.get("/v1/usage", headers=H).status_code, 429)

    def test_batch_sens_fhir(self):
        r = self.c.post("/v1/risk/batch", json={"items": [{**B, "name": "a"}, {**B, "name": "b", "L": 0.3}]}, headers=H).json()
        self.assertEqual(r["count"], 2)
        self.assertEqual(self.c.post("/v1/risk/batch", json={"items": [{**B, "name": str(i)} for i in range(26)]}, headers=H).status_code, 413)
        s = self.c.post("/v1/risk/sensitivity", json={"L": 0.9, "E": 0.65, "V": 0.8, "rho": 0.2}, headers=H).json()
        self.assertTrue(s["one_way"][0]["minus"]["flips_tier"])   # Lagos flips at -10% (paper Table 8)
        self.assertEqual(self.c.post("/v1/risk/score/fhir", json=B, headers=H).json()["resourceType"], "RiskAssessment")


if __name__ == "__main__":
    unittest.main()
