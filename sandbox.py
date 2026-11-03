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
import rmti_breast as BR
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
                notes="male: 1/0. albumin g/L, bilirubin umol/L, platelets 10^9/L. etiology and stratum are optional groupings. Optional tumour columns, filled only for patients who developed HCC (blank = not recorded): "
                      "max_diameter_cm, n_nodules, vp (portal-vein invasion grade, 0 = none), and afp_ng_ml / dcp_ng_ml only if measured AT diagnosis. No tumour LOCATION is modelled."),
    "lung": dict(label="Lung cancer", status="Proposed extension, not part of the published RMTI papers. L from a validated 5-YEAR risk tool; anchors are placeholders.",
                 template=["patient_id", "risk5", "v_count", "ecog", "rho_care", "E", "stratum", "time_years", "cause"],
                 required=["risk5", "v_count"],
                 notes="risk5: 5-year risk as a FRACTION (0.025 = 2.5%). 2-year risks are refused (risk_horizon_years column, if present, must be 5). "
                       "v_count: number of V items present (0-4) that the L tool does not already contain. ecog 0-4 optional (rho_bio, provisional ladder). "
                       "rho_care and E optional per-patient columns, otherwise the settings values are used."),
    "breast": dict(label="Breast cancer (female)", status="PROPOSED SCAFFOLD. L comes from a validated 5-year risk tool with PLACEHOLDER anchors (rmti_breast.py); there is no V-item list and no rho_bio ladder yet, so you supply V, E and rho from your own pre-registered mapping.",
                   template=["patient_id", "risk5", "V", "E", "rho", "sex", "prior_breast_cancer", "stratum", "time_years", "cause"],
                   required=["V", "risk5 (or L)"],
                   notes="risk5: 5-year invasive breast-cancer risk as a FRACTION from a validated tool (BCRAT, BCSC...); other horizons are refused. Or give L directly (0-1). V, and optional E and rho (= ρ), on 0-1 (ρ below 1). "
                         "sex, if present, must be female; prior_breast_cancer = 1 rows are refused (the tools are not valid for them). No variable may feed two terms: declare the variables behind L and V in the settings and overlaps are refused."),
    "imaging": dict(label="Imaging ROI features (research scaffold)", status="SCAFFOLD ONLY. Scores a table of features that someone has ALREADY extracted from an already-segmented region (for example offline with PyRadiomics). It cannot find a tumour and it does not diagnose. You must give every anchor; none is assumed. R is a relative score on the platform's fixed tiers, not a probability of malignancy.",
                    template=["patient_id", "roi_id", "label", "split"],
                    required=["one numeric column for each of L, E, V and rho, chosen in the settings"],
                    notes="Add one column per feature you map (any names). label (optional): 1 = malignant, 0 = benign, by pathology. split (optional): dev or test; anchors chosen on the same rows you validate on inflate performance. "
                          "Rows with a missing or non-numeric value in a mapped column are EXCLUDED and counted, never treated as zero."),
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
        d.update(rho_after=0.50, declared_l_variables=[], declared_v_variables=[], r_lo=BR.L_ANCHORS["r_lo"], r_hi=BR.L_ANCHORS["r_hi"])
    if disease == "imaging":
        d.update(mapping=None, rho_after=None, validation_bootstrap=0)
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
    if {"V"} <= c and ({"L"} <= c or {"risk5"} <= c):
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


def _rows(df, mask):
    r = list(df.index[mask][:5] + 1)
    return "%s%s" % (r, ", ..." if mask.sum() > 5 else "")


