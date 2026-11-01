import io
from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st
from rmti_core import HCC, CONSEQ, TIERS, tier, log_scale, hcc_score, apply_rmti, harrell_c, summarise

st.set_page_config(page_title="RMTI Oncology Sandbox", page_icon="🧬", layout="wide")
DATA = Path(__file__).parent / "data"
NOTICE = ("**Research prototype.** Not a medical device, not clinically validated, not for patient-care decisions. "
          "Do not upload patient-identifiable data: this is a public web app.")
HCC_COLS = ["patient_id", "etiology", "age", "male", "albumin", "bilirubin", "platelets", "time_years", "event"]
SANDBOX = {  # suggested covariates only; no validated anchors are assumed for these cancers
    "Lung cancer": ["patient_id", "age", "sex", "smoking_pack_years", "histology", "stage", "ecog", "screening_ldct",
                    "L", "E", "V", "rho", "time_years", "event"],
    "Breast cancer": ["patient_id", "age", "subtype", "stage", "grade", "screening_mammography",
                      "L", "E", "V", "rho", "time_years", "event"]}


def read(f):
    return pd.read_csv(f) if f.name.lower().endswith(".csv") else pd.read_excel(f)


def csv_bytes(df):
    return df.to_csv(index=False).encode()


def params():
    p = dict(HCC)
    with st.sidebar.expander("RMTI parameters", expanded=False):
        p["tool"] = 1 if st.radio("L tool", ["aMAP-ref (clean)", "Full aMAP (overlaps ALBI: diagnostic)"]).startswith("aMAP-ref") else 2
        p["E"] = st.number_input("E (exposure)", 0.0, 1.0, p["E"], 0.05)
        p["rho_now"] = st.number_input("ρ now", 0.0, 1.0, p["rho_now"], 0.05)
        p["rho_after"] = st.number_input("ρ after", 0.0, 1.0, p["rho_after"], 0.05)
        p["C"] = st.selectbox("C index (consequence)", list(CONSEQ), index=4)
        p["r_lo"] = st.number_input("r_lo (L = 0)", 1e-5, 1.0, p["r_lo"], format="%.4f")
        p["r_hi"] = st.number_input("r_hi (L = 1)", 1e-4, 1.0, p["r_hi"], format="%.3f")
    if p["tool"] == 2:
        st.warning("DIAGNOSTIC: full aMAP contains ALBI, so albumin and bilirubin feed both L and V. Not an RMTI result.")
    return p


def results(o, c=None, rows=None):
    st.subheader("Tier distribution")
    st.dataframe(summarise(o), width="stretch")
    if {"time_years", "event"} <= set(o.columns):
        c = harrell_c(o.time_years, o.event, o.R)
        st.metric("Harrell C of R (simple; competing events censored)", f"{c:.3f}")
    st.download_button("Download scored cohort (CSV)", csv_bytes(o), "rmti_scored.csv")


# ---------------------------------------------------------------- pages
def overview():
    st.title("Risk Mechanism Theory Index · Oncology Sandbox")
    st.markdown("**R = L · E · V · (1 − ρ)**  (bounded 0–1)  ·  **EAL = L · C · (1 − ρ)**")
    st.caption("Fixed tiers: 1 Low <0.05 · 2 Moderate <0.15 · 3 High <0.35 · 4 Severe <0.60 · 5 Critical ≥0.60. "
               "The lower bound of a tier belongs to the higher tier.")
    st.info(NOTICE)
    st.markdown("""
- **HCC calculator**: single patient (age, sex, albumin, bilirubin, platelets), ported from the Excel workbook v2.4.1.
- **HCC cohort**: score a cohort, tier distribution, aetiology and risk-group tables. Upload your own file.
- **Lung / Breast sandbox**: ready for retrospective or real cohorts. Upload data, map columns to L, E, V, ρ, get scores.
- **Generic RMTI**: slider calculator for any field.
""")
    st.warning("No validated L/V instruments are assumed for lung or breast. You choose and document the mapping; "
               "anchors are assigned, not estimated, until your research establishes them.")


