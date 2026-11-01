"""Cohort sandboxes (HCC, lung, breast): framework-free, like service.py. The Streamlit pages and the FastAPI router both call run().

Adds NO equation. Scoring goes through the vendored engine: HCC through rmti_hcc_cohort.score_cohort (the Excel calculator v2.4.1), lung
through rmti_lung helpers + combine_rho + core.score, breast through core.score on user-supplied L, E, V, rho. Outcome statistics
(cumulative incidence with a competing event, Harrell C, crude rates) are descriptive and sit on top of the scores.

Event coding for every disease: cause = 1 event of interest, 2 competing event (e.g. death without the cancer), 0 censored.
A column named 'event' (0/1) is accepted as an alias for cause.
"""
import glob
import hashlib
import json
import os

import numpy as np
import pandas as pd

import service as S                      # adds rmti_engine to sys.path and imports the engine
import registry as R
from core.rmti_core import score
from oncology.rmti_hcc import short_tier
from oncoclastics.rmti_oncoclastics import combine_rho

HERE = os.path.dirname(os.path.abspath(__file__))
HCC, LUNG = S.HCC_COHORT, S.LUNG
MAX_ROWS = 50_000
COHORT_DIR = os.environ.get("RMTI_COHORT_DIR") or os.path.join(HERE, "cohort_data")   # may point outside the repo (a mounted volume) to keep data out of git
OUTCOME_COLS = ["time_years", "cause", "stratum"]

DISEASES = {
    "hcc": dict(label="HCC", status="Published application. Patient-level from routine labs (ALBI for V, aMAP-ref for L), as the Excel calculator v2.4.1.",
                template=["patient_id", "etiology", "age_years", "male", "albumin_g_l", "bilirubin_umol_l", "platelets_1e9_l", "time_years", "cause"],
                required=list(HCC.REQUIRED),
                notes="male: 1/0. albumin g/L, bilirubin umol/L, platelets 10^9/L. etiology and stratum are optional groupings."),
    "lung": dict(label="Lung cancer", status="Proposed extension, not part of the published RMTI papers. L from a validated 5-YEAR risk tool; anchors are placeholders.",
                 template=["patient_id", "risk5", "v_count", "ecog", "rho_care", "E", "stratum", "time_years", "cause"],
                 required=["risk5", "v_count"],
                 notes="risk5: 5-year risk as a FRACTION (0.025 = 2.5%). 2-year risks are refused (risk_horizon_years column, if present, must be 5). "
                       "v_count: number of V items present (0-4) that the L tool does not already contain. ecog 0-4 optional (rho_bio, provisional ladder). "
                       "rho_care and E optional per-patient columns, otherwise the settings values are used."),
    "breast": dict(label="Breast cancer", status="SCAFFOLD ONLY. No breast instruments or anchors exist in the engine, and none are invented here. You supply L, E, V, rho per patient from your own pre-registered mapping.",
                   template=["patient_id", "L", "V", "E", "rho", "stratum", "time_years", "cause"],
                   required=["L", "V"],
                   notes="L, V (and optional E, rho = ρ) must already be on 0-1 (ρ on 0 to <1; a header written as ρ also works). E and ρ fall back to the settings values when the column is absent. "
                         "No variable may feed two terms: declare the variables behind L and behind V in the settings and overlaps are refused. "
                         "Add a disease-specific module (README: 'add a disease by writing a new module') before reporting results."),
}
ANCHORS = HCC.L_ANCHOR_SETS
TIER_SHORT = ["1 Low", "2 Moderate", "3 High", "4 Severe", "5 Critical"]


def defaults(disease):
    d = dict(E=0.60, rho=0.20, rho_after=0.65, C=5, horizons=[5, 10], bootstrap=0)
    if disease == "hcc":
        d.update(l_tool="aMAP-ref", allow_overlap=False, anchors="primary", albi_ref=float(HCC.ALBI_REF))
    if disease == "lung":
        d.update(rho_after=0.50, use_rho_bio=True, ladder=None)
    if disease == "breast":
        d.update(rho_after=0.50, declared_l_variables=[], declared_v_variables=[])
    return d


def templates():
    return {k: dict(columns=v["template"], required=v["required"], status=v["status"], notes=v["notes"], defaults=defaults(k))
            for k, v in DISEASES.items()}


