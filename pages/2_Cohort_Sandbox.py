"""Cohort sandboxes for HCC, lung and breast: ready for retrospective or real cohorts. Uploads are processed for this session and not saved by the app."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Cohort sandbox · Oncoclastics", layout="wide")
import sandbox as B
import service as S
import style
from ui_common import gate, call

style.inject()
gate()
style.hero("Cohort sandbox", "Score a retrospective or real cohort, see the tier distribution and how the tiers relate to outcomes",
           [f"Engine v{S.ENGINE_VERSION}", "HCC · Lung · Breast", "Research prototype", "Not a medical device"])
style.strip()
st.caption("Real cohorts need ethics approval and a data-use agreement. Do not upload names or other identifiers: an identifier guard blocks obvious ones, but it prevents accidents only. "
           "Uploads are processed on the server for this session and are not saved by this app.")

T, DS = B.templates(), B.datasets()
st.markdown("### 1. Choose data")
disease = st.radio("Disease", list(T), format_func=lambda k: B.DISEASES[k]["label"], horizontal=True)
meta, dflt = T[disease], T[disease]["defaults"]
(st.warning if disease in ("breast", "imaging") else st.info)(meta["status"])
k = lambda s: f"{disease}_{s}"
bundled = {f"{d['label']} (bundled)": i for i, d in DS.items() if d["disease"] == disease}
src = st.radio("Source", list(bundled) + ["Upload a file", "Synthetic demo (pipeline test only)"], horizontal=True, key=k("src"))

with st.expander("Data format and blank template"):
    st.write("**Columns:** " + ", ".join(meta["columns"]) + "  ·  **required:** " + ", ".join(meta["required"]))
    st.caption("rho means ρ (resilience): file headers are written in ASCII, and a Greek ρ (for example ρ_care) is accepted too. Save Excel files as CSV UTF-8 so the symbol survives.")
    st.caption(meta["notes"] + " Outcome columns are optional: time_years (> 0) and cause (1 event, 2 competing event, 0 censored; a 0/1 column named event also works). stratum is an optional subgroup label.")
    st.download_button("Download blank template (CSV)", ",".join(meta["columns"]) + "\n", f"{disease}_template.csv", key=k("tpl"))

payload = {}
if src in bundled:
    payload["dataset"] = bundled[src]
    style.note(DS[bundled[src]]["description"] or "Bundled cohort.")
    style.note("Aggregate results only: patient-level rows of a bundled cohort are not shown or downloadable unless the server allows it.")
elif src.startswith("Synthetic"):
    payload["records"] = B.demo_records(disease)
    st.warning("SYNTHETIC random data to test the pipeline. Results mean nothing.")
else:
    up = st.file_uploader("Cohort file (CSV or Excel)", type=["csv", "xlsx"], key=k("up"))
    if up is None:
        st.info("Waiting for your cohort. Download the blank template above, fill it in and upload it here.")
        st.stop()
    try:
        raw = pd.read_csv(up) if up.name.lower().endswith(".csv") else pd.read_excel(up)
        payload["records"] = json.loads(raw.to_json(orient="records"))
    except Exception as e:
        st.error(f"Could not read the file: {e}"); st.stop()

st.markdown("### 2. Settings")
c = st.columns(4)
if disease == "imaging":
    o = dict(E=dflt["E"], rho=dflt["rho"], rho_after=dflt["rho"], C=c[0].select_slider("C: consequence index", [1, 2, 3, 4, 5], dflt["C"], key=k("C")))
    style.note("For imaging, E and ρ come from the mapped feature columns below, not from sliders.")
else:
    o = dict(E=c[0].slider("E: exposure", 0.0, 1.0, dflt["E"], 0.05, key=k("E"), help="Used for every patient unless the file has an E column."),
             rho=c[1].slider("ρ now" + (" (ρ_care)" if disease == "lung" else ""), 0.0, 0.99, dflt["rho"], 0.01, key=k("rho")),
             rho_after=c[2].slider("ρ after", 0.0, 0.99, dflt["rho_after"], 0.01, key=k("ra")),
             C=c[3].select_slider("C: consequence index", [1, 2, 3, 4, 5], dflt["C"], key=k("C")))
with st.expander("More settings"):
    c = st.columns(3)
    o["horizons"] = [float(x) for x in c[0].text_input("Cumulative-incidence horizons (years)", "5, 10", key=k("hz")).replace(",", " ").split() if x]
    o["bootstrap"] = c[1].number_input("Bootstrap resamples for the C-index 95% interval (0 = off)", 0, 1000, 0, 50, key=k("bs"))
    if disease == "hcc":
        o["l_tool"] = c[2].radio("L tool", ["aMAP-ref", "aMAP"], key=k("tool"), help="aMAP overlaps ALBI (double counting): refused unless you tick the box below.")
        o["anchors"] = st.selectbox("L anchors (assigned, not estimated)", list(B.ANCHORS), key=k("anc"),
                                    format_func=lambda a: f"{a}: {B.ANCHORS[a][0] * 100:g}%/yr → 0, {B.ANCHORS[a][1] * 100:g}%/yr → 1")
        o["allow_overlap"] = o["l_tool"] == "aMAP" and st.checkbox("Allow the overlap; output is labelled DIAGNOSTIC and is not the RMTI result", key=k("ov"))
        o["albi_ref"] = float(dflt["albi_ref"])
    if disease == "lung":
        o["use_rho_bio"] = st.checkbox("Use ECOG (if present) for ρ_bio on the provisional ladder", True, key=k("rb"))
    if disease == "breast":
        o["declared_l_variables"] = [x.strip() for x in st.text_input("Variables behind L (comma-separated, optional)", key=k("lv")).split(",") if x.strip()]
        o["declared_v_variables"] = [x.strip() for x in st.text_input("Variables behind V (comma-separated, optional)", key=k("vv")).split(",") if x.strip()]
        st.caption("A variable named in both lists is refused: no measured variable may feed two terms.")
if disease == "breast":
    st.markdown("**L anchors for the 5-year risk (PLACEHOLDERS: invented so the arithmetic runs; pre-register your own)**")
    cc = st.columns(3)
    o["r_lo"] = cc[0].number_input("5-year risk that maps to L = 0", 0.0001, 0.5, float(dflt["r_lo"]), 0.0005, format="%.4f", key=k("rlo"))
    o["r_hi"] = cc[1].number_input("5-year risk that maps to L = 1", 0.001, 1.0, float(dflt["r_hi"]), 0.01, format="%.3f", key=k("rhi"))
    if o["r_lo"] >= o["r_hi"]:
        st.error("The lower anchor must be smaller than the upper anchor."); st.stop()
    try:
        mk = B.BR.reference_markers(o["r_lo"], o["r_hi"])
        cc[2].caption("Published 5-year cut-points on this scale: " + "; ".join(f"{k_.split(',')[0].split(' ')[0]} {v:.2f}" for k_, v in mk.items()))
    except ValueError:
        pass
if disease == "imaging":
    recs = payload.get("records")
    cols_ = [c_ for c_ in (pd.DataFrame(recs).select_dtypes("number").columns if recs else []) if c_ not in ("label",)]
    if not cols_:
        st.info("Load a file (or the synthetic demo) with numeric feature columns, then map them here."); st.stop()
    st.markdown("**Map one numeric column to each term and give its anchors.** Nothing is assumed: the anchors are your decision, ideally fixed on development rows before you look at test rows.")
    mp = {}
    names = {"L": "L: likelihood (e.g. a texture or shape-alignment feature)", "E": "E: exposure (e.g. a signal-intensity feature)",
             "V": "V: vulnerability (e.g. a diffusion or perfusion feature)", "rho": "ρ: resilience (e.g. a boundary-integrity feature)"}
    for i, t in enumerate(["L", "E", "V", "rho"]):
        cc = st.columns([3, 1, 1, 1])
        col = cc[0].selectbox(names[t], cols_, index=min(i, len(cols_) - 1), key=k(f"mc_{t}"))
        x = pd.to_numeric(pd.DataFrame(recs)[col], errors="coerce")
        lo = cc[1].number_input("value → 0", value=float(x.quantile(0.05)) if x.notna().any() else 0.0, key=k(f"ml_{t}"), format="%.4f")
        hi = cc[2].number_input("value → 1", value=float(x.quantile(0.95)) if x.notna().any() else 1.0, key=k(f"mh_{t}"), format="%.4f")
        inv = cc[3].checkbox("invert", key=k(f"mi_{t}"), help="Tick when a LOWER raw value should mean a HIGHER term (for example restricted diffusion raising V).")
        mp[t] = dict(column=col, lo=lo, hi=hi, invert=inv)
    style.note("The suggested anchors are the 5th and 95th percentile of the file you loaded. That is a convenience, not a calibration: choosing anchors on the data you later validate on makes every result optimistic.")
    o["mapping"] = mp
if disease == "hcc" and o["l_tool"] == "aMAP" and not o["allow_overlap"]:
    st.error("Not scored: aMAP and ALBI share albumin and bilirubin. Choose aMAP-ref, or tick the overlap box in More settings."); st.stop()
payload["options"] = o


@st.cache_data(show_spinner="Scoring cohort…", max_entries=6)
def run_cached(dz, pj):
    p = json.loads(pj)
    return call(f"/v1/sandbox/{dz}/score", p, lambda: B.run(dz, p.get("records"), p.get("dataset"), p.get("options")))


try:
    out = run_cached(disease, json.dumps(payload, default=str))
except ValueError as e:
    st.error(str(e)); st.stop()

# ------------------------------------------------------------------ results
st.markdown("### 3. Results")
tiers = pd.DataFrame(out["tiers"])
share = ", ".join(f"{r.pct_now:g}% {r.tier.split(' ', 1)[1]}" for r in tiers.itertuples() if r.patients_now)
st.success(f"{out['n']:,} patients scored ({out['label']}). At ρ now: {share}." + (f" {' / '.join(out['score_status'])}." if out.get("score_status") else ""))
m = out["mean"]
c = st.columns(5)
c[0].metric("Mean L", f"{m['L']:.3f}"); c[1].metric("Mean V", f"{m['V']:.3f}")
c[2].metric("Mean R now", f"{m['R_raw']:.3f}"); c[3].metric("Mean R after", f"{m['R_after']:.3f}"); c[4].metric("Mean EAL", f"{m['EAL']:.3f}")

st.markdown("#### Tier distribution")
g1, g2 = st.columns([5, 4])
g1.dataframe(tiers.rename(columns={"tier": "Tier", "patients_now": "Patients (ρ now)", "pct_now": "% (ρ now)", "patients_after": "Patients (ρ after)", "pct_after": "% (ρ after)"}), hide_index=True)
fig = go.Figure()
fig.add_bar(x=tiers["tier"], y=tiers["patients_now"], name="ρ now", marker_color=style.TIER_ACCENTS, text=tiers["patients_now"], textposition="outside")
fig.add_bar(x=tiers["tier"], y=tiers["patients_after"], name="ρ after", marker_color=style.TIER_ACCENTS, opacity=0.4, text=tiers["patients_after"], textposition="outside")
fig.update_yaxes(range=[0, max(1, int(tiers[["patients_now", "patients_after"]].max().max() * 1.18))])
fig.update_layout(height=300, barmode="group", margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h"), yaxis_title="patients", font=dict(color=style.INK))
g2.plotly_chart(fig, width="stretch")
style.note("Bars are labelled with the number of patients; colour is a visual aid only. Lighter bars show the improved ρ.")

oc = out["outcomes"]
if oc:
    st.markdown("#### Outcomes (descriptive)")
    c = st.columns(5)
    c[0].metric("Patients", f"{oc['n']:,}"); c[1].metric("Events (cause 1)", oc["events"]); c[2].metric("Competing (cause 2)", oc["competing"])
    c[3].metric("Person-years", f"{oc['person_years']:,.0f}"); c[4].metric("Crude per 100 PY", f"{oc['crude_per_100py']:.2f}")
    if "c_index" in oc:
        ci = oc.get("c_index_ci95")
        st.metric("Harrell C of R", f"{oc['c_index']:.3f}", f"95% interval {ci[0]:.3f} to {ci[1]:.3f}" if ci else None, delta_color="off")
        st.caption(oc["c_index_note"] + " 0.5 means no discrimination, 1.0 perfect.")
        if oc["events"] < 30:
            st.warning(f"Only {oc['events']} events: C-index and incidence estimates are unstable.")
    bt = pd.DataFrame(oc["by_tier"])
    cif = [x for x in bt.columns if x.startswith("cif_")]
    bt["person_years"] = bt["person_years"].round(1)
    bt = bt.rename(columns={"tier": "Tier", "n": "Patients", "events": "Events", "competing": "Competing", "person_years": "Person-years", "crude_per_100py": "Crude per 100 PY",
                            **{x: f"Cumulative incidence {x[4:-1]}-year" for x in cif}})
    st.dataframe(bt.round(4), hide_index=True)
    st.caption("Cumulative incidence is Aalen-Johansen for cause 1 with cause 2 as a competing event. R is a relative score, not a probability.")
    if oc.get("by_stratum"):
        st.markdown("**Discrimination by subgroup.** A pooled C-index can hide a subgroup where the score fails.")
        st.dataframe(pd.DataFrame(oc["by_stratum"]).round(3), hide_index=True)
elif disease != "imaging":
    st.info("No usable time_years and cause columns: showing scores and tiers only.")

im = out.get("imaging")
if im:
    st.markdown("#### What was scored, and what to be careful about")
    c = st.columns(4)
    c[0].metric("Rows scored", f"{im['rows_scored']:,}"); c[1].metric("Excluded (missing value)", im["rows_excluded_missing"])
    c[2].metric("Clipped to anchors", sum(im["values_clipped_to_anchors"].values())); c[3].metric("Correlated term pairs", len(im["correlated_term_pairs"]))
    for w in im["warnings"]:
        st.warning(w)
    if im["correlated_term_pairs"]:
        st.dataframe(pd.DataFrame(im["correlated_term_pairs"]).round(2), hide_index=True)
    vd = im.get("validation")
    if vd:
        st.markdown("#### Against the labels (pathology)")
        rows = [{"Rows": name, "n": v["n"], "Malignant": v["malignant"], **{k_: (round(a, 3) if a is not None else None) for k_, a in v["auc"].items()}} for name, v in vd["by_split"].items()]
        st.dataframe(pd.DataFrame(rows), hide_index=True)
        st.caption("AUC of the product R against each term alone and a plain average. If R does not beat its own best single term or the simple mean, the multiplicative form is adding nothing here.")
        tb = pd.DataFrame(vd["by_tier"])
        tb["95% interval"] = tb["wilson95"].apply(lambda w: f"{100 * w[0]:.0f}% to {100 * w[1]:.0f}%")
        st.dataframe(tb.drop(columns=["wilson95"]).rename(columns={"tier": "Tier", "n": "n", "malignant": "Malignant", "proportion_malignant": "Proportion malignant"}).round({"Proportion malignant": 3}), hide_index=True)
        for w in vd.get("direction_warnings", []):
            st.error(w["message"])
        st.warning(vd["note"] + " " + vd["reading"])
    else:
        st.info("Add a label column (1 malignant, 0 benign) and, ideally, a split column (dev / test) to see how R ranks against pathology.")

ex = out.get("extras") or {}
if ex.get("tumour_at_diagnosis_by_tier"):
    st.markdown("#### Tumour at diagnosis, by baseline tier (cases only)")
    tt = pd.DataFrame(ex["tumour_at_diagnosis_by_tier"]).rename(columns={"baseline_tier": "Baseline tier", "cases": "HCC cases", "median_diameter_cm": "Median size (cm)", "median_nodules": "Median nodules", "pct_over_3cm": "% over 3 cm", "n_size_recorded": "n size", "pct_multinodular": "% 2+ nodules", "n_nodules_recorded": "n nodules", "n_vp_recorded": "n Vp",
         "pct_portal_vein_invasion": "% portal-vein invasion", "median_afp_ng_ml": "Median AFP (ng/mL)", "median_dcp_ng_ml": "Median DCP (ng/mL)"})
    st.dataframe(tt.round(1), hide_index=True)
    st.caption(ex["tumour_note"])

if ex.get("by_etiology"):
    st.markdown("#### By aetiology")
    st.dataframe(pd.DataFrame(ex["by_etiology"]).rename(columns={"etiology": "Aetiology", "n": "Patients", "mean_L": "Mean L", "mean_V": "Mean V", "R_now": "R (ρ now)", "tier_now": "Tier (ρ now)",
                 "R_after": "R (ρ after)", "tier_after": "Tier (ρ after)", "events": "Events", "person_years": "Person-years", "crude_per_100py": "Crude per 100 PY"}).round({"mean_L": 3, "mean_V": 3, "R_now": 3, "R_after": 3, "person_years": 1, "crude_per_100py": 2, "Mean L": 3, "Mean V": 3, "R (ρ now)": 3, "R (ρ after)": 3, "Person-years": 1, "Crude per 100 PY": 2}), hide_index=True)
    st.caption(ex["by_etiology_note"])
if ex.get("observed_vs_published"):
    st.markdown("#### Observed incidence against the published aMAP ranges")
    ov = pd.DataFrame(ex["observed_vs_published"])
    ov["inside_published_range"] = ov["inside_published_range"].map({True: "Yes", False: "No"})
    st.dataframe(ov.rename(columns={"risk_group": "aMAP group", "n": "Patients", "events": "Events", "person_years": "Person-years", "observed_per_100py": "Observed per 100 PY",
                                    "published_low_per_100py": "Published low", "published_high_per_100py": "Published high", "inside_published_range": "Observed within published range"})
                 .round({"Person-years": 1, "Observed per 100 PY": 2, "Published low": 2, "Published high": 2}), hide_index=True)
    st.caption("Published ranges: Fan 2020, J Hepatol, per 100 person-years. Crude rates, not adjusted for competing risks.")

d = st.columns(3)
d[0].download_button("Tier table (CSV)", tiers.to_csv(index=False), f"{disease}_tiers.csv", key=k("dl1"))
if out.get("patients") is not None:
    d[1].download_button("Scored cohort (CSV)", pd.DataFrame(out["patients"]).to_csv(index=False), f"{disease}_scored.csv", key=k("dl2"))
else:
    d[1].caption(out.get("patients_note") or "")
rec = {k_: v for k_, v in out.items() if k_ in ("disease", "n", "options", "audit", "tiers", "mean", "disclaimer")}
d[2].download_button("Reproducibility record (JSON)", json.dumps(rec, indent=1), f"{disease}_record.json", key=k("dl3"), help="Settings, versions and data fingerprint, so the run can be repeated and audited.")

# ------------------------------------------------------------------ method and audit
st.markdown("### 4. Method and audit")
vf = out.get("verification")
if vf:
    with st.expander(f"Check against the Excel workbook's Python run: {vf.get('overall', 'not applicable')}"):
        if vf.get("checks"):
            st.dataframe(pd.DataFrame(vf["checks"]), hide_index=True); st.caption(vf["source"])
        else:
            st.info(vf["note"])
with st.expander("Method, limits and versions"):
    au = out["audit"]
    st.markdown(f"""
- **Scoring** uses the platform engine unchanged (engine v{au['engine']}, registry {au['registry']}). No equation is added by the sandbox.
- **Cumulative incidence, Harrell C and crude rates** are descriptive statistics on top of the scores. They do not recalibrate or retrain anything.
- **Anchors are assigned, not estimated.** Nothing you upload changes a constant.
- **Lung** anchors and the ρ_bio ladder are provisional placeholders. **Breast** has no instruments or anchors: you supply L, E, V and ρ from your own pre-registered mapping.
- **Not a medical device.** Results are for research discussion, not patient-care decisions.
""")
    if au.get("bundled_dataset"):
        b = au["bundled_dataset"]
        st.markdown(f"**Bundled data:** {b['label']}, file `{b['file']}`, {b['rows']:,} rows, SHA-256 `{b['sha256'][:16]}…` (the full hash is in the record).")
    st.json({k_: v for k_, v in out.items() if k_ in ("options", "dataset")})
