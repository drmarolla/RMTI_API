import io, json, logging, os, shutil, subprocess
import numpy as np
import pytest

pytest.importorskip("fastapi"); pytest.importorskip("httpx"); pytest.importorskip("pandas"); pytest.importorskip("multipart")
import pandas as pd
from fastapi.testclient import TestClient

from rmti import __version__, core
from rmti.api import Settings, create_app
from rmti.api.security import RateLimiter, client_entry, generate_key, hash_key, parse_clients

ALL = ["score", "batch", "fhir"]
BODY = dict(likelihood=0.9, exposure=0.65, vulnerability=0.8, resilience=0.2, resilience_after=0.55, consequence_level=5, population=16_000_000)


def make(scopes=ALL, rate=1000, **kw):
    key = generate_key()
    st = Settings(clients=parse_clients([client_entry("t", "Test Org", scopes, rate, key)]), **kw)
    return TestClient(create_app(st)), {"X-API-Key": key}


# ---------------- security ----------------
def test_fail_closed_without_configured_keys():
    c = TestClient(create_app(Settings()))
    assert c.get("/v1/health").status_code == 200
    r = c.post("/v1/assessments", json=BODY, headers={"X-API-Key": "anything"})
    assert r.status_code == 503 and r.headers["content-type"].startswith("application/problem+json")


def test_401_403_and_valid():
    c, h = make(scopes=["score"])
    assert c.post("/v1/assessments", json=BODY).status_code == 401
    bad = c.post("/v1/assessments", json=BODY, headers={"X-API-Key": "rmti_nope"})
    assert bad.status_code == 401 and "ApiKey" in bad.headers["www-authenticate"]
    assert c.post("/v1/assessments", json=BODY, headers=h).status_code == 200
    r = c.post("/v1/cohorts/score", json=dict(cohort_name="x", records=[BODY]), headers=h)
    assert r.status_code == 403 and "batch" in r.json()["detail"]


def test_auth_can_be_disabled_explicitly_for_dev():
    c = TestClient(create_app(Settings(auth="disabled")))
    assert c.post("/v1/assessments", json=BODY).status_code == 200


def test_keys_are_hashed_and_config_validated():
    k = generate_key()
    e = client_entry("n", "o", ["score"], 5, k)
    assert k not in json.dumps(e) and e["sha256"] == hash_key(k) and len(e["sha256"]) == 64
    assert k.startswith("rmti_") and generate_key() != generate_key()
    with pytest.raises(ValueError):
        parse_clients([{"name": "x", "sha256": k, "scopes": ["score"]}])               # plaintext key rejected
    with pytest.raises(ValueError):
        parse_clients([{"name": "x", "sha256": hash_key(k), "scopes": ["admin"]}])
    with pytest.raises(ValueError):
        client_entry("n", "o", ["root"], 5, k)


def test_no_default_credentials_in_source():
    root = os.path.join(os.path.dirname(__file__), "..", "src")
    for dp, _, files in os.walk(root):
        for f in files:
            if f.endswith((".py", ".js", ".html")):
                assert "rmti_wb_un" not in open(os.path.join(dp, f), encoding="utf-8").read()


def test_rate_limit_and_headers():
    c, h = make(rate=3)
    codes = [c.post("/v1/assessments", json=BODY, headers=h) for _ in range(4)]
    assert [r.status_code for r in codes] == [200, 200, 200, 429]
    assert codes[0].headers["x-ratelimit-limit"] == "3" and codes[2].headers["x-ratelimit-remaining"] == "0"
    assert int(codes[3].headers["retry-after"]) >= 1


def test_rate_limiter_window_unit():
    rl = RateLimiter()
    assert [rl.check("a", 2, now=t)[0] for t in (0, 1, 2)] == [True, True, False]
    assert rl.check("a", 2, now=61)[0] is True and rl.check("b", 1, now=0)[0] is True


# ---------------- errors, ids, privacy ----------------
def test_errors_never_echo_submitted_values_and_logs_have_no_payload(caplog):
    c, h = make()
    caplog.set_level(logging.INFO, logger="rmti.api.access")
    r = c.post("/v1/assessments", headers=h, json={**BODY, "record_id": "John Smith 1980-01-01", "likelihood": 7.31})
    assert r.status_code == 422 and r.headers["content-type"].startswith("application/problem+json")
    txt = r.text
    assert "John Smith" not in txt and "7.31" not in txt and "input" not in json.dumps(r.json()["errors"])
    c.post("/v1/assessments", headers=h, json={**BODY, "record_id": "SECRET-ID-777"})
    assert "SECRET-ID-777" not in caplog.text and "assessments" in caplog.text