# ---------------------------------------------------------------- data in
def _norm_col(c):
    """Column names are case-insensitive; a Greek rho in a header is accepted (ρ_care -> rho_care). Wire names stay ASCII."""
    c = str(c).strip().replace("ρ", "rho").replace("₀", "0")
    return {"l": "L", "v": "V", "e": "E"}.get(c.lower(), c.lower())


def _infer_disease(cols):
    c = {_norm_col(x) for x in cols}
    if set(HCC.REQUIRED) <= c:
        return "hcc"
    if {"risk5", "v_count"} <= c:
        return "lung"
    if {"L", "V"} <= c:
        return "breast"
    return None


def datasets():
    """Bundled cohorts: every *.csv in cohort_data/ (or RMTI_COHORT_DIR). Drop a file in to add a cohort, replace it to update, delete it to remove.
    Optional sidecar <name>.meta.json: id, disease, label, description, reference_file. Without it the id is the file name and the disease is
    inferred from the columns (HCC lab columns, lung risk5 + v_count, breast L + V)."""
    out = {}
    for path in sorted(glob.glob(os.path.join(COHORT_DIR, "*.csv"))):
        stem = os.path.basename(path)[:-4]
        mp = os.path.join(COHORT_DIR, stem + ".meta.json")
        try:
            meta = json.load(open(mp)) if os.path.exists(mp) else {}
            cols = list(pd.read_csv(path, nrows=0).columns)
        except Exception:
            continue                                          # unreadable file or metadata: not offered
        disease = meta.get("disease") or _infer_disease(cols)
        if disease not in DISEASES:
            continue
        ref = os.path.join(COHORT_DIR, meta["reference_file"]) if meta.get("reference_file") else None
        cid = meta.get("id", stem)
        out[cid] = dict(id=cid, disease=disease, path=path, label=meta.get("label", cid), description=meta.get("description", ""),
                        reference=ref if ref and os.path.exists(ref) else None)
    return out


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_dataset(name):
    d = datasets().get(name)
    if d is None:
        raise ValueError("unknown dataset %r; available: %s" % (name, sorted(datasets())))
    return d, S.privacy_check(pd.read_csv(d["path"]))          # the identifier guard also runs on bundled files


def dataset_reference(name):
    d = datasets().get(name)
    return json.load(open(d["reference"])) if d and d["reference"] else None


def _prepare(df):
    df = df.copy()
    if len(df) == 0:
        raise ValueError("no rows to score")
    if len(df) > MAX_ROWS:
        raise ValueError("at most %d rows per request" % MAX_ROWS)
    df.columns = [_norm_col(c) for c in df.columns]
    if "cause" not in df.columns and "event" in df.columns:
        df["cause"] = df["event"]
    if "patient_id" not in df.columns:
        df.insert(0, "patient_id", ["row%05d" % i for i in range(1, len(df) + 1)])
    if "cause" in df.columns:
        c = pd.to_numeric(df["cause"], errors="coerce")
        bad = c.notna() & ~c.isin([0, 1, 2])
        if bad.any():
            raise ValueError("cause must be 0 (censored), 1 (event) or 2 (competing event); bad rows: %s" % list(df.index[bad][:5] + 1))
        df["cause"] = c
    return df


def _need(df, cols):
    miss = [c for c in cols if c not in df.columns]
    if miss:
        raise ValueError("missing columns: %s" % miss)


def _num(df, col, lo=None, hi=None, hi_open=False, integer=False):
    x = pd.to_numeric(df[col], errors="coerce")
    bad = x.isna()
    if lo is not None:
        bad |= x < lo
    if hi is not None:
        bad |= (x >= hi) if hi_open else (x > hi)
    if integer:
        bad |= (x != x.round())
    if bad.any():
        rows = list(df.index[bad][:5] + 1)
        raise ValueError("column %s has missing or out-of-range values (rows %s%s)" % (col, rows, ", ..." if bad.sum() > 5 else ""))
    return x.astype(float)


