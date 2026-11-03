"""Framework-free service layer. Both the FastAPI app and the Streamlit app call
these functions, so the math lives in one place (the unmodified RMTI v2.3.0 engine)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "rmti_engine"))

import numpy as np
import pandas as pd
from core.rmti_core import assess, rank_cohort, score, TIER
from oncology.rmti_hcc import (assess_patient, rank_cohort_hcc, HCC_TIER_POSTURE,
                               N_MIN_HCC, N_MAX_HCC, ALBI_V, C_LADDER, RHO_ANCHORS)
from dynamic.rmti_dynamic import (TrajectoryParams, HCC_PARAMS, DISASTER_PARAMS,
                                  run_trajectory, tier_changes)

from oncology import rmti_lung as LUNG
from oncology import rmti_hcc_cohort as HCC_COHORT
from oncology import lung_evidence as LUNG_EVIDENCE
import rmti_breast as BREAST                                 # female breast cancer: proposed scaffold, see rmti_breast.py
import fhir_export
from oncoclastics.rmti_oncoclastics import (score_two_senses, care_disruption, run_two_sense_trajectory,
                                            oncoclastic_events, combine_rho, RHO_BIO_ANCHORS, RHO_BIO_DESCRIPTORS, RHO_BIO_CEILING)

ENGINE_VERSION = "2.4.0"
DISCLAIMER = ("Research prototype. Not validated, not a medical device, not for patient-care or "
              "emergency decisions. Parameters are uncalibrated placeholders. Do not enter identifying data.")
TIERS = [lbl for _, lbl in TIER]


def resolve_domain(domain, site=None):
    """RMTI v2.3.0 vocabulary -> internal key. 'oncoclastics' + site ('hcc' default, or 'lung'); 'disaster_science' -> disaster."""
    d = (domain or "").lower()
    if d == "oncoclastics":
        return (site or "hcc").lower()
    return {"disaster_science": "disaster"}.get(d, d)


def _params(domain, overrides=None):
    domain = resolve_domain(domain)
    base = {"hcc": HCC_PARAMS, "lung": LUNG.LUNG_PARAMS, "breast": BREAST.BREAST_PARAMS}.get(domain, DISASTER_PARAMS)
    d = {**base.__dict__, **(overrides or {})}
    return TrajectoryParams(**d)


def snapshot(domain, N, L, E, V, rho_now, rho_after=None, C=5):
    domain = resolve_domain(domain)
    if domain == "hcc":
        return assess_patient(N, L, E, V, rho_now, rho_after, C)
    if domain == "lung":
        return LUNG.assess_patient(N, L, E, V, rho_now, rho_after, C)
    if domain == "breast":
        return BREAST.assess_patient(N, L, E, V, rho_now, rho_after, C)
    return assess(N, L, E, V, rho_now, rho_after, C)


def trajectory(domain, L, E, C, rho0, observations, delivery, params=None):
    domain = resolve_domain(domain)
    p = _params(domain, params)
    post = {"hcc": HCC_TIER_POSTURE, "lung": LUNG.LUNG_TIER_POSTURE, "breast": BREAST.BREAST_TIER_POSTURE}.get(domain)
    on = run_trajectory(L, E, C, rho0, observations, delivery, p, post)
    off = run_trajectory(L, E, C, rho0, observations, delivery,
                         TrajectoryParams(**{**p.__dict__, "filter_on": False}), post)
    return {"filtered": on, "memoryless": off, "tier_changes": tier_changes(on),
            "params": p.__dict__}


def cohort(domain, rows):
    """rows: list of {name, N, L, E, V, rho_now, [rho_after], [C]}"""
    domain = resolve_domain(domain)
    d = {}
    for r in rows:
        r = dict(r); name = r.pop("name")
        r.setdefault("C", 5)
        if domain == "lung" and "risk5" in r:                 # 5-year risk (fraction) -> scaled L
            r["L"] = LUNG.l_from_risk(r.pop("risk5"))
        if domain == "breast" and "risk5" in r:                # 5-year risk (fraction) -> scaled L, breast placeholder anchors
            r["L"] = BREAST.l_from_risk(r.pop("risk5"))
        if domain == "disaster":
            r["E_sel"] = r.pop("E")
        d[name] = r
    if domain == "hcc":
        return rank_cohort_hcc(d)
    if domain == "breast":
        return BREAST.rank_cohort_breast(d)
    return LUNG.rank_cohort_lung(d) if domain == "lung" else rank_cohort(d)


def lung_inputs(risk5, horizon_years=5, ecog=None, ladder=None, l_tool="Other or custom tool (tick the variables)", v_items=()):
    """Raw lung inputs -> L, V, rho_bio using rmti_lung helpers only (no new maths). Refuses 2-year risk and V items the L tool already contains."""
    tool_vars = LUNG_EVIDENCE.L_TOOL_VARIABLES
    if l_tool not in tool_vars:
        raise ValueError("unknown L tool %r; use one of %s" % (l_tool, sorted(tool_vars)))
    L = LUNG.l_from_risk(risk5, horizon_years)
    y = LUNG.v_indicator(list(v_items), tool_vars[l_tool])
    valid = {i["label"] for i in LUNG_EVIDENCE.V_ITEMS}
    unknown = [x for x in v_items if x not in valid]
    if unknown:
        raise ValueError("unknown V item(s): " + "; ".join(unknown))
    out = {"L": L, "V": LUNG.v_from_indicator(y), "v_count": y, "L_anchors": dict(LUNG.L_ANCHORS),
           "ladder": ladder or LUNG.ACTIVE_LADDER}
    if ecog is not None:
        out["rho_bio"] = LUNG.rho_bio_from_ecog(ecog, ladder)
    return out


def hcc_patient(age_years, male, albumin_g_l, bilirubin_umol_l, platelets_1e9_l, l_tool="aMAP-ref", E=0.60, rho=0.20, rho_after=0.65, C=5, allow_overlap=False):
    """One patient through the patient-level RMTI-HCC (rmti_hcc_cohort). Default L tool aMAP-ref keeps L (age, sex, platelets) and V (albumin,
    bilirubin) on disjoint variables. l_tool='aMAP' overlaps ALBI and is refused unless allow_overlap=True; the reply is then labelled DIAGNOSTIC."""
    df = pd.DataFrame([dict(age_years=age_years, male=int(male), albumin_g_l=albumin_g_l, bilirubin_umol_l=bilirubin_umol_l, platelets_1e9_l=platelets_1e9_l)])
    o = HCC_COHORT.score_cohort(df, l_tool=l_tool, E=E, rho=rho, rho_after=rho_after, C=C, allow_overlap=allow_overlap).iloc[0]
    return {"status": o["status"], "albi": float(o["albi"]), "albi_grade": int(o["albi_grade"]), "amap": float(o["amap"]), "amap_ref": float(o["amap_ref"]),
            "risk_group": int(o["amap_group"]), "annual_incidence": float(o["annual_incidence"]), "L": float(o["L"]), "V": float(o["V"]), "E": E, "rho": rho,
            "R": float(o["R"]), "R_raw": float(o["R_raw"]), "tier": o["tier"], "rho_after": rho_after, "R_after": float(o["R_after"]), "tier_after": o["tier_after"],
            "EAL": float(o["EAL"]), "overlap": bool(o["overlap_flag"]), "disclaimer": DISCLAIMER}


# ---------------- retrospective validation on serial data -----------------
SERIAL_COLS = ["patient_id", "cycle", "y"]
def validate_serial(df, domain="hcc", params=None):
    domain = resolve_domain(domain)
    """Long-format serial data -> per-patient final-cycle R, then discrimination and
    tier-wise observed event rates against a supplied outcome.

    Required columns: patient_id, cycle, y (indicator; blank = missed visit)
    Optional per-row: delivery (0-1), L, E, C, rho0 (taken from each patient's first row)
    Outcome (per patient, any row): event (0/1) and time (follow-up, same unit for all)
    """
    privacy_check(df)
    miss = [c for c in SERIAL_COLS if c not in df.columns]
    if miss:
        raise ValueError(f"Missing columns: {miss}")
    p = _params(domain, params)
    rows = []
    for pid, g in df.sort_values(["patient_id", "cycle"]).groupby("patient_id"):
        first = g.iloc[0]
        g_ = lambda k, dflt: float(first[k]) if k in g.columns and pd.notna(first[k]) else dflt
        obs = [None if pd.isna(v) else float(v) for v in g["y"]]
        dlv = ([None if pd.isna(v) else float(v) for v in g["delivery"]]
               if "delivery" in g.columns else [None] * len(g))
        if obs[0] is None:
            raise ValueError(f"Patient {pid}: baseline y is missing")
        tr = run_trajectory(g_("L", 0.3), g_("E", 0.6), int(g_("C", 5)), g_("rho0", 0.2),
                            obs, dlv, p, {"hcc": HCC_TIER_POSTURE, "lung": LUNG.LUNG_TIER_POSTURE, "breast": BREAST.BREAST_TIER_POSTURE}.get(domain))
        last, base = tr[-1], tr[0]
        rec = {"patient_id": pid, "R_baseline": base["R"], "R_final": last["R"],
               "tier_final": last["tier"], "dR": last["R"] - base["R"], "cycles": len(tr)}
        if "stratum" in g.columns and g["stratum"].notna().any():
            rec["stratum"] = str(g["stratum"].dropna().iloc[0])
        if "event" in g.columns:
            rec["event"] = int(g["event"].dropna().iloc[0]) if g["event"].notna().any() else np.nan
            rec["time"] = float(g["time"].dropna().iloc[0]) if "time" in g.columns and g["time"].notna().any() else np.nan
        rows.append(rec)
    res = pd.DataFrame(rows)
    out = {"patients": res}
    if "event" in res.columns and res["event"].notna().all() and res["time"].notna().all():
        ev, tm = res["event"].astype(int).values, res["time"].values
        out["n"], out["events"] = len(res), int(ev.sum())
        out["c_index_final"] = c_index(tm, ev, res["R_final"].values)
        out["c_index_baseline"] = c_index(tm, ev, res["R_baseline"].values)
        out["auc_final"] = auc(ev, res["R_final"].values)
        out["auc_baseline"] = auc(ev, res["R_baseline"].values)
        out["by_tier"] = tier_table(res)
        out["km"] = {t: km(g["time"].values, g["event"].astype(int).values)
                     for t, g in res.groupby("tier_final")}
        if "stratum" in res.columns:
            out["by_stratum"] = stratified(res)
        out["note"] = ("Compare final-cycle (trajectory) vs baseline (level) discrimination. "
                       "With few events these estimates are very unstable; report CIs before drawing conclusions.")
    return out


def c_index(time, event, risk):
    """Harrell's C: among comparable pairs (earlier time had an event), share where the
    earlier-failing patient has the higher risk; risk ties count 0.5."""
    t, e, r = (np.asarray(x, float) for x in (time, event, risk))
    comp = (e[:, None] == 1) & (t[None, :] > t[:, None])
    den = comp.sum()
    if den == 0:
        return float("nan")
    num = ((r[:, None] > r[None, :]) & comp).sum() + 0.5 * ((r[:, None] == r[None, :]) & comp).sum()
    return float(num / den)


def auc(event, risk):
    e, r = np.asarray(event), np.asarray(risk)
    pos, neg = r[e == 1], r[e == 0]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    gt = (pos[:, None] > neg[None, :]).sum() + 0.5 * (pos[:, None] == neg[None, :]).sum()
    return float(gt / (len(pos) * len(neg)))


def tier_table(res):
    g = res.groupby("tier_final").agg(n=("event", "size"), events=("event", "sum"),
                                      mean_R=("R_final", "mean")).reset_index()
    g["observed_event_rate"] = g["events"] / g["n"]
    g["tier_order"] = g["tier_final"].map({t: i for i, t in enumerate(TIERS)})
    return g.sort_values("tier_order").drop(columns="tier_order")


def km(time, event):
    """Kaplan-Meier estimate -> list of (t, S(t))."""
    time, event = np.asarray(time, float), np.asarray(event, int)
    s, out = 1.0, [(0.0, 1.0)]
    for t in np.unique(time[event == 1]):
        at_risk = (time >= t).sum()
        d = ((time == t) & (event == 1)).sum()
        s *= 1 - d / at_risk
        out.append((float(t), float(s)))
    return out


def example_serial(n=60, seed=7, y_max=6.0):
    """SYNTHETIC serial data for demonstration only (outcome generated from a made-up rule)."""
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n):
        base, drift = rng.uniform(0, 4), rng.normal(0.1, 0.5)
        L, E, rho0 = rng.uniform(0.1, 0.6), rng.uniform(0.4, 0.8), rng.uniform(0.15, 0.5)
        risk = 0.02 + 0.05 * (base + 4 * max(drift, 0)) / 6 + 0.1 * L
        stratum = str(rng.choice(["never smoker", "former smoker", "current smoker"]))
        event = int(rng.random() < min(risk * 3, 0.9))
        time = float(rng.uniform(6, 36) if event else 36)
        for t in range(6):
            y = float(np.clip((base + drift * t + rng.normal(0, 0.5)) * y_max / 6.0, 0, y_max))
            rows.append(dict(patient_id=f"S{i:03d}", cycle=t, y=None if (t > 0 and rng.random() < .08) else round(y, 2),
                             delivery=round(float(np.clip(rho0 + rng.normal(0, .08), 0, 1)), 2),
                             L=round(L, 2), E=round(E, 2), C=3, rho0=round(rho0, 2), stratum=stratum,
                             event=event, time=round(time, 1)))
    return pd.DataFrame(rows)


# ---------------- privacy guard, uncertainty, calibration -----------------
import re
_ID_COLS = re.compile(r"(^|_)(name|first|last|surname|mrn|dob|birth|ssn|email|phone|tel|address|street|zip|postcode|"
                      r"postal|nhs|passport|insurance|national_?id)($|_)", re.I)
_ID_VALUES = [re.compile(p) for p in (r"[\w.+-]+@[\w-]+\.[\w.]+", r"\b\d{3}-\d{2}-\d{4}\b",
                                      r"\b\d{3}[-. ]\d{3}[-. ]\d{4}\b")]


def privacy_check(df):
    """Refuse uploads that look like they contain direct identifiers. Heuristic: it reduces
    accidents, it does not make real patient data safe (see README)."""
    bad = [c for c in df.columns if _ID_COLS.search(str(c))]
    for c in df.select_dtypes(include=["object", "string"]).columns:
        sample = df[c].dropna().astype(str).head(500)
        if any(p.search(v) for p in _ID_VALUES for v in sample):
            bad.append(f"{c} (values look like emails, phone or ID numbers)")
    if bad:
        raise ValueError("Upload refused: possible direct identifiers in " + ", ".join(map(str, bad)) +
                         ". Remove them and use pseudonymous patient_id values.")
    return df


def bootstrap_ci(res, B=500, seed=1, level=0.95):
    """Percentile bootstrap over patients for C-index (final, baseline) and the difference
    final - baseline. Needs event/time columns in `res` (output of validate_serial()['patients'])."""
    rng = np.random.default_rng(seed)
    t, e = res["time"].values, res["event"].astype(int).values
    rf, rb = res["R_final"].values, res["R_baseline"].values
    n, draws = len(res), []
    for _ in range(B):
        i = rng.integers(0, n, n)
        cf, cb = c_index(t[i], e[i], rf[i]), c_index(t[i], e[i], rb[i])
        if not (np.isnan(cf) or np.isnan(cb)):
            draws.append((cf, cb, cf - cb))
    d = np.array(draws)
    if len(d) < B * 0.5:
        return {"note": "Too few events for a stable bootstrap."}
    lo, hi = (1 - level) / 2 * 100, (1 + level) / 2 * 100
    ci = lambda k: [float(np.percentile(d[:, k], lo)), float(np.percentile(d[:, k], hi))]
    return {"B": len(d), "level": level, "c_final": ci(0), "c_baseline": ci(1), "delta_c": ci(2),
            "delta_c_excludes_zero": bool(ci(2)[0] > 0 or ci(2)[1] < 0)}


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (float(c - h), float(c + h))


def calibration(res):
    """Observed event proportion per tier with Wilson 95% intervals, plus a logistic
    calibration slope of event on log(R). R is a relative score, NOT a probability, so the
    slope describes monotone association strength only; it is not a calibration of absolute risk."""
    tt = tier_table(res)
    lo_hi = [wilson(int(k), int(n)) for k, n in zip(tt["events"], tt["n"])]
    tt["ci_low"], tt["ci_high"] = zip(*lo_hi) if lo_hi else ([], [])
    x = np.log(np.clip(res["R_final"].values, 1e-9, None)); y = res["event"].astype(int).values
    slope = intercept = float("nan")
    if 0 < y.sum() < len(y):
        X = np.column_stack([np.ones_like(x), (x - x.mean())]); b = np.zeros(2)
        for _ in range(50):                      # Newton-Raphson logistic regression
            p = 1 / (1 + np.exp(-X @ b)); W = p * (1 - p) + 1e-9
            step = np.linalg.solve(X.T @ (X * W[:, None]) + 1e-8 * np.eye(2), X.T @ (y - p))
            b += step
            if np.abs(step).max() < 1e-8:
                break
        intercept, slope = float(b[0]), float(b[1])
    return {"by_tier": tt, "slope_log_R": slope, "intercept": intercept}


def stratified(res, min_events=10):
    """Discrimination within subgroups (e.g. smoking status, histology, sex). Cancers are heterogeneous, so a pooled
    C-index can hide a subgroup where the score fails. C-index is withheld where a stratum has fewer than min_events events."""
    rows = []
    for k, g in res.groupby("stratum"):
        ev = int(g["event"].sum())
        ok = ev >= min_events and g["event"].nunique() > 1
        rows.append({"stratum": k, "n": len(g), "events": ev,
                     "c_index_final": c_index(g["time"], g["event"], g["R_final"]) if ok else None,
                     "c_index_baseline": c_index(g["time"], g["event"], g["R_baseline"]) if ok else None,
                     "note": "" if ok else f"withheld: fewer than {min_events} events"})
    return pd.DataFrame(rows)


# ---------------- Oncoclastics: the two senses of resilience (v2.3.0 module, unchanged) -----------------
def two_sense_snapshot(L, E, V, rho_bio, rho_care, C=3, rho_care_after=None):
    """Biological sense (L, E, V, rho_bio) and care-system sense (rho_care) through the unchanged v2.3.0 module.
    rho_bio = 0 means 'not scored' and reproduces the standard score."""
    out = score_two_senses(L, E, V, rho_bio, rho_care, C)
    if rho_care_after is not None:
        out["care_disruption"] = care_disruption(L, E, V, rho_bio, rho_care, rho_care_after, C)
    return out


def two_sense_trajectory(domain, L, E, C, rho_bio, rho0_care, observations, delivery, params=None, v_step=0.0):
    domain = resolve_domain(domain)
    rows = run_two_sense_trajectory(L, E, C, rho_bio, rho0_care, observations, delivery, _params(domain, params))
    return {"rows": rows, "events": oncoclastic_events(rows, v_step)}


def events_for(rows, v_step=0.0):
    return oncoclastic_events(rows, v_step)


# ---------------- lung: risk-versus-treatment method demo (SYNTHETIC anchors, platform-only) -----------------
RTP_DEMO_ANCHORS = {   # invented to show the arithmetic; not from any study; the engine module ships no anchors
    "p_resection":  [(0.01, 0.60), (0.03, 0.50), (0.05, 0.40)],
    "s5_resection": [(0.01, 0.65), (0.03, 0.55), (0.05, 0.45)],
}


def rtp_curve(anchors, n=41):
    lo, hi = min(x for x, _ in anchors["p_resection"]), max(x for x, _ in anchors["p_resection"])
    return [LUNG.rtp_point(lo + (hi - lo) * i / (n - 1), anchors) for i in range(n)]


# ---------------- FHIR export (research use) -----------------
def fhir_risk_assessment(label, domain, inputs, site=None):
    """Score a snapshot and return a FHIR R4 RiskAssessment (status preliminary). inputs: N, L, E, V, rho_now, [rho_after], [C], [rho_bio]."""
    key = resolve_domain(domain, site)
    if key == "disaster":
        raise ValueError("FHIR export is offered for the Oncoclastics domain only")
    base = snapshot(key, inputs["N"], inputs["L"], inputs["E"], inputs["V"], inputs["rho_now"], inputs.get("rho_after"), inputs.get("C", 5))
    rb = float(inputs.get("rho_bio") or 0.0)
    if rb > 0:
        ts = two_sense_snapshot(inputs["L"], inputs["E"], inputs["V"], rb, inputs["rho_now"], inputs.get("C", 5))
        base = dict(base, R_now=ts["R_raw"], tier_now=ts["tier"])
    use = {k: v for k, v in dict(L=inputs["L"], E=inputs["E"], V=inputs["V"], rho_care=inputs["rho_now"], rho_bio=rb, C=inputs.get("C", 5)).items()}
    return fhir_export.risk_assessment(label, base, use, domain="oncoclastics", site=key, version=ENGINE_VERSION)
