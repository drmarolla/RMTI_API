import json, os, shutil, sys
import numpy as np, pandas as pd, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import registry as R
from fastapi.testclient import TestClient


@pytest.fixture
def tmp_registry(tmp_path, monkeypatch):
    """A private, UNLOCKED copy of the whole engine package (so the code-hash lock can be tested too)."""
    pkg = tmp_path / "pkg"
    shutil.copytree(os.path.dirname(os.path.dirname(R.REG_DIR)), pkg, ignore=shutil.ignore_patterns("__pycache__"))
    d = pkg / "oncology" / "registry"
    if (d / "prereg_lock.json").exists():
        (d / "prereg_lock.json").unlink()
    pa = json.load(open(d / "lung_parameters.json")); pa["locked"] = False
    json.dump(pa, open(d / "lung_parameters.json", "w"), indent=1)
    monkeypatch.setattr(R, "REG_DIR", str(d))
    monkeypatch.setattr(R, "LOCK_FILE", str(d / "prereg_lock.json"))
    monkeypatch.setattr(R, "PROPOSAL_DIR", str(tmp_path / "proposed"))
    return d


def _gradient(n=4000, seed=3, rates=(0.002, 0.0035, 0.0067, 0.0126, 0.027), counts=(1500, 1500, 600, 300, 100)):
    rng = np.random.default_rng(seed)
    rows = []
    for k, (r, c) in enumerate(zip(rates, counts)):
        t = rng.exponential(1 / r, c)
        cens = rng.uniform(100, 600, c)
        rows += [dict(ecog=k, time=min(a, b), event=int(a <= b)) for a, b in zip(t, cens)]
    return pd.DataFrame(rows)


def test_shipped_registry_is_consistent():
    assert R.validate() == []
    assert len(R.stamp().split("+")[1]) == 12


def test_engine_reads_registry_both_ladders_available():
    from rmti_engine.oncology import rmti_lung as LU
    lad = {"A": ([0.10, 0.25, 0.40, 0.55, 0.70], 0.70), "B": ([0.16, 0.41, 0.59, 0.74, 0.80], 0.80)}
    assert LU.RHO_BIO_LUNG_ANCHORS == lad[LU.ACTIVE_LADDER][0] and LU.RHO_BIO_LUNG_CEILING == lad[LU.ACTIVE_LADDER][1]
    assert [LU.rho_bio_from_ecog(e, "A") for e in (4, 3, 2, 1, 0)] == [0.10, 0.25, 0.40, 0.55, 0.70]
    assert LU.RHO_BIO_LUNG_CEILINGS == {"A": 0.70, "B": 0.80}
    with pytest.raises(ValueError, match="unknown ladder"):
        LU.rho_bio_from_ecog(1, "Z")
    assert LU.L_ANCHORS == {"r_lo": 0.001, "r_hi": 0.10}                       # nothing else moved


def test_add_evidence_bumps_version_not_parameters(tmp_registry):
    before = R.params_hash(); v0 = R.load()["evidence"]["registry_version"]
    e = dict(id="x2026", status="peer-reviewed", verified="abstract", cite="c", design="d", findings="f", use="u", limits="l")
    v1 = R.add_evidence(e)
    assert v1 != v0 and R.validate() == []
    assert R.params_hash() == before                       # constants identical: only the version label moved


def test_evidence_and_cohorts_can_be_added_after_the_lock(tmp_registry):
    R.lock(); locked = R.params_hash(); assert R.validate() == []
    e = dict(id="late2027", status="peer-reviewed", verified="abstract", cite="c", design="d", findings="f", use="u", limits="l")
    R.add_evidence(e)
    R.register_cohort(dict(id="c_late", source_evidence_id="late2027", centre="Elsewhere", period="2015-2019", n=500,
                           cancer_scope="lung", ecog_levels_reported="0-4", ecog_pooling="none"))
    assert R.validate() == [] and R.params_hash() == locked          # the lock still holds
    p = R.load()["parameters"]; p["rho_bio_ladder"][0]["value"] = 0.12
    json.dump(p, open(R._path("parameters"), "w"))
    assert any("LOCKED parameters" in x for x in R.validate())       # but a constant change is caught