# ---------------------------------------------------------------- scoring
def _finish(df, L, V, E, rho, rho_after, C, extra):
    """Common tail: core.score() per patient on L, E, V, rho (and rho_after)."""
    now = [score(float(l), float(e), float(v), float(r), C) for l, e, v, r in zip(L, E, V, rho)]
    aft = [score(float(l), float(e), float(v), float(r), C) for l, e, v, r in zip(L, E, V, rho_after)]
    out = df.copy()
    out["L"], out["V"], out["E"], out["rho"] = np.asarray(L), np.asarray(V), np.asarray(E), np.asarray(rho)
    out["R_raw"] = [s["R_raw"] for s in now]
    out["R"] = [s["R"] for s in now]
    out["tier"] = [short_tier(s["R_raw"]) for s in now]
    out["R_after"] = [s["R"] for s in aft]
    out["tier_after"] = [short_tier(s["R_raw"]) for s in aft]
    out["EAL"] = [s["EAL"] for s in now]
    for k, v in extra.items():
        out[k] = v
    return out


def _score_hcc(df, o):
    if o["anchors"] not in ANCHORS:
        raise ValueError("anchors must be one of %s" % sorted(ANCHORS))
    _need(df, HCC.REQUIRED)
    d = df.copy()
    for c, lo, hi in (("age_years", 18, 110), ("albumin_g_l", 1, 70), ("bilirubin_umol_l", 0.1, 1000), ("platelets_1e9_l", 0, 2000)):
        d[c] = _num(d, c, lo, hi)
    d["male"] = _num(d, "male", 0, 1, integer=True).astype(int)
    r = HCC.score_cohort(d, l_tool=o["l_tool"], E=o["E"], rho=o["rho"], rho_after=o["rho_after"], C=int(o["C"]),
                         l_anchors=ANCHORS[o["anchors"]], albi_ref=float(o["albi_ref"]), allow_overlap=bool(o["allow_overlap"]))
    r = r.rename(columns={"amap_group": "risk_group"})
    r["rho"], r["E"] = o["rho"], o["E"]
    return r


def _score_lung(df, o):
    _need(df, ["risk5", "v_count"])
    risk = _num(df, "risk5", 0, 1)
    if (risk > 0.5).mean() > 0.5:
        raise ValueError("risk5 looks like percentages; enter 5-year risk as a fraction (0.025 = 2.5%)")
    hz = _num(df, "risk_horizon_years", 1, 50) if "risk_horizon_years" in df.columns else pd.Series(5.0, index=df.index)
    y = _num(df, "v_count", 0, len(LUNG.V_ITEMS), integer=True)
    L = [LUNG.l_from_risk(float(r), int(h)) for r, h in zip(risk, hz)]
    V = [LUNG.v_from_indicator(v) for v in y]
    E = _num(df, "E", 0, 1) if "E" in df.columns else pd.Series(o["E"], index=df.index)
    care = _num(df, "rho_care", 0, 1, hi_open=True) if "rho_care" in df.columns else pd.Series(o["rho"], index=df.index)
    if o.get("use_rho_bio") and "ecog" in df.columns:
        eg = _num(df, "ecog", 0, 4, integer=True)
        rb = pd.Series([LUNG.rho_bio_from_ecog(int(e), o.get("ladder")) for e in eg], index=df.index)
    else:
        rb = pd.Series(0.0, index=df.index)
    rho = [combine_rho(float(b), float(c)) for b, c in zip(rb, care)]
    after = [combine_rho(float(b), float(o["rho_after"])) for b in rb]
    ex = {"rho_bio": rb.values, "rho_care": care.values, "status": "PROVISIONAL: lung anchors and rho_bio ladder are placeholders"}
    return _finish(df, L, V, E, rho, after, int(o["C"]), ex)


def _score_breast(df, o):
    _need(df, ["L", "V"])
    clash = sorted(set(map(str.lower, o.get("declared_l_variables") or [])) & set(map(str.lower, o.get("declared_v_variables") or [])))
    if clash:
        raise ValueError("REFUSED: variable(s) %s are declared in both L and V, so they would be counted twice." % clash)
    L, V = _num(df, "L", 0, 1), _num(df, "V", 0, 1)
    E = _num(df, "E", 0, 1) if "E" in df.columns else pd.Series(o["E"], index=df.index)
    rho = _num(df, "rho", 0, 1, hi_open=True) if "rho" in df.columns else pd.Series(o["rho"], index=df.index)
    after = pd.Series(o["rho_after"], index=df.index)
    return _finish(df, L, V, E, rho, after, int(o["C"]),
                   {"status": "SCAFFOLD: L, E, V, rho supplied by the user; no engine anchors"})


