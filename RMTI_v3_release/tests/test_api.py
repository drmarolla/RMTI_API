import unittest

from fastapi.testclient import TestClient

import api
import rmti_core as core

H = {"X-API-Key": core.SANDBOX_KEY}
BODY = {"L": 0.7, "E": 0.6, "V": 0.8, "rho": 0.35}


class ApiTests(unittest.TestCase):
    def setUp(self):
        api._hits.clear()
        self.c = TestClient(api.app)

    def test_health_public(self):
        self.assertEqual(self.c.get("/health").status_code, 200)

    def test_score(self):
        r = self.c.post("/v1/risk/score", json=BODY, headers=H)
        self.assertEqual(r.status_code, 200)
        d = r.json()
        self.assertAlmostEqual(d["risk"], 0.7 * 0.6 * 0.8 * 0.65, places=5)
        self.assertEqual(d["tier"], "moderate")  # R = 0.2184
        self.assertIn("X-RateLimit-Remaining", r.headers)
        self.assertIn("X-Request-ID", r.headers)

    def test_auth(self):
        self.assertEqual(self.c.post("/v1/risk/score", json=BODY).status_code, 401)
        r = self.c.post("/v1/risk/score", json=BODY, headers={"X-API-Key": "nope"})
        self.assertEqual(r.json()["code"], "invalid_api_key")

    def test_validation(self):
        r = self.c.post("/v1/risk/score", json={**BODY, "L": 1.5}, headers=H)
        self.assertEqual(r.status_code, 422)
        self.assertEqual(r.json()["code"], "validation_error")

    def test_rate_limit(self):
        for _ in range(20):
            self.assertEqual(self.c.get("/v1/usage", headers=H).status_code, 200)
        r = self.c.get("/v1/usage", headers=H)
        self.assertEqual(r.status_code, 429)
        self.assertIn("Retry-After", r.headers)

    def test_batch_and_cap(self):
        r = self.c.post("/v1/risk/batch", json={"items": [BODY] * 3}, headers=H)
        self.assertEqual(r.json()["count"], 3)
        r = self.c.post("/v1/risk/batch", json={"items": [BODY] * 26}, headers=H)
        self.assertEqual(r.status_code, 413)

    def test_sweep_and_fhir(self):
        r = self.c.post("/v1/risk/sensitivity", json={**BODY, "lever": "rho", "steps": 5}, headers=H)
        pts = r.json()["points"]
        self.assertEqual(len(pts), 5)
        self.assertEqual(pts[-1]["risk"], 0.0)
        f = self.c.post("/v1/risk/score/fhir", json=BODY, headers=H).json()
        self.assertEqual(f["resourceType"], "RiskAssessment")

    def test_priority_lever(self):
        d = core.score(0.9, 0.9, 0.9, 0.0)
        self.assertIn(d["priority_lever"], ("L", "E", "V", "rho"))
        self.assertEqual(core.score(0, 0.5, 0.5, 0.5)["priority_lever"], None)


if __name__ == "__main__":
    unittest.main()