def test_conference_abstract_cannot_enter_peer_reviewed_list(tmp_registry):
    e = dict(id="c1", status="conference-abstract", verified="abstract", cite="c", design="d", findings="f", use="u", limits="l")
    with pytest.raises(ValueError, match="only peer-reviewed"):
        R.add_evidence(e)


def test_pending_source_cannot_support_a_claim(tmp_registry):
    e = dict(id="p1", status="peer-reviewed", verified="abstract_partial", cite="c", design="d", findings="f", use="u",
             limits="l", pending_verification=True, supports=["ecog_five_level_order"])
    with pytest.raises(ValueError, match="pending verification"):
        R.add_evidence(e)


def test_locked_parameters_detect_tampering(tmp_registry):
    R.lock(); assert R.validate() == []
    p = R.load()["parameters"]; p["L_anchors"]["r_hi"] = 0.2
    json.dump(p, open(R._path("parameters"), "w"))
    assert any("LOCKED" in x for x in R.validate())


def test_overlap_flag_same_centre_and_period(tmp_registry):
    meta = dict(id="nguyen_b", source_evidence_id="nguyen2025", centre="nghe an oncology hospital", period="2019-2023",
                n=500, cancer_scope="lung_stage_III", ecog_levels_reported="0-4", ecog_pooling="none")
    out = R.register_cohort(meta)
    assert out["overlap_flags"] and "not independent" in out["overlap_flags"][0]["reason"]


def test_ladder_support_separates_a_real_gradient():
    rep = R.ladder_support(_gradient())
    assert [s["verdict"] for s in rep["steps"]][1:3] == ["separates", "separates"]
    assert rep["levels"][4]["n"] == 100


def test_ladder_support_flags_sparse_and_pooled_levels():
    d = _gradient(counts=(1500, 1500, 600, 300, 100)); d = d[d.ecog != 4]          # no ECOG 4 at all
    rep = R.ladder_support(d)
    assert rep["steps"][3]["verdict"] == "no data" and not rep["supports_five_levels"]
    d2 = _gradient(counts=(1500, 1500, 600, 300, 8)); rep2 = R.ladder_support(d2, min_events=10)
    assert rep2["levels"][4]["sparse"] and "sparse" in rep2["steps"][3]["verdict"]


def test_ladder_support_rejects_bad_input():
    with pytest.raises(ValueError):
        R.ladder_support(pd.DataFrame({"ecog": [0, 1], "time": [0, 5], "event": [1, 0]}))
    with pytest.raises(ValueError, match="not found"):
        R.ladder_support(pd.DataFrame({"x": [1]}))


# ---- API ------------------------------------------------------------------------------------------------------------
@pytest.fixture
def client(monkeypatch):
    monkeypatch.delenv("RMTI_API_KEYS", raising=False)
    monkeypatch.delenv("RMTI_ADMIN_KEYS", raising=False)
    import api
    return TestClient(api.app)


def test_every_response_carries_registry_stamp(client):
    r = client.get("/health")
    assert r.headers["X-RMTI-Registry"] == R.stamp() and r.json()["registry"] == R.stamp()
    r2 = client.post("/v1/snapshot", json=dict(domain="lung", L=.5, E=.5, V=.5, rho_now=.3))
    assert r2.status_code == 200 and r2.headers["X-RMTI-Registry"] == R.stamp()


def test_registry_endpoints(client):
    s = client.get("/v1/registry").json()
    assert s["problems"] == [] and s["counts"]["evidence"] == 10 and s["parameters_locked"] == R.load()["parameters"]["locked"]
    ev = client.get("/v1/registry/evidence?include_supplementary=false").json()["evidence"]
    assert {"jang2014", "lee2024", "howard2025", "kaesmann2019"} <= {e["id"] for e in ev}
    assert [r["ecog"] for r in client.get("/v1/registry/parameters").json()["rho_bio_ladder"]] == [4, 3, 2, 1, 0]


