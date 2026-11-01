"""RMTI core: R = L·E·V·(1-rho). HCC instruments ported 1:1 from the Excel calculator v2.4.1."""
import numpy as np
import pandas as pd

# Defaults = Parameters sheet of the Excel workbook (assigned anchors, not estimated).
HCC = dict(
    albi_c1=-2.6, albi_c2=-1.39, albi_b=0.66, albi_a=-0.085, V=(0.35, 0.60, 0.85),
    amap_age=0.06, amap_male=0.89, amap_albi=0.48, amap_plt=-0.01, amap_const=7.4, amap_div=14.77,
    g_lo=50, g_hi=60, inc=(0.001, 0.007, 0.028), inc_range=((0, .002), (.004, .01), (.016, .04)),
    r_lo=0.0005, r_hi=0.15, E=0.60, rho_now=0.20, rho_after=0.65, C=5, tool=1)
CONSEQ = {1: 0.1, 2: 0.3, 3: 0.5, 4: 0.75, 5: 1.0}
BOUNDS = np.array([0, 0.05, 0.15, 0.35, 0.60])
TIERS = np.array(["1 Low", "2 Moderate", "3 High", "4 Severe", "5 Critical"])


def tier(r):
    """Lower bound belongs to the higher tier; uses unrounded R."""
    return TIERS[np.searchsorted(BOUNDS, np.asarray(r, float), side="right") - 1]


def log_scale(x, lo, hi):
    with np.errstate(divide="ignore", invalid="ignore"):
        v = (np.log10(np.asarray(x, float)) - np.log10(lo)) / (np.log10(hi) - np.log10(lo))
    return np.clip(np.nan_to_num(v, nan=0.0, neginf=0.0), 0, 1)


def hcc_score(df, p=HCC):
    """df needs: age, male (1/0), albumin g/L, bilirubin umol/L, platelets 10^9/L."""
    o = df.copy()
    o["ALBI"] = np.log10(o.bilirubin) * p["albi_b"] + o.albumin * p["albi_a"]
    o["ALBI_grade"] = np.where(o.ALBI <= p["albi_c1"], 1, np.where(o.ALBI <= p["albi_c2"], 2, 3))
    o["V"] = np.array(p["V"])[o.ALBI_grade - 1]

    def amap(albi):
        return ((p["amap_age"] * o.age + p["amap_male"] * o.male + p["amap_albi"] * albi
                 + p["amap_plt"] * o.platelets) + p["amap_const"]) / p["amap_div"] * 100
    o["aMAP_full"], o["aMAP_ref"] = amap(o.ALBI), amap(p["albi_c1"])  # ref = ALBI fixed at grade-1/2 boundary
    s = o.aMAP_ref if p["tool"] == 1 else o.aMAP_full
    o["risk_group"] = np.where(s < p["g_lo"], 1, np.where(s <= p["g_hi"], 2, 3))
    o["annual_incidence"] = np.array(p["inc"])[o.risk_group - 1]
    o["L"] = log_scale(o.annual_incidence, p["r_lo"], p["r_hi"])
    return apply_rmti(o, p["E"], p["rho_now"], p["rho_after"], p["C"])


def apply_rmti(o, E, rho_now, rho_after, C=5, L="L", V="V"):
    """Generic core. E / rho may be scalars or per-patient columns."""
    o = o.copy()
    ir = o[L] * E * o[V]
    o["R"], o["Tier"] = ir * (1 - rho_now), tier(ir * (1 - rho_now))
    o["R_after"], o["Tier_after"] = ir * (1 - rho_after), tier(ir * (1 - rho_after))
    o["EAL"] = o[L] * CONSEQ[int(C)] * (1 - rho_now)
    return o


def harrell_c(time, event, score):
    """Simple Harrell C; event==1 is the event, everything else censored (no competing-risk handling)."""
    t, e, s = (np.asarray(a, float) for a in (time, event == 1, score))
    num = den = 0.0
    for i in np.where(e)[0]:
        m = t > t[i]
        den += m.sum()
        num += (s[i] > s[m]).sum() + 0.5 * (s[i] == s[m]).sum()
    return num / den if den else np.nan


def summarise(o, time="time_years", event="event"):
    """Tier table + (if outcome columns exist) events, person-years, crude rate per tier."""
    rows = []
    for tcol, lab in (("Tier", "now"), ("Tier_after", "after")):
        c = o[tcol].value_counts().reindex(TIERS, fill_value=0)
        rows.append(pd.DataFrame({f"patients (rho {lab})": c, f"% (rho {lab})": (100 * c / len(o)).round(1)}))
    out = pd.concat(rows, axis=1)
    if time in o and event in o:
        g = o.groupby("Tier").agg(events=(event, lambda s: int((s == 1).sum())), person_years=(time, "sum"))
        g["crude per 100 PY"] = (100 * g.events / g.person_years).round(3)
        out = out.join(g.reindex(TIERS))
    return out
