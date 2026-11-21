import pytest
pytest.importorskip("fastapi"); pytest.importorskip("httpx"); pytest.importorskip("pandas")
from fastapi.testclient import TestClient
from rmti.api import app

c = TestClient(app)


def test_health_and_score():
    assert c.get("/health").json()["status"] == "ok"
    r = c.post("/score", json=dict(L=0.9, E_sel=0.65, V=0.8, rho=0.2, rho_after=0.55, C=5, N=16000000)).json()
    assert r["R"] == 0.374 and r["R_after"] == 0.211 and r["tier"].startswith("Tier 4")
    assert r["assessment"]["risk_reduction_pct"] == 43.8
    assert c.post("/score", json=dict(L=1.2, E_sel=.5, V=.5, rho=.5)).status_code == 422


def test_simulate():
    p = lambda m: {"mean": m, "woe": "w_ic"}
    r = c.post("/simulate", json=dict(L=p(.9), E=p(.65), V=p(.8), rho=p(.2), n_sims=5000)).json()
    assert 0.5 < r["p_point_tier"] < 0.8
    bad = c.post("/simulate", json=dict(L={"mean": .5, "woe": "zz"}, E=p(.5), V=p(.5), rho=p(.5)))
    assert bad.status_code == 422


def test_optimize():
    body = dict(budget=100, projects=[dict(name="a", cost=60, R_now=.4, R_after=.2), dict(name="b", cost=60, R_now=.3, R_after=.2),
                                      dict(name="c", cost=40, R_now=.3, R_after=.15)])
    r = c.post("/optimize", json=body).json()
    assert set(r["selected"]) == {"a", "c"}
    body["mandatory"] = ["a", "b"]
    assert c.post("/optimize", json=body).status_code == 422


def test_hcc():
    r = c.post("/hcc/albi", json=dict(albumin=45, bilirubin=10)).json()
    assert r["albi_grade"] == 1 and r["V"] == 0.35
    pts = [dict(id="A", L=.3, E=.6, albi_grade=1, surveillance="usual", bclc_if_missed="A"),
           dict(id="B", L=.25, E=.6, albumin=30, bilirubin=50, surveillance="usual", bclc_if_missed="C-D")]
    out = c.post("/hcc/score", json=dict(patients=pts)).json()["patients"]
    assert [p["id"] for p in out] == ["B", "A"] and out[0]["priority"] == 1
    pts[0]["surveillance"] = "weekly"
    assert c.post("/hcc/score", json=dict(patients=pts)).status_code == 422