def test_ladder_support_endpoint_and_privacy(client):
    rows = _gradient(n=0, counts=(200, 200, 100, 60, 30)).to_dict("records")
    assert client.post("/v1/registry/ladder-support", json=dict(records=rows)).status_code == 200
    bad = [dict(r, patient_name="x") for r in rows[:5]]
    assert client.post("/v1/registry/ladder-support", json=dict(records=bad)).status_code == 422


def test_proposals_need_admin_key_and_change_nothing(client, monkeypatch, tmp_path):
    body = dict(target="rho_bio_ladder", reason="New cohort separates ECOG 3 from 4", author="rev01", payload={})
    assert client.post("/v1/registry/proposals", json=body).status_code == 403      # no key configured = disabled
    monkeypatch.setenv("RMTI_ADMIN_KEYS", "k1"); monkeypatch.setattr(R, "PROPOSAL_DIR", str(tmp_path / "p"))
    before = R.stamp()
    assert client.post("/v1/registry/proposals", json=body, headers={"X-Admin-Key": "bad"}).status_code == 403
    ok = client.post("/v1/registry/proposals", json=body, headers={"X-Admin-Key": "k1"})
    assert ok.status_code == 200 and R.stamp() == before
    assert len(client.get("/v1/registry/proposals", headers={"X-Admin-Key": "k1"}).json()) == 1


def test_kawaguchi_is_verified_and_supports_all_levels():
    ev = {e["id"]: e for e in R.load()["evidence"]["evidence"]}
    k = ev["kawaguchi2010"]
    assert k["verified"] == "full_text" and not k.get("pending_verification")
    lv = k["adjusted_hr"]["levels"]
    assert [lv[str(i)]["hr"] for i in (1, 2, 3, 4)] == [1.293, 2.044, 2.944, 4.179]
    # adjacent intervals do not overlap: every step separates
    his = [lv[str(i)]["hi"] for i in (1, 2, 3)]; los = [lv[str(i)]["lo"] for i in (2, 3, 4)]
    assert all(h < l for h, l in zip(his, los))


def test_numeric_hr_requires_full_text(tmp_registry):
    e = dict(id="h1", status="peer-reviewed", verified="abstract", cite="c", design="d", findings="f", use="u", limits="l",
             adjusted_hr={"reference_level": 0, "levels": {"1": {"hr": 1.2, "lo": 1.1, "hi": 1.3}}})
    with pytest.raises(ValueError, match="full_text"):
        R.add_evidence(e)


def test_ladder_face_validity_matches_hand_calculation():
    chk = R.ladder_face_validity("kawaguchi2010", ladder="A")[0]
    assert chk["ladder"] == "A" and chk["ladder_max_multiplier"] == pytest.approx(1 / 0.30, abs=1e-3)
    by = {r["ecog"]: r for r in chk["levels"]}
    assert [by[k]["ladder_implied"] for k in (1, 2, 3, 4)] == [1.5, 2.0, 2.5, 3.0]
    assert "too steep" in by[1]["verdict"] and "within" in by[2]["verdict"]
    assert "too shallow" in by[3]["verdict"] and "unreachable" in by[4]["verdict"]


def test_ladder_check_endpoint(client):
    r = client.get("/v1/registry/ladder-check?source=kawaguchi2010")
    assert r.status_code == 200 and r.json()["checks"][0]["source"] == "kawaguchi2010"


def test_health_is_open_but_v1_needs_key_when_keys_are_set(monkeypatch):
    monkeypatch.setenv("RMTI_API_KEYS", "k1")
    import api
    c = TestClient(api.app)
    assert c.get("/health").status_code == 200
    assert c.get("/v1/registry").status_code == 401
    assert c.get("/v1/registry", headers={"X-API-Key": "k1"}).status_code == 200


