"""RMTI web app. Local:  streamlit run streamlit_app.py   |   Streamlit Cloud: main file = streamlit_app.py
Research prototype: not validated against outcomes; not a medical device."""
import json, os, tempfile
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

import rmti
from rmti import (UncertainParam as U, Project, boundary_margins, datasets, optimize_portfolio, budget_frontier,
                  project_from_inputs, score, simulate_rmti, woe_sensitivity)
from rmti.core import C_INFRA, TIER_LABELS
from rmti.stochastic import WOE_CONCENTRATION

st.set_page_config(page_title="RMTI | Risk Mechanism Theory Index", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
  .block-container{max-width:1320px;padding-top:2rem;padding-bottom:4rem}
  h1,h2,h3{font-weight:600;letter-spacing:-.01em}
  div[data-testid="stMetric"]{background:#fff;border:1px solid #d9dee5;border-radius:4px;padding:.7rem .9rem}
  div[data-testid="stMetricValue"]{font-variant-numeric:tabular-nums}
  div[data-testid="stTabs"] button[role="tab"]{font-weight:500}
  div[data-testid="stMarkdownContainer"] *{overflow-wrap:anywhere}
  div[data-testid="stDataFrame"],div[data-testid="stTable"]{max-width:100%;overflow-x:auto}
  section[data-testid="stSidebar"]{border-right:1px solid #d9dee5}
</style>""", unsafe_allow_html=True)
st.title("Risk Mechanism Theory Index (RMTI)")
st.caption("R = L · E · V · (1 − ρ).  Research prototype — scores are decision-support indices, not probabilities or "
           "monetary losses; the oncology module is not validated against outcomes and is not a medical device.")

# ---------------- sidebar inputs shared by Score + Uncertainty ----------------
cohorts = {"Custom": dict(L=0.8, E_sel=0.7, V=0.7, rho_now=0.2, rho_after=0.5, C=4)}
cohorts.update({f"Urban · {k}": v for k, v in datasets.load_urban_cohort().items()})
cohorts.update({f"HCC · {k}": v for k, v in datasets.load_hcc_published().items()})
with st.sidebar:
    st.header("Inputs")
    pick = st.selectbox("Preset (paper inputs)", list(cohorts))
    p = cohorts[pick]
    key = pick  # re-key widgets when the preset changes
    L = st.slider("L  likelihood", 0.0, 1.0, float(p["L"]), 0.01, key=f"L{key}")
    E = st.slider("E_sel  exposure", 0.0, 1.0, float(p["E_sel"]), 0.01, key=f"E{key}")
    V = st.slider("V  vulnerability", 0.0, 1.0, float(p["V"]), 0.01, key=f"V{key}")
    rho = st.slider("ρ now", 0.0, 1.0, float(p["rho_now"]), 0.01, key=f"r{key}")
    rho2 = st.slider("ρ after", 0.0, 1.0, float(p.get("rho_after", min(1.0, p["rho_now"] + 0.3))), 0.01, key=f"r2{key}")
    C = st.select_slider("C  consequence level", [1, 2, 3, 4, 5], int(p.get("C", 4)), key=f"C{key}",
                         help="Table 2: " + ", ".join(f"{k}={v}" for k, v in C_INFRA.items()))

tabs = st.tabs(["Score", "Uncertainty", "Portfolio", "Geospatial (urban)", "Oncology (HCC)", "About"])

# ---------------- Score ----------------
with tabs[0]:
    a, b = score(L, E, V, rho, C), score(L, E, V, rho2, C)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("R now", a["R"]); c1.caption(a["tier"])
    c2.metric("R after", b["R"]); c2.caption(b["tier"])
    c3.metric("Risk reduction", f"{(1 - (1 - rho2) / (1 - rho)) * 100:.1f}%" if rho < 1 else "–")
    c4.metric("EAL now → after", f"{a['EAL']} → {b['EAL']}")
    m = boundary_margins(L, E, V, rho)
    st.subheader("How close is the tier boundary?")
    lo, hi = m["lower_threshold"], m["upper_threshold"]
    rows = []
    if lo is not None:
        rows.append(("Down to " + str(lo), f"{m['rel_change_LEV_to_lower']:+.1%}", None if m["delta_rho_to_lower"] is None else f"{m['delta_rho_to_lower']:+.3f}"))
    if hi is not None:
        rows.append(("Up to " + str(hi), f"{m['rel_change_LEV_to_upper']:+.1%}", None if m["delta_rho_to_upper"] is None else f"{m['delta_rho_to_upper']:+.3f}"))
    st.table(pd.DataFrame(rows, columns=["Boundary", "Relative error in L, E or V that crosses it", "Absolute change in ρ that crosses it"]))
    el = rmti.elasticity
    st.caption(f"Elasticities: L, E, V = +1; ρ = {el.elasticity_rho(rho):+.2f} (a ±10% error in ρ moves R by only about "
               f"{abs(el.elasticity_rho(rho)) * 10:.1f}%).")

# ---------------- Uncertainty ----------------
with tabs[1]:
    st.warning("Tier probabilities depend on an **assumed** mapping from evidence grade to spread "
               "(Table 9.3 gives no variances). Treat them as a sensitivity analysis, not a measurement.")
    grades = list(WOE_CONCENTRATION)
    cols = st.columns(5)
    g = {n: cols[i].selectbox(n, grades, index=2, key=f"g{n}") for i, n in enumerate(["L", "E", "V", "ρ now", "ρ after"])}
    n_sims = st.select_slider("Simulations", [5_000, 20_000, 50_000, 100_000], 20_000)
    corr = st.checkbox("Correlate L and V")
    rcorr = st.slider("Correlation L–V", -0.9, 0.9, 0.5, 0.1) if corr else 0
    C4 = np.eye(4); C4[0, 2] = C4[2, 0] = rcorr
    r = simulate_rmti(U(L, g["L"]), U(E, g["E"]), U(V, g["V"]), U(rho, g["ρ now"]), U(rho2, g["ρ after"]),
                      n_sims=n_sims, correlation=C4 if corr else None)
    s = r.summary()
    c1, c2, c3 = st.columns(3)
    c1.metric("P(point-estimate tier)", f"{r.p_point_tier:.0%}"); c1.caption(r.point_tier)
    c2.metric("R 95% interval", f"{s['R_ci_95'][0]} – {s['R_ci_95'][1]}")
    c3.metric("P(package improves tier)", f"{s['p_tier_improves']:.0%}")
    st.bar_chart(pd.DataFrame({"now": r.tier_probabilities, "after": r.tier_probabilities_after}))
    st.caption("Sensitivity to the assumption (same grade on all four inputs):")
    st.dataframe(pd.DataFrame(woe_sensitivity(L, E, V, rho, n_sims=10_000), index=["P(point tier)"]).round(2))

# ---------------- Portfolio ----------------
with tabs[2]:
    st.write("Pick the best set of projects under a budget. ΔR is summed across assets — a normative "
             "assumption — and every ρ after is a scenario assumption.")
    default = pd.DataFrame([dict(name=k, group=k, cost=50.0, N=v["N"], L=v["L"], E_sel=v["E_sel"], V=v["V"],
                                 rho_now=v["rho_now"], rho_after=v["rho_after"], C=v["C"])
                            for k, v in datasets.load_urban_cohort().items() if "rho_after" in v])
    df = st.data_editor(default, num_rows="dynamic", width="stretch")
    c1, c2 = st.columns(2)
    budget = c1.number_input("Budget (same units as cost)", 0.0, 1e9, 100.0)
    obj = c2.selectbox("Objective", ["delta_R", "delta_EAL", "delta_equity"],
                       help="delta_equity = reduction in EAL per million residents (Eq. 7)")
    if st.button("Optimise"):
        try:
            projs = [project_from_inputs(r.name, r.cost, r.N, r.L, r.E_sel, r.V, r.rho_now, r.rho_after, int(r.C), r.group)
                     for r in df.itertuples()]
            res = optimize_portfolio(projs, budget, obj)
            st.success(f"Selected: {', '.join(res.selected) or 'none'} — cost {res.total_cost:g} of {budget:g}; "
                       f"objective {res.objective_value:.3f} (greedy {res.greedy_value:.3f})")
            fr = budget_frontier(projs, np.linspace(0, df["cost"].sum(), 8), obj)
            st.line_chart(pd.DataFrame({"budget": [f["budget"] for f in fr], "value": [f["value"] for f in fr]}).set_index("budget"))
        except Exception as e:
            st.error(str(e))

# ---------------- Geospatial ----------------
def show_map(path, height=560):
    html = open(path, encoding="utf-8").read()
    if hasattr(st, "iframe"):
        st.iframe(html, height=height)
    else:  # older Streamlit
        components.html(html, height=height, scrolling=False)

with tabs[3]:
    st.write("Derive **E_sel** from a hazard footprint and an asset layer, and N from a population raster. "
             "Imagery-derived footprints are screening proxies; L, V and ρ remain analyst inputs.")
    mode = st.radio("Data", ["Synthetic demo (optical pre/post)", "Synthetic demo (SAR pre/post)", "Upload my GIS layers"], horizontal=True)
    cc = st.columns(4)
    Lg = cc[0].slider("L", 0.0, 1.0, 0.9, 0.01, key="Lg"); Vg = cc[1].slider("V", 0.0, 1.0, 0.8, 0.01, key="Vg")
    rg = cc[2].slider("ρ now", 0.0, 1.0, 0.2, 0.01, key="rg"); rg2 = cc[3].slider("ρ after", 0.0, 1.0, 0.55, 0.01, key="rg2")
    S = datasets.sample_path
    if mode.startswith("Synthetic"):
        if mode.startswith("Synthetic demo (SAR"):
            st.caption("Radar sees through cloud. Footprint = Lee-filtered VV, dark now (< −15 dB) and ≥3 dB darker than before. "
                       "Flooded buildings/vegetation are under-detected by this method.")
        if st.button("Run demo"):
            from rmti.pipeline import flood_run
            from rmti.stac import bandstack_from_tif
            out = tempfile.mkdtemp()
            common = dict(L=Lg, V=Vg, rho=rg, C=5, rho_after=rg2, zones=S("urban_zones.geojson"))
            if "SAR" in mode:
                sensors = dict(sar_pre=bandstack_from_tif(S("urban_sar_pre.tif"), ["vv", "vh"]),
                               sar_post=bandstack_from_tif(S("urban_sar_post.tif"), ["vv", "vh"]))
            else:
                nm = ["green", "red", "nir", "swir1"]
                sensors = dict(post=bandstack_from_tif(S("urban_bands_post.tif"), nm), pre=bandstack_from_tif(S("urban_bands_pre.tif"), nm))
            res = flood_run(S("urban_aoi.geojson"), S("urban_assets_lines.geojson"), S("urban_population.tif"), out, **sensors, **common)
            st.session_state["flood"] = res
    else:
        up = st.file_uploader("Assets (GeoJSON)", type=["geojson", "json"])
        uh = st.file_uploader("Hazard footprint (GeoJSON)", type=["geojson", "json"])
        ur = st.file_uploader("Population count raster (GeoTIFF, persons per cell)", type=["tif", "tiff"])
        uj = st.file_uploader("Jurisdiction boundary (GeoJSON)", type=["geojson", "json"])
        if st.button("Run") and all([up, uh, ur, uj]):
            import geopandas as gpd
            from rmti.pipeline import flood_run
            d = tempfile.mkdtemp()
            paths = {}
            for k, f in dict(a=up, h=uh, j=uj).items():
                paths[k] = os.path.join(d, k + ".geojson"); open(paths[k], "wb").write(f.getvalue())
            rp = os.path.join(d, "pop.tif"); open(rp, "wb").write(ur.getvalue())
            try:
                st.session_state["flood"] = flood_run(paths["j"], paths["a"], rp, d, hazard=paths["h"], L=Lg, V=Vg, rho=rg,
                                                      rho_after=rg2, weight_col=None)
            except Exception as e:
                st.error(str(e))
    res = st.session_state.get("flood")
    if res:
        sm = res.summary
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("E_sel (assets in hazard)", sm["exposure"]["E_sel"]); m2.metric("E_pop (people in hazard)", sm["exposure"]["E_pop"])
        m3.metric("R now", sm["R"]); m3.caption(sm["tier"]); m4.metric("R after", sm.get("R_after")); m4.caption(str(sm.get("tier_after")))
        st.caption("Hazard source: " + sm["hazard_source"])
        show_map(res.outputs["map"])
        with open(res.outputs["hazard"], "rb") as f:
            st.download_button("Download hazard footprint (GeoJSON)", f, "hazard.geojson")
        with open(res.outputs["map"], "rb") as f:
            st.download_button("Download map (HTML)", f, "rmti_map.html")

# ---------------- Oncology ----------------
with tabs[4]:
    st.error("Research prototype. Not validated against incident-HCC outcomes. Not for individual patient care decisions.")
    sub = st.radio("Mode", ["Patient registry triage", "District access & surveillance map"], horizontal=True)
    if sub.startswith("Patient"):
        from rmti.domains import hcc
        up = st.file_uploader("CSV: L, E, surveillance, bclc_if_missed, and albi_grade or albumin+bilirubin", type="csv")
        c1, c2 = st.columns(2)
        au = c1.selectbox("Albumin unit", ["g/L", "g/dL"]); bu = c2.selectbox("Bilirubin unit", ["umol/L", "mg/dL"])
        raw = pd.read_csv(up) if up else pd.read_csv(datasets.sample_path("hcc_patients_synthetic.csv"))
        st.caption("Using your file." if up else "Using SYNTHETIC sample patients.")
        try:
            out = hcc.score_table(raw, au, bu)
            st.bar_chart(out["tier"].value_counts().reindex(TIER_LABELS).fillna(0))
            st.dataframe(out.head(200), width="stretch")
            st.download_button("Download scored CSV", out.to_csv(index=False), "hcc_scored.csv")
        except ValueError as e:
            st.error(str(e))
    else:
        import geopandas as gpd
        from rmti.domains import hcc_geo
        from rmti.webmap import risk_map
        zones = gpd.read_file(datasets.sample_path("hcc_districts.geojson"))
        cen = gpd.read_file(datasets.sample_path("hcc_centers.geojson"))
        rad = st.slider("Surveillance reach radius (km, straight-line)", 2, 60, 15)
        after = st.checkbox("Score an optimised-programme scenario (ρ = 0.65)")
        z = hcc_geo.access_exposure(zones, cen, rad, datasets.sample_path("hcc_at_risk.tif"))
        z["rho"] = hcc_geo.rho_from_uptake(z["uptake"])
        z = hcc_geo.score_zones(z, rho_after=0.65 if after else None)
        tmp = os.path.join(tempfile.mkdtemp(), "m.html")
        risk_map(zones=z, centers=cen, popup_cols=("name", "E", "R", "tier"), satellite=False).save(tmp)
        show_map(tmp, 520)
        st.dataframe(z.drop(columns="geometry").round(3))
        st.caption("SYNTHETIC districts. E = share of at-risk persons within the radius of a centre. "
                   "ρ interpolated from uptake on the published ladder (an assumption of this library).")

# ---------------- About ----------------
with tabs[5]:
    st.markdown(f"""
**rmti-py {rmti.__version__}** · Apache-2.0 · Marolla, *From Narrative to Algorithm*, IJMADA 6(1):354–388 (2026).

* Inputs are analyst-scored; ρ after is a scenario assumption; R is a relative index.
* Tier probabilities rest on an assumed evidence-grade → spread mapping.
* Imagery proxies (MNDWI, NDMI) are screening tools, not hazard models.
* Sample data in the demos is **synthetic**.
* Programmatic access (API keys, FHIR R4 output, CSV/Parquet cohorts): see the developer portal served by the API at `/portal/`.
""")