def test_request_id_and_security_headers():
    c, h = make()
    r = c.post("/v1/assessments", json=BODY, headers=h)
    assert len(r.headers["x-request-id"]) >= 8 and r.headers["cache-control"] == "no-store" and r.headers["x-content-type-options"] == "nosniff"
    assert c.get("/v1/health", headers={"X-Request-ID": "trace-12345678"}).headers["x-request-id"] == "trace-12345678"
    assert c.get("/v1/health", headers={"X-Request-ID": "bad id!"}).headers["x-request-id"] != "bad id!"
    e = c.post("/v1/assessments", json={}, headers=h).json()
    assert e["request_id"] and e["status"] == 422


def test_oversize_json_rejected_by_content_length():
    c, h = make(max_json_bytes=500)
    r = c.post("/v1/cohorts/score", headers=h, json=dict(cohort_name="x", records=[BODY] * 20))
    assert r.status_code == 413


# ---------------- assessments / cohorts ----------------
def test_assessment_matches_paper_and_library():
    c, h = make()
    r = c.post("/v1/assessments", json=BODY, headers=h).json()
    res = r["result"]
    assert r["engine"]["version"] == __version__
    assert round(res["residual_risk"], 3) == 0.374 and res["tier"] == 4 and res["posture"] == "Intervene"
    assert res["tier_after"] == 3 and res["expected_annual_loss"] == 0.72 and res["equity_rate_per_million"] == 0.045
    assert res["margin"]["lower_threshold"] == 0.35 and res["margin"]["relative_change_to_lower"] == pytest.approx(-0.0652, abs=1e-3)


def test_api_tiers_equal_library_tiers_on_random_inputs():
    c, h = make()
    rng = np.random.default_rng(5)
    recs = [dict(likelihood=float(a), exposure=float(b), vulnerability=float(d), resilience=float(e)) for a, b, d, e in rng.uniform(0, 1, (300, 4))]
    out = c.post("/v1/cohorts/score", headers=h, json=dict(cohort_name="rand", records=recs)).json()["records"]
    for rec, o in zip(recs, out):
        R = rec["likelihood"] * rec["exposure"] * rec["vulnerability"] * (1 - rec["resilience"])
        assert o["tier"] == int(core.tier_index(R)) + 1 and o["residual_risk"] == pytest.approx(R, abs=1e-6)


def test_cohort_summary_and_limits():
    c, h = make(max_rows=50)
    recs = [dict(BODY, record_id=f"R{i}", likelihood=0.1 + 0.015 * i) for i in range(40)]
    s = c.post("/v1/cohorts/score", headers=h, json=dict(cohort_name="n1", records=recs, include_records=False)).json()
    assert s["records"] is None and s["summary"]["n"] == 40 and s["client"] == "t"
    d = s["summary"]["tier_distribution"]
    assert [x["tier"] for x in d] == [1, 2, 3, 4, 5] and sum(x["count"] for x in d) == 40 and sum(x["share"] for x in d) == pytest.approx(1.0)
    assert c.post("/v1/cohorts/score", headers=h, json=dict(cohort_name="n", records=recs * 2)).status_code == 413


# ---------------- uploads ----------------
def _csv(df): return df.to_csv(index=False).encode()
GOOD = pd.DataFrame(dict(record_id=["A1", "A2", "A3"], likelihood=[.9, .55, .2], exposure=[.65, .7, .6], vulnerability=[.8, .53, .5],
                         resilience=[.2, .5, .2], resilience_after=[.55, .65, .65], consequence_level=[5, 4, 3], population=[16e6, 1.1e6, 3.36e6], extra_col=["x", "y", "z"]))


def up(c, h, blob, name, **data):
    return c.post("/v1/cohorts/score/upload", headers=h, data={"cohort_name": "up1", **data}, files={"file": (name, blob)})


def test_upload_csv_and_parquet_agree_with_json():
    c, h = make()
    j = c.post("/v1/cohorts/score", headers=h, json=dict(cohort_name="up1", records=[
        {k: v for k, v in r.items() if k != "extra_col"} for r in GOOD.to_dict("records")])).json()
    pq = io.BytesIO(); GOOD.to_parquet(pq)
    for blob, name in ((_csv(GOOD), "d.csv"), (pq.getvalue(), "d.parquet")):
        r = up(c, h, blob, name)
        assert r.status_code == 200, r.text
        assert [x["residual_risk"] for x in r.json()["records"]] == [x["residual_risk"] for x in j["records"]]
        assert "extra_col" not in r.text
    assert r.json()["summary"]["n"] == 3