def _score_breast(df, o):
    clash = sorted(set(map(str.lower, o.get("declared_l_variables") or [])) & set(map(str.lower, o.get("declared_v_variables") or [])))
    if clash:
        raise ValueError("REFUSED: variable(s) %s are declared in both L and V, so they would be counted twice." % clash)
    if "sex" in df.columns:
        notf = ~df["sex"].astype(str).str.strip().str.lower().isin(["f", "female", "woman"])
        if notf.any():
            raise ValueError("This is the FEMALE breast-cancer sandbox; rows with sex other than female: %s" % _rows(df, notf))
    if "prior_breast_cancer" in df.columns:
        prior = pd.to_numeric(df["prior_breast_cancer"], errors="coerce").fillna(0) == 1
        if prior.any():
            raise ValueError("REFUSED: the validated 5-year risk tools are not valid after a previous breast cancer, DCIS or LCIS (rows %s)." % _rows(df, prior))
    _need(df, ["V"])
    if "L" in df.columns:
        L = _num(df, "L", 0, 1)
    elif "risk5" in df.columns:
        risk = _num(df, "risk5", 0, 1)
        if (risk > 0.5).mean() > 0.5:
            raise ValueError("risk5 looks like percentages; enter the 5-year risk as a fraction (0.0167 = 1.67%)")
        hz = _num(df, "risk_horizon_years", 1, 50) if "risk_horizon_years" in df.columns else pd.Series(5.0, index=df.index)
        L = pd.Series([BR.l_from_risk(float(r), int(h), o.get("r_lo"), o.get("r_hi")) for r, h in zip(risk, hz)], index=df.index)
    else:
        raise ValueError("missing columns: give risk5 (5-year risk, fraction) or L (0-1)")
    V = _num(df, "V", 0, 1)
    E = _num(df, "E", 0, 1) if "E" in df.columns else pd.Series(o["E"], index=df.index)
    rho = _num(df, "rho", 0, 1, hi_open=True) if "rho" in df.columns else pd.Series(o["rho"], index=df.index)
    after = pd.Series(o["rho_after"], index=df.index)
    return _finish(df, L, V, E, rho, after, int(o["C"]),
                   {"status": "SCAFFOLD: L from a validated 5-year risk with PLACEHOLDER anchors; V, E, rho supplied by the user"})


def _wilson(k, n, z=1.96):
    if n == 0:
        return [None, None]
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return [max(0.0, c - h), min(1.0, c + h)]