def hcc_calc():
    p = params()
    st.title("HCC single-patient calculator")
    c = st.columns(5)
    age = c[0].number_input("Age (years)", 18.0, 100.0, 62.0)
    male = c[1].selectbox("Sex", ["Male", "Female"]) == "Male"
    alb = c[2].number_input("Albumin (g/L)", 10.0, 60.0, 40.0)
    bil = c[3].number_input("Bilirubin (µmol/L)", 1.0, 500.0, 14.0)
    plt_ = c[4].number_input("Platelets (10⁹/L)", 10.0, 800.0, 150.0)
    o = hcc_score(pd.DataFrame(dict(age=[age], male=[int(male)], albumin=[alb], bilirubin=[bil], platelets=[plt_])), p).iloc[0]
    a, b, d = st.columns(3)
    a.metric("L (likelihood)", f"{o.L:.3f}", f"aMAP group {int(o.risk_group)}", delta_color="off")
    b.metric("V (vulnerability)", f"{o.V:.2f}", f"ALBI grade {int(o.ALBI_grade)}", delta_color="off")
    d.metric("E (exposure)", f"{p['E']:.2f}")
    a, b, d = st.columns(3)
    a.metric(f"R now (ρ={p['rho_now']})", f"{o.R:.3f}", o.Tier, delta_color="off")
    b.metric(f"R after (ρ={p['rho_after']})", f"{o.R_after:.3f}", o.Tier_after, delta_color="off")
    d.metric("EAL", f"{o.EAL:.3f}")
    with st.expander("Intermediate values"):
        st.write({k: round(float(o[k]), 4) for k in ["ALBI", "aMAP_full", "aMAP_ref", "annual_incidence"]})


def hcc_cohort():
    p = params()
    st.title("HCC cohort")
    st.caption("Columns: " + ", ".join(HCC_COLS) + "  (event: 1 = incident HCC, 2 = death without HCC, 0 = censored)")
    st.download_button("Download blank template", csv_bytes(pd.DataFrame(columns=HCC_COLS)), "hcc_template.csv")
    up = st.file_uploader("Upload cohort (CSV or Excel)", type=["csv", "xlsx"])
    df = read(up) if up else (pd.read_csv(DATA / "japan_cohort.csv") if (DATA / "japan_cohort.csv").exists() else None)
    if df is None:
        st.info("No cohort loaded. Upload a file in the template format.")
        ref = DATA / "python_results_reference.csv"
        if ref.exists():
            st.subheader("Published reference results (aggregate, from the Python run)")
            st.dataframe(pd.read_csv(ref, header=None), width="stretch", hide_index=True)
        return
    need = ["age", "male", "albumin", "bilirubin", "platelets"]
    if missing := [c for c in need if c not in df]:
        return st.error(f"Missing columns: {missing}")
    df = df.dropna(subset=need)
    o = hcc_score(df, p)
    st.success(f"{len(o):,} patients scored" + (" (bundled Japanese Ogaki cohort)" if not up else ""))
    results(o)
    if "etiology" in o:
        st.subheader("By aetiology")
        g = o.groupby("etiology").agg(n=("R", "size"), mean_L=("L", "mean"), mean_V=("V", "mean"), mean_R=("R", "mean"))
        if "event" in o:
            g["HCC"] = o.groupby("etiology").event.apply(lambda s: int((s == 1).sum()))
            g["person_years"] = o.groupby("etiology").time_years.sum()
            g["crude per 100 PY"] = 100 * g.HCC / g.person_years
        st.dataframe(g.round(3), width="stretch")
    if "event" in o:
        st.subheader("Published aMAP incidence vs observed")
        g = o.groupby("risk_group").agg(n=("R", "size"), HCC=("event", lambda s: int((s == 1).sum())), PY=("time_years", "sum"))
        g["observed per 100 PY"] = 100 * g.HCC / g.PY
        g["published range per 100 PY"] = [f"{100*a:g} to {100*b:g}" for a, b in p["inc_range"]]
        st.dataframe(g.round(3), width="stretch")