def test_ladder_b_matches_its_derivation_and_kawaguchi_intervals():
    chk = R.ladder_face_validity("kawaguchi2010", ladder="B")[0]
    assert chk["ladder"] == "B" and chk["ladder_max_multiplier"] == pytest.approx(5.0)
    assert all("within" in r["verdict"] for r in chk["levels"])
    kw = {e["id"]: e for e in R.load()["evidence"]["evidence"]}["kawaguchi2010"]
    hr = {int(k): v["hr"] for k, v in kw["adjusted_hr"]["levels"].items()}
    pa = R.load()["parameters"]
    rows = pa["rho_bio_ladder"] if pa["active_ladder"] == "B" else pa["ladder_alternatives"]["B"]["ladder"]
    lad = {r["ecog"]: r["value"] for r in rows}
    for k, h in hr.items():                                                            # (1 - rho_k) = 0.20 x HR_k, to the nearest 0.01
        assert abs((1 - lad[k]) - 0.20 * h) <= 0.0051


def test_both_ladders_validate_and_ceiling_is_enforced(tmp_registry):
    assert R.validate() == []
    p = R.load()["parameters"]; p["rho_bio_ceiling"] = 0.75
    json.dump(p, open(R._path("parameters"), "w"))
    assert any("top value must equal its ceiling" in x for x in R.validate())


def test_unknown_ladder_is_rejected(client):
    assert client.get("/v1/registry/ladder-check?ladder=Z").status_code == 422
    assert client.get("/v1/registry/ladder-check?ladder=A").json()["checks"][0]["ladder"] == "A"


def test_set_active_ladder_swaps_and_refuses_when_locked(tmp_registry):
    v0 = R.load()["evidence"]["registry_version"]
    cur = R.load()["parameters"]["active_ladder"]; other = "A" if cur == "B" else "B"
    ceil = {"A": 0.70, "B": 0.80}
    R.set_active_ladder(other)
    pa = R.load()["parameters"]
    assert pa["active_ladder"] == other and pa["rho_bio_ceiling"] == ceil[other] and max(r["value"] for r in pa["rho_bio_ladder"]) == ceil[other]
    assert cur in pa["ladder_alternatives"] and R.validate() == [] and R.load()["evidence"]["registry_version"] != v0
    assert R.ladder_face_validity("kawaguchi2010", ladder=cur)[0]["ladder"] == cur
    R.lock()
    with pytest.raises(ValueError, match="locked"):
        R.set_active_ladder(cur)


def test_lock_also_covers_engine_code(tmp_path, monkeypatch):
    pkg = tmp_path / "pkg"; shutil.copytree(os.path.dirname(os.path.dirname(R.REG_DIR)), pkg, ignore=shutil.ignore_patterns("__pycache__"))
    monkeypatch.setattr(R, "REG_DIR", str(pkg / "oncology" / "registry"))
    monkeypatch.setattr(R, "LOCK_FILE", str(pkg / "oncology" / "registry" / "prereg_lock.json"))
    R.lock(); assert R.validate() == [] and set(R.code_hashes()) == set(R.CODE_FILES)
    f = pkg / "oncology" / "rmti_lung.py"
    f.write_bytes(f.read_bytes().replace(b"\n", b"\r\n"))                      # a Windows checkout must NOT trip the lock
    assert R.validate() == []
    f.write_text(f.read_text() + "\nV_RANGE_CHANGED = 1\n")                     # a real edit must
    assert any("engine code changed" in x and "rmti_lung.py" in x for x in R.validate())


def test_missing_registry_gives_a_clear_error(tmp_path, monkeypatch):
    monkeypatch.setattr(R, "REG_DIR", str(tmp_path / "nope"))
    with pytest.raises(FileNotFoundError, match="RMTI_REGISTRY_DIR"):
        R.load()
    import subprocess
    r = subprocess.run([sys.executable, os.path.join(os.path.dirname(R.__file__), "registry.py"), "validate"],
                       env=dict(os.environ, RMTI_REGISTRY_DIR=str(tmp_path / "nope")), capture_output=True, text=True)
    assert r.returncode != 0 and "ERROR: registry file not found" in r.stderr and "Traceback" not in r.stderr