def auc(y, s):
    """Mann-Whitney AUC; ties count one half. y in {0,1}."""
    y = np.asarray(y, int)
    s = pd.Series(np.asarray(s, float))
    n1, n0 = int(y.sum()), int((1 - y).sum())
    if n1 == 0 or n0 == 0:
        return None
    r = s.rank().values
    return float((r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def _score_imaging(df, o):
    mp = o.get("mapping")
    terms = ["L", "E", "V", "rho"]
    if not isinstance(mp, dict) or any(t not in mp for t in terms):
        raise ValueError("options.mapping is required: for each of L, E, V, rho give {column, lo, hi, invert}. No anchor is assumed.")
    cfg = {}
    for t in terms:
        m = mp[t]
        if not isinstance(m, dict) or "column" not in m or "lo" not in m or "hi" not in m:
            raise ValueError("mapping.%s needs column, lo and hi" % t)
        lo, hi = float(m["lo"]), float(m["hi"])
        if not hi > lo:
            raise ValueError("mapping.%s: hi must be greater than lo" % t)
        cfg[t] = dict(column=_norm_col(m["column"]) if _norm_col(m["column"]) in df.columns else str(m["column"]), lo=lo, hi=hi, invert=bool(m.get("invert", False)))
    cols = [cfg[t]["column"] for t in terms]
    dup = sorted({c for c in cols if cols.count(c) > 1})
    if dup:
        raise ValueError("REFUSED: column(s) %s would feed more than one term, so they would be counted twice." % dup)
    _need(df, cols)
    raw = pd.DataFrame({t: pd.to_numeric(df[cfg[t]["column"]], errors="coerce") for t in terms}, index=df.index)
    bad = raw.isna().any(axis=1)
    if bad.all():
        raise ValueError("no row has a numeric value in all four mapped columns")
    scaled, clipped = {}, {}
    for t in terms:
        c = cfg[t]
        x = (raw[t] - c["lo"]) / (c["hi"] - c["lo"])
        clipped[t] = int(((x < 0) | (x > 1))[~bad].sum())
        x = x.clip(0, 1)
        scaled[t] = (1 - x) if c["invert"] else x
    capped = int((scaled["rho"][~bad] > 0.99).sum())
    keep = ~bad
    d = df[keep]
    sc = {t: scaled[t][keep] for t in terms}
    sc["rho"] = sc["rho"].clip(upper=0.99)
    after = sc["rho"]
    res = _finish(d, sc["L"], sc["V"], sc["E"], sc["rho"], after, int(o["C"]),
                  {"status": "SCAFFOLD: features mapped with user-supplied anchors; research only, not a diagnosis"})
    corr = raw[keep].corr(method="spearman")
    pairs = [{"terms": [a, b], "columns": [cfg[a]["column"], cfg[b]["column"]], "spearman": float(corr.loc[a, b])}
             for i, a in enumerate(terms) for b in terms[i + 1:] if abs(corr.loc[a, b]) >= 0.7]
    info = {"mapping": cfg, "rows_in": int(len(df)), "rows_scored": int(keep.sum()), "rows_excluded_missing": int(bad.sum()),
            "excluded_row_numbers": [int(i) + 1 for i in df.index[bad][:10]], "values_clipped_to_anchors": clipped, "rho_capped_at_0.99": capped,
            "correlated_term_pairs": pairs,
            "warnings": (["%d row(s) excluded: a mapped column was missing or not numeric (never treated as zero)" % int(bad.sum())] if bad.any() else [])
                        + (["Source columns of different terms are strongly rank-correlated (|rho| >= 0.7); the product may count the same signal twice"] if pairs else [])
                        + ["Values outside the anchors are clipped to 0 or 1; check how many (values_clipped_to_anchors)"] * int(any(clipped.values()))}
    if "label" in res.columns:
        y = pd.to_numeric(res["label"], errors="coerce")
        ok = y.isin([0, 1])
        if ok.sum() and y[ok].nunique() == 2:
            r = res[ok].assign(_y=y[ok].astype(int))
            parts = {"all rows": r}
            if "split" in r.columns:
                for k in ("dev", "test"):
                    g = r[r["split"].astype(str).str.lower() == k]
                    if len(g):
                        parts[k] = g
            v = {}
            for name, g in parts.items():
                terms_auc = {"R": auc(g["_y"], g["R_raw"]), "L alone": auc(g["_y"], g["L"]), "E alone": auc(g["_y"], g["E"]),
                             "V alone": auc(g["_y"], g["V"]), "1 - rho alone": auc(g["_y"], 1 - g["rho"]),
                             "simple mean of the four terms": auc(g["_y"], (g["L"] + g["E"] + g["V"] + (1 - g["rho"])) / 4)}
                v[name] = {"n": int(len(g)), "malignant": int(g["_y"].sum()), "auc": terms_auc}
            tb = []
            for t in sorted(r["tier"].unique()):
                g = r[r.tier == t]
                tb.append({"tier": t, "n": int(len(g)), "malignant": int(g["_y"].sum()), "proportion_malignant": float(g["_y"].mean()),
                           "wilson95": _wilson(int(g["_y"].sum()), int(len(g)))})
            first = "dev" if "dev" in v else "all rows"
            wrong = [{"term": k_, "auc": round(a_, 3), "message": "%s ranks BENIGN above malignant (AUC %.2f on %s rows). Check the 'invert' box for that term, or the choice of column." % (k_, a_, first)}
                     for k_, a_ in v[first]["auc"].items() if k_ in ("L alone", "E alone", "V alone", "1 - rho alone") and a_ is not None and a_ < 0.4]
            info["validation"] = {"by_split": v, "by_tier": tb, "direction_warnings": wrong,
                                  "note": ("No split column: anchors chosen on these same rows make every AUC optimistic." if "split" not in r.columns else
                                           "dev rows may be used to choose anchors; only the test rows are an honest estimate."),
                                  "reading": "AUC says how well the score ranks malignant above benign in THIS file. It is not a probability, and it is not a validation unless the anchors were fixed before looking at the test rows."}
    res.attrs["imaging"] = info
    return res


SCORERS = {"hcc": _score_hcc, "lung": _score_lung, "breast": _score_breast, "imaging": _score_imaging}


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
    tum = [c for c in ("max_diameter_cm", "n_nodules", "vp", "afp_ng_ml", "dcp_ng_ml") if c in res.columns]
    if tum and "cause" in res.columns:
        cases = res[res["cause"] == 1]
        rows = []
        pct = lambda mask, known: (float(100 * mask[known].mean()), int(known.sum())) if known.any() else (None, 0)   # percentage among patients WITH a recorded value
        for t in sorted(cases["tier"].unique()):
            g = cases[cases.tier == t]
            row = {"baseline_tier": t, "cases": int(len(g))}
            if "max_diameter_cm" in g:
                sz = pd.to_numeric(g["max_diameter_cm"], errors="coerce")
                row["median_diameter_cm"] = float(sz.median()) if sz.notna().any() else None
                row["pct_over_3cm"], row["n_size_recorded"] = pct(sz > 3, sz.notna())
            if "n_nodules" in g:
                nd = pd.to_numeric(g["n_nodules"], errors="coerce")
                row["pct_multinodular"], row["n_nodules_recorded"] = pct(nd >= 2, nd.notna())
            if "vp" in g:
                v = pd.to_numeric(g["vp"], errors="coerce")
                row["pct_portal_vein_invasion"], row["n_vp_recorded"] = pct(v > 0, v.notna())
            for c_, nm in (("afp_ng_ml", "median_afp_ng_ml"), ("dcp_ng_ml", "median_dcp_ng_ml")):
                if c_ in g:
                    x = pd.to_numeric(g[c_], errors="coerce")
                    row[nm] = float(x.median()) if x.notna().any() else None
            rows.append(row)
        ex["tumour_at_diagnosis_by_tier"] = rows
        ex["tumour_note"] = ("Among patients who developed HCC: baseline tier against the tumour found at diagnosis. Percentages use only patients with a recorded value (the n columns). "
                             "Descriptive only; with few cases in a tier the figures are unstable. No tumour LOCATION is modelled, and none exists in the cohort. "
                             "A coarse 'early HCC' flag is not used because the source codes it Yes or blank, so 'not early' cannot be told from 'not recorded'.")
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
    if res.attrs.get("imaging"):
        out["imaging"] = res.attrs["imaging"]
        out["n"] = n
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
    elif disease == "breast":
        base.update(risk5=(0.004 + 0.12 * risk).round(4), V=r.beta(2, 3, n).round(3), E=r.uniform(.4, .9, n).round(2), rho=r.uniform(0, .5, n).round(2), sex="female")
    else:   # imaging: four SYNTHETIC feature columns and a pathology-like label generated from an arbitrary rule
        a, b, c, d = r.normal(size=(4, n))
        mal = (r.random(n) < 1 / (1 + np.exp(-(1.2 * a + 0.8 * b - 0.5)))).astype(int)
        base = {"patient_id": base["patient_id"], "roi_id": ["R%04d" % i for i in range(n)], "label": mal,
                "split": np.where(np.arange(n) < n // 2, "dev", "test"),
                "feat_texture": (3 + 1.2 * a + 1.0 * mal).round(3), "feat_intensity_var": (2000 + 700 * b + 600 * mal).round(1),
                "feat_adc": (1.4 + 0.3 * c - 0.3 * mal).round(3), "feat_sphericity": (0.65 + 0.1 * d - 0.05 * mal).round(3)}
    return _rec(pd.DataFrame(base))