SCORERS = {"hcc": _score_hcc, "lung": _score_lung, "breast": _score_breast}


# ---------------------------------------------------------------- outcome statistics (descriptive)
def cumulative_incidence(time, cause, horizons):
    """Aalen-Johansen cumulative incidence of cause 1 with cause 2 as a competing event, at each horizon (years)."""
    t, c = np.asarray(time, float), np.asarray(cause, int)
    o = np.argsort(t, kind="stable")
    t, c = t[o], c[o]
    n = len(t)
    m = c > 0
    if not m.any():
        return {h: 0.0 for h in horizons}
    u, inv = np.unique(t[m], return_inverse=True)
    d1 = np.bincount(inv, weights=(c[m] == 1).astype(float), minlength=len(u))
    d2 = np.bincount(inv, weights=(c[m] == 2).astype(float), minlength=len(u))
    at_risk = n - np.searchsorted(t, u, side="left")
    surv_prev = np.concatenate([[1.0], np.cumprod(1 - (d1 + d2) / at_risk)[:-1]])
    cif = np.cumsum(surv_prev * d1 / at_risk)
    out = {}
    for h in horizons:
        i = np.searchsorted(u, h, side="right") - 1
        out[h] = float(cif[i]) if i >= 0 else 0.0
    return out


def _c_index(res):
    return S.c_index(res["time_years"].values, (res["cause"] == 1).astype(int).values, res["R_raw"].values)


def _bootstrap_c(res, B, seed=1):
    rng = np.random.default_rng(seed)
    t, e, r = res["time_years"].values, (res["cause"] == 1).astype(int).values, res["R_raw"].values
    n, d = len(res), []
    for _ in range(B):
        i = rng.integers(0, n, n)
        c = S.c_index(t[i], e[i], r[i])
        if not np.isnan(c):
            d.append(c)
    return [float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))] if len(d) >= B * 0.5 else None


def outcomes(res, horizons=(5, 10), bootstrap=0):
    """Descriptive outcome report. Returns None if the file has no time/cause columns."""
    if not {"time_years", "cause"} <= set(res.columns):
        return None
    r = res.dropna(subset=["time_years", "cause"]).copy()
    r["time_years"] = pd.to_numeric(r["time_years"], errors="coerce")
    r = r[r["time_years"] > 0]
    if len(r) == 0:
        return None
    r["cause"] = r["cause"].astype(int)
    py = float(r["time_years"].sum())
    out = {"n": len(r), "events": int((r.cause == 1).sum()), "competing": int((r.cause == 2).sum()),
           "censored": int((r.cause == 0).sum()), "person_years": py,
           "crude_per_100py": 100 * float((r.cause == 1).sum()) / py}
    rows = []
    for t in sorted(r["tier"].unique()):
        g = r[r.tier == t]
        cif = cumulative_incidence(g.time_years, g.cause, horizons)
        row = {"tier": t, "n": len(g), "events": int((g.cause == 1).sum()), "competing": int((g.cause == 2).sum()),
               "person_years": float(g.time_years.sum())}
        row["crude_per_100py"] = 100 * row["events"] / row["person_years"]
        row.update({"cif_%gy" % h: v for h, v in cif.items()})
        rows.append(row)
    out["by_tier"] = rows
    if (r.cause == 1).any() and (r.cause != 1).any():
        out["c_index"] = _c_index(r)
        out["c_index_note"] = "Harrell C of R for the event of interest; competing events treated as censored (as in the workbook's Python run)."
        if bootstrap:
            out["c_index_ci95"] = _bootstrap_c(r, int(bootstrap))
    if "stratum" in r.columns and r["stratum"].notna().any():
        srows = []
        for k, g in r.groupby(r["stratum"].astype(str)):
            ev = int((g.cause == 1).sum())
            ok = ev >= 10 and g["cause"].nunique() > 1
            srows.append({"stratum": k, "n": len(g), "events": ev, "c_index": _c_index(g) if ok else None,
                          "note": "" if ok else "withheld: fewer than 10 events"})
        out["by_stratum"] = srows
    return out