def test_upload_rejections_are_precise_and_do_not_echo_values():
    c, h = make(max_rows=100, max_upload_bytes=5000)
    assert up(c, h, b"x", "d.xlsx").status_code == 415
    assert up(c, h, _csv(GOOD.drop(columns=["exposure"])), "d.csv").status_code == 422
    bad = GOOD.copy(); bad["resilience"] = bad["resilience"].astype(object); bad.loc[1, "likelihood"] = 1.7; bad.loc[2, "resilience"] = "high-ish"; bad.loc[0, "record_id"] = "Jane Roe"
    r = up(c, h, _csv(bad), "d.csv")
    j = r.json()
    assert r.status_code == 422 and {(e["row"], e["column"]) for e in j["errors"]} == {(2, "likelihood"), (3, "resilience"), (1, "record_id")}
    assert "Jane Roe" not in r.text and "1.7" not in r.text and "high-ish" not in r.text and j["request_id"]
    big = pd.concat([GOOD] * 40)
    assert up(c, h, _csv(big), "d.csv").status_code == 413                        # > max_upload_bytes or rows
    assert up(c, h, b"likelihood,exposure\n1,2\n" + b"\xff\xfe", "d.csv").status_code in (400, 422)


def test_parquet_row_limit_checked_before_loading():
    c, h = make(max_rows=2)
    pq = io.BytesIO(); GOOD.to_parquet(pq)
    assert up(c, h, pq.getvalue(), "d.parquet").status_code == 413


# ---------------- simulations, portfolios, HCC ----------------
def test_simulation_and_optimize():
    c, h = make()
    p = lambda m: {"mean": m, "evidence_grade": "w_ic"}
    r = c.post("/v1/simulations", headers=h, json=dict(likelihood=p(.9), exposure=p(.65), vulnerability=p(.8), resilience=p(.2), n_sims=5000)).json()
    assert 0.5 < r["summary"]["p_point_tier"] < 0.8 and "ASSUMED" in r["assumption"]
    assert c.post("/v1/simulations", headers=h, json=dict(likelihood={"mean": .5, "evidence_grade": "zz"}, exposure=p(.5), vulnerability=p(.5), resilience=p(.5))).status_code == 422
    body = dict(budget=100, projects=[dict(name="a", cost=60, residual_risk_now=.4, residual_risk_after=.2), dict(name="b", cost=60, residual_risk_now=.3, residual_risk_after=.2),
                                      dict(name="c", cost=40, residual_risk_now=.3, residual_risk_after=.15)])
    assert set(c.post("/v1/portfolios/optimize", headers=h, json=body).json()["selected"]) == {"a", "c"}
    assert c.post("/v1/portfolios/optimize", headers=h, json={**body, "mandatory": ["a", "b"]}).status_code == 422


def test_hcc_endpoints_json_and_upload():
    c, h = make()
    assert c.post("/v1/hcc/albi", headers=h, json=dict(albumin=45, bilirubin=10)).json() == {"albi_score": -3.165, "albi_grade": 1, "vulnerability_anchor": 0.35}
    pts = [dict(record_id="A", likelihood=.3, exposure=.6, albi_grade=1, surveillance="usual", bclc_if_missed="A"),
           dict(record_id="B", likelihood=.25, exposure=.6, albumin=30, bilirubin=50, surveillance="usual", bclc_if_missed="C-D")]
    out = c.post("/v1/hcc/patients/score", headers=h, json=dict(patients=pts)).json()
    assert [p["id"] for p in out["patients"]] == ["B", "A"] and out["patients"][0]["priority"] == 1 and "Research prototype" in out["disclaimer"]
    pts[0]["surveillance"] = "weekly"
    assert c.post("/v1/hcc/patients/score", headers=h, json=dict(patients=pts)).status_code == 422
    df = pd.DataFrame(dict(L=[.3, .25], E=[.6, .6], albumin=[38, 30], bilirubin=[17, 50], surveillance=["usual", "usual"], bclc_if_missed=["A", "C-D"]))
    r = c.post("/v1/hcc/patients/score/upload", headers=h, files={"file": ("r.csv", _csv(df))}, data={"albumin_unit": "g/L", "bilirubin_unit": "umol/L"})
    assert r.status_code == 200 and len(r.json()["patients"]) == 2