def sandbox(name):
    st.title(f"{name} sandbox")
    st.info("Ready for retrospective or prospective cohorts. Nothing is stored: data lives only in your session.")
    cols = SANDBOX[name]
    st.download_button("Download blank template", csv_bytes(pd.DataFrame(columns=cols)), f"{name.split()[0].lower()}_template.csv")
    up = st.file_uploader("Upload cohort (CSV or Excel)", type=["csv", "xlsx"], key=name)
    df = read(up) if up else None
    if df is None and st.toggle("Use synthetic demo rows (random numbers, for testing the pipeline only)", key="demo" + name):
        r = np.random.default_rng(1); n = 200
        df = pd.DataFrame(dict(patient_id=range(n), L=r.beta(2, 4, n), E=r.uniform(.4, .9, n), V=r.beta(2, 3, n),
                               rho=r.uniform(0, .5, n), time_years=r.exponential(5, n), event=r.integers(0, 2, n)))
        st.warning("SYNTHETIC DATA. Results mean nothing.")
    if df is None:
        return st.caption("Awaiting data.")
    st.dataframe(df.head(), width="stretch")
    st.subheader("Map columns to the model")
    opts = ["(constant)"] + list(df.columns)
    maps = {}
    for t, dflt in (("L", .5), ("E", .6), ("V", .5)):
        c = st.columns([2, 2, 2, 2])
        col = c[0].selectbox(f"{t} column", opts, index=opts.index(t) if t in opts else 0, key=f"{name}{t}c")
        if col == "(constant)":
            maps[t] = pd.Series(c[1].number_input(f"{t} value", 0.0, 1.0, dflt, key=f"{name}{t}v"), index=df.index); continue
        how = c[1].selectbox("scale", ["already 0–1", "log scale between anchors", "min–max"], key=f"{name}{t}h")
        x = pd.to_numeric(df[col], errors="coerce")
        if how.startswith("log"):
            lo, hi = c[2].number_input("value → 0", 1e-6, 1e6, 0.0005, format="%.5f", key=f"{name}{t}lo"), c[3].number_input("value → 1", 1e-6, 1e6, 0.15, format="%.4f", key=f"{name}{t}hi")
            x = pd.Series(log_scale(x, lo, hi), index=df.index)
        elif how == "min–max":
            x = (x - x.min()) / (x.max() - x.min())
        maps[t] = x
    c = st.columns(3)
    rn = c[0].number_input("ρ now", 0.0, 1.0, 0.2, 0.05, key=name + "rn")
    ra = c[1].number_input("ρ after", 0.0, 1.0, 0.5, 0.05, key=name + "ra")
    cc = c[2].selectbox("C index", list(CONSEQ), index=4, key=name + "C")
    o = df.assign(L=maps["L"], E=maps["E"], V=maps["V"])
    o = apply_rmti(o, o.E, rn, ra, cc).dropna(subset=["L", "E", "V"])
    if "event" in o and "time_years" in o:
        o["event"] = pd.to_numeric(o.event, errors="coerce")
    results(o)


def generic():
    st.title("Generic RMTI calculator")
    c = st.columns(5)
    L, E, V = c[0].slider("L", 0., 1., .8), c[1].slider("E", 0., 1., .85), c[2].slider("V", 0., 1., .75)
    rn, ra = c[3].slider("ρ now", 0., 1., .2), c[4].slider("ρ after", 0., 1., .58)
    C = st.selectbox("C index", list(CONSEQ), index=4)
    o = apply_rmti(pd.DataFrame(dict(L=[L], V=[V])), E, rn, ra, C).iloc[0]
    a, b, d = st.columns(3)
    a.metric("R now", f"{o.R:.3f}", o.Tier, delta_color="off")
    b.metric("R after", f"{o.R_after:.3f}", o.Tier_after, delta_color="off")
    d.metric("EAL", f"{o.EAL:.3f}")


PAGES = {"Overview": overview, "HCC calculator": hcc_calc, "HCC cohort": hcc_cohort,
         "Lung cancer sandbox": lambda: sandbox("Lung cancer"), "Breast cancer sandbox": lambda: sandbox("Breast cancer"),
         "Generic RMTI": generic}
page = st.sidebar.radio("Navigate", list(PAGES))
PAGES[page]()
st.sidebar.link_button("Oncology sandbox (site)", "https://drmarolla.github.io/rmti-oncology-sandbox/")
st.sidebar.link_button("Disaster-science sandbox (site)", "https://drmarolla.github.io/rmti-disaster-science-sandbox/")
st.sidebar.caption("© Dr. Cesar Marolla · RMTI research prototype")