# ---------------------------------------------------------------- HCC extras and verification against the workbook
def hcc_extras(res, o):
    ex = {}
    ex["observed_vs_published"] = None
    if {"time_years", "cause"} <= set(res.columns):
        g = res.groupby("risk_group").agg(n=("R_raw", "size"), events=("cause", lambda s: int((s == 1).sum())), person_years=("time_years", "sum"))
        g["observed_per_100py"] = 100 * g["events"] / g["person_years"]
        g["published_low_per_100py"] = [100 * HCC.AMAP_GROUP_RANGE[i][0] for i in g.index]
        g["published_high_per_100py"] = [100 * HCC.AMAP_GROUP_RANGE[i][1] for i in g.index]
        g["inside_published_range"] = (g.observed_per_100py >= g.published_low_per_100py) & (g.observed_per_100py <= g.published_high_per_100py)
        ex["observed_vs_published"] = _rec(g.reset_index())
    if "etiology" in res.columns:
        rows = []
        for k, g in [("All", res)] + list(res.groupby("etiology")):
            mL, mV = float(g["L"].mean()), float(g["V"].mean())
            s0, s1 = score(mL, o["E"], mV, o["rho"], int(o["C"])), score(mL, o["E"], mV, o["rho_after"], int(o["C"]))
            row = {"etiology": k, "n": len(g), "mean_L": mL, "mean_V": mV, "R_now": s0["R"], "tier_now": short_tier(s0["R_raw"]),
                   "R_after": s1["R"], "tier_after": short_tier(s1["R_raw"])}
            if {"time_years", "cause"} <= set(g.columns):
                row.update(events=int((g.cause == 1).sum()), person_years=float(g.time_years.sum()))
                row["crude_per_100py"] = 100 * row["events"] / row["person_years"]
            rows.append(row)
        ex["by_etiology"] = rows
        ex["by_etiology_note"] = "Unchanged equations applied to cohort means, as Table 1 of the preprint and Japan_Summary of the workbook."
    return ex


def verify_against_workbook(d, res, opt, out):
    """For the bundled cohort at the reference settings, compare with the workbook's Python run (Checks sheet)."""
    if not d.get("reference"):
        return None
    ref = json.load(open(d["reference"]))
    if ref.get("data_sha256") and ref["data_sha256"] != file_sha256(d["path"]):
        return {"note": "The cohort file has changed since the reference values were computed, so no comparison is made. Replace or remove the reference file to silence this.", "checks": []}
    if any(opt.get(k) != v for k, v in ref["config"].items()):
        return {"note": "Settings differ from the reference run (%s), so no comparison is made." % ref["config"], "checks": []}
    ex = out["extras"]["by_etiology"][0]
    tn, ta = res["tier"].value_counts(), res["tier_after"].value_counts()
    chk = [("Patients", len(res), ref["n"]), ("Incident HCC", int((res.cause == 1).sum()), ref["incident_hcc"]),
           ("Cohort R now", ex["R_now"], ref["cohort_R_now"]), ("Cohort R after", ex["R_after"], ref["cohort_R_after"]),
           ("Mean L", ex["mean_L"], ref["mean_L"]), ("Mean V", ex["mean_V"], ref["mean_V"])]
    chk += [("Tier %s (rho now)" % k, int(tn.get(k, 0)), v) for k, v in ref["tier_now"].items()]
    chk += [("Tier %s (rho after)" % k, int(ta.get(k, 0)), v) for k, v in ref["tier_after"].items()]
    bt = {r["tier"]: r for r in out["outcomes"]["by_tier"]}
    for k, d in ref["cif_hcc_by_tier"].items():
        for h, v in d.items():
            chk.append(("Cumulative incidence, %s, %s-year" % (k, h), bt[k]["cif_%sy" % h], v))
    chk.append(("Harrell C of R (full follow-up)", out["outcomes"].get("c_index"), ref["harrell_c_R_clean_full_followup"]))
    rows = [{"check": n, "computed": c, "reference": r, "difference": None if c is None else c - r,
             "result": "PASS" if c is not None and abs(c - r) <= (0.0005 if isinstance(r, float) and r < 1 else 0) + 1e-9 else "CHECK"} for n, c, r in chk]
    return {"source": ref["source"], "checks": rows, "overall": "ALL PASS" if all(x["result"] == "PASS" for x in rows) else "REVIEW"}


# ---------------------------------------------------------------- public entry point
def _rec(df):
    return json.loads(df.to_json(orient="records"))      # NaN -> null, numpy -> python