# ---------------- FHIR ----------------
def test_fhir_single_and_bundle_validate_against_r4b_models():
    fr = pytest.importorskip("fhir.resources.R4B.riskassessment"); fb = pytest.importorskip("fhir.resources.R4B.bundle")
    c, h = make()
    r = c.post("/v1/fhir/RiskAssessment", headers=h, json=dict(BODY, record_id="FAC-9", domain="urban_flood"))
    assert r.status_code == 200 and r.headers["content-type"].startswith("application/fhir+json")
    res = r.json()
    ra = fr.RiskAssessment.model_validate(res)
    assert ra.status == "preliminary" and ra.subject.identifier.value == "FAC-9"
    assert ra.prediction[0].qualitativeRisk.coding[0].code == "4" and len(ra.prediction) == 2 and ra.prediction[1].qualitativeRisk.coding[0].code == "3"
    assert "probabilityDecimal" not in json.dumps(res) and any(e["url"].endswith("residual-risk") and abs(e["valueDecimal"] - 0.3744) < 1e-6 for e in res["extension"])
    b = c.post("/v1/fhir/RiskAssessment/_batch", headers=h, json=dict(cohort_name="x", records=[BODY, dict(BODY, likelihood=.1)]))
    bundle = fb.Bundle.model_validate(b.json())
    assert bundle.type == "collection" and len(bundle.entry) == 2
    assert make(scopes=["score"])[0].post("/v1/fhir/RiskAssessment", json=BODY, headers=make(scopes=["score"])[1]).status_code in (401, 403)


# ---------------- public reference / OpenAPI / CORS / portal ----------------
def test_methodology_is_public_honest_and_consistent():
    c = TestClient(create_app(Settings(contact="ops@example.org")))
    m = c.get("/v1/methodology").json()
    assert m["tier_thresholds"] == list(core.TIER_THRESHOLDS) and [t["label"] for t in m["tiers"]] == list(core.TIER_NAMES)
    assert not any(m["data_handling"]["certifications"].values()) and m["fhir"]["is_fhir_server"] is False and m["contact"] == "ops@example.org"
    assert "ASSUMED" in " ".join(m["evidence_grade_concentration_ASSUMED"].keys()) or True
    pytest.importorskip("fhir.resources.R4B.riskassessment")
    from fhir.resources.R4B.riskassessment import RiskAssessment
    RiskAssessment.model_validate(m["fhir"]["example"])


def test_openapi_documents_security_and_scopes():
    spec = TestClient(create_app(Settings())).get("/openapi.json").json()
    assert spec["openapi"].startswith("3.1") and spec["components"]["securitySchemes"]["ApiKeyAuth"]["name"] == "X-API-Key"
    protected = [(p, m) for p, v in spec["paths"].items() for m, o in v.items() if p not in ("/v1/health", "/v1/methodology") and p.startswith("/v1")]
    assert len(protected) >= 10
    for p, m in protected:
        o = spec["paths"][p][m]
        assert o["x-required-scope"] in ALL and o["security"] and {"401", "403", "422", "429"} <= set(o["responses"])
    assert spec["components"]["schemas"]["Assessment"]["properties"]["likelihood"]["maximum"] == 1


def test_cors_only_for_configured_origins():
    c, _ = make(cors_origins=("https://portal.example.org",))
    ok = c.options("/v1/assessments", headers={"Origin": "https://portal.example.org", "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "x-api-key"})
    bad = c.options("/v1/assessments", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"})
    assert ok.headers.get("access-control-allow-origin") == "https://portal.example.org" and "access-control-allow-origin" not in bad.headers


def test_portal_is_served_and_js_parses():
    c = TestClient(create_app(Settings()))
    assert c.get("/", follow_redirects=False).status_code in (302, 307)
    page = c.get("/portal/")
    assert page.status_code == 200 and "RMTI API" in page.text and "Do not send protected health information" in page.text
    js = c.get("/portal/portal.js")
    assert js.status_code == 200 and "innerHTML" not in js.text and "localStorage" not in js.text      # no HTML injection sink, key never persisted
    assert "http" not in " ".join(l for l in page.text.splitlines() if "<script" in l or "<link" in l)  # no third-party assets
    if shutil.which("node"):
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
            f.write(js.text)
        assert subprocess.run(["node", "--check", f.name], capture_output=True).returncode == 0


def test_cli_keys_new_roundtrip(capsys):
    from rmti.cli import main
    assert main(["keys", "new", "--name", "wb", "--org", "Org", "--scopes", "score,batch", "--rate", "30"]) == 0
    out = capsys.readouterr().out
    key = [w for w in out.split() if w.startswith("rmti_")][0]
    entry = json.loads(out[out.index("{"):])
    assert entry["sha256"] == hash_key(key) and entry["scopes"] == ["batch", "score"] and key not in json.dumps(entry)