def run(disease, records=None, dataset=None, options=None):
    """Score a cohort and report. Give either records (list of dicts) or dataset (bundled name). Returns a JSON-serialisable dict."""
    if disease not in DISEASES:
        raise ValueError("disease must be one of %s" % sorted(DISEASES))
    opt = {**defaults(disease), **(options or {})}
    unknown = sorted(set(opt) - set(defaults(disease)))
    if unknown:
        raise ValueError("unknown option(s) for %s: %s" % (disease, unknown))
    if (records is None) == (dataset is None):
        raise ValueError("give exactly one of records or dataset")
    if dataset:
        d, df = load_dataset(dataset)
        if d["disease"] != disease:
            raise ValueError("dataset %r belongs to %s, not %s" % (dataset, d["disease"], disease))
        bundled = True
    else:
        df = S.privacy_check(pd.DataFrame(records))
        bundled = False
    res = SCORERS[disease](_prepare(df), opt)
    n = len(res)
    cnt = lambda col: res[col].value_counts().reindex(TIER_SHORT, fill_value=0)
    now, aft = cnt("tier"), cnt("tier_after")
    tiers = [{"tier": t, "patients_now": int(now[t]), "pct_now": round(100 * now[t] / n, 1),
              "patients_after": int(aft[t]), "pct_after": round(100 * aft[t] / n, 1)} for t in now.index]
    out = {"disease": disease, "label": DISEASES[disease]["label"], "status": DISEASES[disease]["status"], "n": n, "options": opt,
           "dataset": dataset, "tiers": tiers, "mean": {k: float(res[k].mean()) for k in ("L", "V", "E", "rho", "R_raw", "R_after", "EAL")},
           "outcomes": outcomes(res, opt["horizons"], opt["bootstrap"]), "extras": {}, "verification": None,
           "disclaimer": S.DISCLAIMER,
           "audit": {"engine": S.ENGINE_VERSION, "registry": R.stamp(), "bundled_dataset": ({"id": dataset, "label": d["label"], "file": os.path.basename(d["path"]),
                     "sha256": file_sha256(d["path"]), "rows": len(df)} if dataset else None)}}
    if "status" in res.columns:
        out["score_status"] = sorted(res["status"].unique())
    if disease == "hcc":
        out["extras"] = hcc_extras(res, opt)
        if dataset and out["outcomes"]:
            out["verification"] = verify_against_workbook(d, res, opt, out)
    export = (not bundled) or os.environ.get("RMTI_ALLOW_COHORT_EXPORT") == "1"
    out["patients"] = _rec(res) if export else None
    out["patients_note"] = None if export else "Patient-level rows of the bundled cohort are not returned (set RMTI_ALLOW_COHORT_EXPORT=1 on the server to allow it)."
    return out


def demo_records(disease, n=300, seed=11):
    """SYNTHETIC rows to test the pipeline (random numbers, no meaning)."""
    r = np.random.default_rng(seed)
    base = {"patient_id": ["DEMO%04d" % i for i in range(n)], "stratum": r.choice(["A", "B"], n)}
    risk = r.beta(1.2, 6, n)
    t = r.exponential(6, n).round(2) + 0.1
    cause = np.where(r.random(n) < 0.15 + 0.5 * risk, 1, np.where(r.random(n) < 0.15, 2, 0))
    base.update(time_years=t, cause=cause)
    if disease == "hcc":
        base.update(age_years=r.normal(62, 10, n).clip(30, 90).round(1), male=r.integers(0, 2, n), albumin_g_l=r.normal(40, 5, n).clip(20, 52).round(),
                    bilirubin_umol_l=r.lognormal(2.7, 0.5, n).clip(3, 120).round(1), platelets_1e9_l=r.normal(160, 60, n).clip(30, 450).round())
    elif disease == "lung":
        base.update(risk5=(0.005 + 0.12 * risk).round(4), v_count=r.integers(0, 5, n), ecog=r.choice([0, 1, 2], n, p=[.6, .3, .1]))
    else:
        base.update(L=risk.clip(0, 1).round(3), V=r.beta(2, 3, n).round(3), E=r.uniform(.4, .9, n).round(2), rho=r.uniform(0, .5, n).round(2))
    return _rec(pd.DataFrame(base))
